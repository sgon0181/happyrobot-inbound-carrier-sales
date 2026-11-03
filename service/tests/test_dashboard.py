"""The operations snapshot: derived outcomes, each call's reservation, and KPIs on real calls."""

import asyncio
from datetime import timedelta
from typing import Any

from service.adapters.twin import Row
from service.dashboard import build_snapshot, handoffs, outcome
from service.tests.fake_tms import make_load
from service.tests.rig import AGENT, RUN, START, Rig, rig

LANE = {"equipment": "dry van", "origin_state": "tx", "dest_state": "GA"}


def reserved() -> Rig:
    """A real call that passed its code, heard an offer 40 seconds in and reserved LD09001."""
    r = rig()
    r.board.records = [make_load()]
    r.verified()
    r.clock.now = START + timedelta(seconds=40)
    assert r.post("/loads/search", **LANE)["status"] == "found"
    assert r.post("/negotiate", load_id="LD09001", rate=1850)["status"] == "agreed"
    return r


def test_only_the_ops_key_reads_the_snapshot() -> None:
    r = rig()
    assert r.get("/ops/snapshot", key=AGENT)["http"] == 401
    assert r.get("/ops/snapshot", key="")["http"] == 401
    assert r.get("/ops/snapshot")["http"] == 200


def test_a_reserved_call_shows_its_booking_version_and_counts_as_a_handoff() -> None:
    r = reserved()
    snapshot = r.get("/ops/snapshot")
    [call], [booking] = snapshot["calls"], snapshot["bookings"]
    assert (call["id"], call["outcome"], call["rounds"]) == (RUN, "agreed_pending_rep", 0)
    assert call["booking"] == {"load_id": "LD09001", "state": "RESERVED", "submitted": False}
    assert "otp" not in call  # the code hash never leaves Twin
    assert (booking["load_id"], booking["version"], booking["state"]) == ("LD09001", 1, "RESERVED")
    assert (booking["call_id"], booking["rate"], booking["mc"]) == (RUN, 1850, "138328")
    assert "void_claims" not in booking
    kpis = snapshot["kpis"]
    assert (kpis["calls"], kpis["code_passed"], kpis["handoffs"], kpis["northstar"]) == (1, 1, 1, 1)
    assert kpis["median_seconds_to_first_offer"] == 40
    assert kpis["outcomes"] == {"agreed_pending_rep": 1}
    assert (kpis["rep_confirmed"], kpis["tms_acknowledged"], kpis["closed_with_summary"]) == (
        0,
        0,
        0,
    )


def test_outcomes_follow_the_first_rule_that_applies() -> None:
    now = START + timedelta(hours=1)
    quiet = (START + timedelta(minutes=29)).isoformat()
    booking = {"load_id": "LD1", "state": "RELEASED", "submitted": False}
    assert outcome({"outcome": "no_match"}, booking, now) == "agreed_pending_rep"
    assert outcome({"outcome": "no_match", "closed_at": quiet}, None, now) == "no_match"
    assert outcome({"outcome": None, "closed_at": quiet}, None, now) == "ended_without_agreement"
    assert outcome({"ended_at": quiet}, None, now) == "ended_without_close"
    assert outcome({"last_activity": START.isoformat()}, None, now) == "end_not_recorded"
    assert outcome({"last_activity": quiet}, None, now - timedelta(minutes=2)) == "in_progress"
    assert outcome({}, None, now) == "in_progress"


def events(*steps: tuple[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"seq": n, "action": action, **detail} for n, (action, detail) in enumerate(steps, 1)]


def test_each_call_keeps_its_own_reservation_on_a_reused_load() -> None:
    history = events(
        ("reserved", {"call_id": "old"}),
        ("decline", {"state": "RELEASED"}),
        ("claim_voided", {"call_id": "x"}),
        ("reserved", {"call_id": "new"}),
        ("confirm", {"state": "SUBMITTING"}),
        ("sent", {"state": "ACK_PENDING"}),
    )
    bookings = {
        "LD1": Row(6, {"state": "ACK_PENDING", "events": history}),
        "LD2": Row(1, {"state": "UNCLAIMED", "events": events(("claim_voided", {}))}),
        "LD3": Row(1, {"state": "RESERVED"}),  # written before events existed
    }
    assert handoffs(bookings) == {
        "old": {"load_id": "LD1", "state": "RELEASED", "submitted": False},
        "new": {"load_id": "LD1", "state": "ACK_PENDING", "submitted": True},
    }
    snapshot = build_snapshot({}, bookings, START)
    assert [booking["load_id"] for booking in snapshot["bookings"]] == ["LD1", "LD3"]


def call(cohort: str, **data: Any) -> Row:
    fields = {"cohort": cohort, "started_at": START.isoformat(), "verified_at": None}
    return Row(1, fields | {"closed_at": None, "search": None, "events": []} | data)


def test_kpis_count_real_calls_and_test_data_is_shown_apart() -> None:
    lane = {"equipment": "REEFER", "origin_state": "CA", "dest_state": "KY"}
    sent = events(("reserved", {"call_id": "a"}), ("confirm", {"state": "SUBMITTING"}))
    calls = {
        "a": call("real", verified_at=START.isoformat(), closed_at=START.isoformat()),
        "b": call("real", verified_at=START.isoformat(), outcome="no_match", search=lane),
        "c": call("real", outcome="no_match", search=lane),
        "d": call("real", outcome="no_match", search=None, events=None),
        "e": call("synthetic", verified_at=START.isoformat(), outcome="no_match", search=lane),
        "selftest-20261103-deploy": Row(1, {"cohort": "real", "verified_at": "x"}),
    }
    bookings = {"LD1": Row(3, {"state": "UNKNOWN", "events": sent})}
    snapshot = build_snapshot(calls, bookings, START)
    kpis = snapshot["kpis"]
    assert (kpis["calls"], kpis["code_passed"], kpis["handoffs"], kpis["northstar"]) == (
        4,
        2,
        1,
        0.5,
    )
    assert (kpis["rep_confirmed"], kpis["unknown"], kpis["tms_confirmed"]) == (1, 1, 0)
    assert (kpis["synthetic_calls"], kpis["closed_with_summary"]) == (2, 0)
    assert kpis["median_seconds_to_first_offer"] is None
    assert snapshot["turned_away"] == [
        {"equipment": "REEFER", "origin_state": "CA", "dest_state": "KY", "calls": 2},
        {"equipment": None, "origin_state": None, "dest_state": None, "calls": 1},
    ]
    selftest = next(c for c in snapshot["calls"] if c["id"] == "selftest-20261103-deploy")
    assert selftest["cohort"] == "synthetic"


def test_with_no_calls_the_ratios_are_empty_not_zero() -> None:
    kpis = build_snapshot({}, {}, START)["kpis"]
    assert (kpis["calls"], kpis["northstar"], kpis["median_seconds_to_first_offer"]) == (
        0,
        None,
        None,
    )


def test_the_snapshot_is_cached_for_five_seconds_unless_forgotten() -> None:
    r = reserved()
    r.get("/ops/snapshot")
    count = len(r.twin.statements)
    r.clock.now += timedelta(seconds=4)
    r.get("/ops/snapshot")
    assert len(r.twin.statements) == count
    r.clock.now += timedelta(seconds=1)
    r.get("/ops/snapshot")
    assert len(r.twin.statements) == count + 2  # one statement per table
    r.dashboard.forget()
    r.get("/ops/snapshot")
    assert len(r.twin.statements) == count + 4


def test_a_twin_failure_is_reported_as_unavailable() -> None:
    r = rig()
    r.twin.statuses.extend([500])
    assert r.get("/ops/snapshot") == {"status": "temporarily_unavailable", "http": 503}


def test_a_call_that_changes_mc_after_passing_its_code_still_counts_as_code_passed() -> None:
    r = rig()
    r.verified()  # a correction is still allowed before a claim or agreement
    assert r.post("/carriers/verify", mc="MC-1515")["status"] == "eligible"
    assert r.row()["verified_at"] is None
    snapshot = r.get("/ops/snapshot")
    assert snapshot["calls"][0]["code_passed"] is True
    kpis = snapshot["kpis"]
    assert (kpis["code_passed"], kpis["handoffs"], kpis["northstar"]) == (1, 0, 0)


def test_dashboards_asking_together_share_one_refresh() -> None:
    r = reserved()
    count = len(r.twin.statements)

    async def twelve() -> list[Any]:
        return list(await asyncio.gather(*(r.dashboard.snapshot() for _ in range(12))))

    snapshots = asyncio.run(twelve())
    assert len(r.twin.statements) == count + 2
    assert all(snapshot is snapshots[0] for snapshot in snapshots)


def test_a_refresh_read_before_a_rep_action_is_not_cached_after_it() -> None:
    r = reserved()
    read = r.dashboard.twin.get_all

    async def action_lands_between_tables(table: str) -> Any:
        rows = await read(table)
        if table == "calls":
            r.dashboard.forget()  # a decline finished while this refresh was reading
        return rows

    r.dashboard.twin.get_all = action_lands_between_tables  # type: ignore[method-assign]
    asyncio.run(r.dashboard.snapshot())
    r.dashboard.twin.get_all = read  # type: ignore[method-assign]
    count = len(r.twin.statements)
    r.get("/ops/snapshot")
    assert len(r.twin.statements) == count + 2  # read afresh, not the outdated refresh


def test_send_mode_is_explicit_in_the_authenticated_snapshot() -> None:
    for enabled in (False, True):
        r = rig(live_booking=enabled)
        assert r.get("/ops/snapshot")["live_booking"] is enabled
        assert r.get("/ops/snapshot", key=AGENT)["http"] == 401
        assert r.board.sends == []


def test_closing_notes_and_reported_ends_count_only_actual_evidence() -> None:
    rows = {
        "none": call("real", closed_at=START.isoformat()),
        "blank": call("real", closed_at=START.isoformat(), summary="  "),
        "notes": call(
            "real", closed_at=START.isoformat(), summary="No match.", ended_at=START.isoformat()
        ),
        "test": call(
            "synthetic", closed_at=START.isoformat(), summary="Fixture", ended_at=START.isoformat()
        ),
    }
    kpis = build_snapshot(rows, {}, START)["kpis"]
    assert (kpis["calls"], kpis["closed_with_summary"], kpis["ends_reported"]) == (3, 1, 1)
