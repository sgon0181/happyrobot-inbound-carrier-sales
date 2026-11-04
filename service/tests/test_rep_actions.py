"""A rep's confirm, decline and reconcile: the version they saw, one send, nothing discarded."""

import asyncio
import hashlib
import json
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

from service.adapters.tms.client import Sent
from service.adapters.tms.protocol import InvalidRequest
from service.bookings import Bookings
from service.rep_actions import _save, classify
from service.tests.fake_tms import make_load
from service.tests.rig import AGENT, OPS, PENDING_RECEIPT, START, Rig, rig, sent

FIXTURES = Path(__file__).parents[2] / "docs" / "tms" / "fixtures" / "booking-replies.json"
LANE = {"equipment": "dry van", "origin_state": "tx", "dest_state": "GA"}
REP = "rep@happyrobot.test"


def reserved(*, live: bool = True, **load: str) -> Rig:
    """A real call's reservation of LD09001 at 1850, MC 138328, at booking version 1."""
    r = rig(live_booking=live)
    r.board.records = [make_load(**load)]
    r.verified()
    assert r.post("/loads/search", **LANE)["status"] == "found"
    assert r.post("/negotiate", load_id="LD09001", rate=1850)["status"] == "agreed"
    return r


def act(r: Rig, action: str, version: int = 1, load_id: str = "LD09001", **body: Any) -> Any:
    response = r.client.post(
        f"/bookings/{load_id}/{action}",
        json={"version": version, "rep": REP} | body,
        headers={"Authorization": f"Bearer {OPS}"},
    )
    return response.json() | {"http": response.status_code}


def booking(r: Rig) -> dict[str, Any]:
    return r.twin.data("bookings", "LD09001")


def version(r: Rig) -> int:
    return r.twin.tables["bookings"]["LD09001"][0]


def test_confirm_sends_once_and_keeps_the_whole_receipt() -> None:
    r = reserved()
    assert act(r, "confirm") == {
        "status": "sent",
        "state": "ACK_PENDING",
        "reason": None,
        "reference": "FIXTURE01",
        "tms_status": "PENDING",
        "http": 200,
    }
    assert r.board.sends == [("LD09001", "138328", 1850)]
    row = booking(r)
    assert (row["state"], row["reference"], row["tms_status"], row["rep"]) == (
        "ACK_PENDING",
        "FIXTURE01",
        "PENDING",
        REP,
    )
    assert row["raw_reply"].encode("latin-1") == PENDING_RECEIPT
    digest = hashlib.sha256(PENDING_RECEIPT).hexdigest()
    size = len(PENDING_RECEIPT)
    assert row["send"] == {"step": "received", "error": None, "bytes": size, "sha256": digest}
    actions = [(event["action"], event.get("state")) for event in row["events"]]
    assert actions == [("reserved", "RESERVED"), ("confirm", "SUBMITTING"), ("sent", "ACK_PENDING")]
    snapshot = r.get("/ops/snapshot")  # forgotten, so the rep sees their own action
    assert (snapshot["kpis"]["rep_confirmed"], snapshot["kpis"]["tms_acknowledged"]) == (1, 1)
    assert snapshot["kpis"]["tms_confirmed"] == 0  # PENDING is never counted as confirmed


def test_a_second_click_or_a_second_rep_sends_nothing() -> None:
    r = reserved()
    assert act(r, "confirm")["state"] == "ACK_PENDING"
    assert act(r, "confirm") == {"status": "stale", "http": 200}
    assert act(r, "confirm", version(r)) == {
        "status": "not_allowed",
        "state": "ACK_PENDING",
        "http": 200,
    }
    assert len(r.board.sends) == 1


def test_two_confirms_at_once_send_once() -> None:
    r = reserved()

    async def both() -> list[Any]:
        return list(await asyncio.gather(*(r.desk.confirm("LD09001", 1, REP) for _ in range(2))))

    replies = asyncio.run(both())
    assert sorted(reply["status"] for reply in replies) == ["sent", "stale"]
    assert len(r.board.sends) == 1


def test_with_live_booking_off_confirm_reads_and_sends_nothing() -> None:
    r = reserved(live=False)
    before = (version(r), len(r.twin.statements))
    assert act(r, "confirm") == {"status": "live_booking_off", "http": 200}
    assert (version(r), len(r.twin.statements), r.board.sends) == (*before, [])


def test_a_rep_on_an_out_of_date_screen_changes_nothing() -> None:
    r = reserved()
    assert act(r, "confirm", version=2)["status"] == "stale"
    assert act(r, "decline", version=2)["status"] == "stale"
    assert act(r, "confirm", load_id="LD404")["status"] == "stale"
    assert (version(r), booking(r)["state"], r.board.sends) == (1, "RESERVED", [])


def test_a_tms_outage_before_sending_leaves_the_reservation_to_retry() -> None:
    r = reserved()
    r.board.down = True
    assert act(r, "confirm")["status"] == "tms_unavailable"
    assert (version(r), booking(r)["state"], r.board.sends) == (1, "RESERVED", [])


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"STATUS": "PENDING"}, "load_not_open"),
        ({"PICKUP_DT": "20261102110000"}, "load_not_open"),  # passed by START
        ({"DEST_STATE": "NY"}, "shipment_changed"),
        ({"ORIG_ZIP": "75202"}, "shipment_changed"),
        ({"EQTYPE": "REEFER"}, "shipment_changed"),
        ({"PICKUP_DT": "20271102110000"}, "shipment_changed"),
        ({"MAX_BUY": "1825"}, "ceiling_below_rate"),
        ({"MAX_BUY": ""}, "ceiling_below_rate"),
        (None, "load_gone"),
    ],
)
def test_a_recheck_that_fails_sends_nothing_and_frees_the_load(
    change: dict[str, str] | None, reason: str
) -> None:
    r = reserved()
    if change is None:
        r.board.records = []
    else:
        r.board.details["LD09001"] = make_load(**change)
    assert act(r, "confirm") == {"status": "failed", "reason": reason, "http": 200}
    row = booking(r)
    assert (row["state"], row["reason"], row["rep"], r.board.sends) == ("FAILED", reason, REP, [])
    assert row["events"][-1]["action"] == "recheck_failed"


def test_a_spent_load_is_never_sent() -> None:
    r = reserved()
    r.desk.blocked = frozenset({"LD09001"})
    assert act(r, "confirm")["reason"] == "load_not_open"
    assert r.board.sends == []


def test_a_write_lost_to_another_writer_is_stale_and_sends_nothing() -> None:
    r = reserved()
    r.twin.interfere = True
    assert act(r, "confirm")["status"] == "stale"
    r.board.details["LD09001"] = make_load(STATUS="PENDING")
    assert act(r, "confirm", version(r))["status"] == "stale"  # the FAILED write lost too
    assert act(r, "decline", version(r))["status"] == "stale"
    assert r.board.sends == []


def test_a_booking_request_we_cannot_build_was_never_sent() -> None:
    r = reserved()

    async def refuse() -> None:
        raise InvalidRequest("bad")

    r.board.sending = refuse
    assert act(r, "confirm")["state"] == "FAILED"
    assert booking(r)["send"]["step"] == "build"


def fixture_cases() -> list[tuple[str, str, str]]:
    states = {
        "ack_pending": "ACK_PENDING",
        "rejected": "FAILED",
        "already_booked_not_confirmation": "UNKNOWN",
    }
    cases = json.loads(FIXTURES.read_text())["cases"]
    return [(case["load_id"], case["raw"], states[case["expected_outcome"]]) for case in cases]


@pytest.mark.parametrize(("load_id", "raw", "state"), fixture_cases())
def test_every_recorded_reply_maps_to_the_state_it_proves(
    load_id: str, raw: str, state: str
) -> None:
    assert classify(sent(raw.encode("ascii")), load_id).state == state


TWO_RECORDS = PENDING_RECEIPT.replace(b"END\r\n", b"") + PENDING_RECEIPT


@pytest.mark.parametrize(
    ("outcome", "state", "reason"),
    [
        (sent(PENDING_RECEIPT), "ACK_PENDING", None),
        (sent(PENDING_RECEIPT.replace(b"PENDING ", b"BOOKED  ")), "CONFIRMED", None),
        (sent(b"ERR|CODE:NOT_FOUND|MSG:no\r\n"), "FAILED", "not_found"),
        (sent(b"ERR|CODE:SERVER_ERROR|MSG:no\r\n"), "UNKNOWN", "server_error"),
        (Sent("connect", "TimeoutError", b"", None), "FAILED", "not_sent"),
        (Sent("send", "OSError", b"", None), "UNKNOWN", "no_complete_reply"),
        (Sent("receive", "TimeoutError", b"LOAD", None), "UNKNOWN", "no_complete_reply"),
        (sent(PENDING_RECEIPT.replace(b"LD09001", b"LD09002")), "UNKNOWN", "unexpected_receipt"),
        (sent(PENDING_RECEIPT.replace(b"FIXTURE01", b"")), "UNKNOWN", "unexpected_receipt"),
        (sent(PENDING_RECEIPT.replace(b"PENDING ", b"HELD    ")), "UNKNOWN", "unexpected_receipt"),
        (
            sent(PENDING_RECEIPT.replace(b"|TIMESTAMP:20261103010203", b"")),
            "UNKNOWN",
            "unexpected_receipt",
        ),
        (
            sent(PENDING_RECEIPT.replace(b"20261103010203", b"20260231000000")),
            "UNKNOWN",
            "unexpected_receipt",
        ),
        (sent(TWO_RECORDS), "UNKNOWN", "unexpected_receipt"),
        (sent(b"END\r\n"), "UNKNOWN", "unexpected_receipt"),
    ],
)
def test_only_a_complete_matching_receipt_is_acknowledged(
    outcome: Sent, state: str, reason: str | None
) -> None:
    receipt = classify(outcome, "LD09001")
    assert (receipt.state, receipt.reason) == (state, reason)


def test_a_refused_send_keeps_its_whole_receipt_after_the_load_is_reserved_again() -> None:
    r = reserved()
    refusal = b"ERR|CODE:INVALID_RATE|MSG:AGREED_RATE must be a positive integer\r\n"
    r.board.receipt = sent(refusal)
    assert act(r, "confirm")["state"] == "FAILED"
    held = asyncio.run(
        Bookings(r.desk.twin).reserve(
            "LD09001", claim_id="c2", call_id="next", mc="1515", rate=1800, cohort="real", now=START
        )
    )
    assert held is not None and held["raw_reply"] is None  # the new reservation starts afresh
    [receipt] = [event for event in booking(r)["events"] if event["action"] == "sent"]
    assert receipt["raw_reply"].encode("latin-1") == refusal
    assert receipt["send"]["sha256"] == hashlib.sha256(refusal).hexdigest()


def test_a_receipt_save_retries_through_a_twin_outage() -> None:
    r = reserved()

    async def twin_fails_twice() -> None:
        r.twin.statuses.extend([500, 500])

    r.board.sending = twin_fails_twice
    assert act(r, "confirm")["status"] == "sent"
    row = booking(r)
    assert row["state"] == "ACK_PENDING"
    assert [event["action"] for event in row["events"]].count("sent") == 1


def test_a_receipt_twin_never_takes_is_shown_to_the_rep_and_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    r = reserved()

    async def twin_stays_down() -> None:
        r.twin.statuses.extend([500] * 5)

    r.board.sending = twin_stays_down
    reply = act(r, "confirm")
    assert (reply["status"], reply["reference"], reply["send"]["bytes"]) == (
        "receipt_not_saved",
        "FIXTURE01",
        len(PENDING_RECEIPT),
    )
    assert booking(r)["state"] == "SUBMITTING"
    assert reply["send"]["sha256"] in caplog.text
    assert "FIXTURE01" not in caplog.text and "raw_reply" not in reply


def test_a_receipt_that_landed_is_not_written_twice() -> None:
    edit = _save("s1", {"state": "ACK_PENDING"}, START)
    data, _ = edit({"events": []})
    assert data is not None
    assert edit(data) == (None, None)
    assert edit(None)[0] is not None


def test_a_closed_screen_does_not_stop_the_send_being_saved() -> None:
    r = reserved()
    release = asyncio.Event()

    async def held() -> None:
        await release.wait()

    r.board.sending = held

    async def scenario() -> None:
        rep = asyncio.ensure_future(r.desk.confirm("LD09001", 1, REP))
        while not r.board.sends:
            await asyncio.sleep(0)
        rep.cancel()
        release.set()
        await asyncio.gather(*r.desk._sending)

    asyncio.run(scenario())
    assert booking(r)["state"] == "ACK_PENDING"


def test_decline_releases_the_reservation_the_rep_saw() -> None:
    r = reserved()
    assert act(r, "decline") == {"status": "released", "http": 200}
    row = booking(r)
    assert (row["state"], row["rep"], row["events"][-1]["state"], r.board.sends) == (
        "RELEASED",
        REP,
        "RELEASED",
        [],
    )
    assert act(r, "decline", version(r))["status"] == "not_allowed"
    snapshot = r.get("/ops/snapshot")
    assert snapshot["calls"][0]["booking"]["state"] == "RELEASED"


def submitting(r: Rig) -> None:
    """A confirm whose process died after winning SUBMITTING."""

    async def died() -> None:
        raise asyncio.CancelledError

    r.board.sending = died
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(r.desk.confirm("LD09001", 1, REP))
    assert booking(r)["state"] == "SUBMITTING"


def test_an_interrupted_send_becomes_unknown_after_a_minute_and_is_never_resent() -> None:
    r = reserved()
    submitting(r)
    assert act(r, "reconcile", 2) == {"status": "too_early", "http": 200}
    r.clock.now = START + timedelta(seconds=61)
    assert act(r, "reconcile", 2) == {
        "status": "reconciled",
        "state": "UNKNOWN",
        "load_status": "OPEN",
        "http": 200,
    }
    row = booking(r)
    assert (row["state"], row["reason"], len(r.board.sends)) == (
        "UNKNOWN",
        "interrupted_send",
        1,
    )
    assert (row["events"][-1]["rep"], row["events"][-1]["load_status"]) == (REP, "OPEN")


def test_reconcile_records_what_the_tms_shows_without_changing_the_state() -> None:
    r = reserved()
    act(r, "confirm")
    r.board.details["LD09001"] = make_load(STATUS="PENDING")
    assert act(r, "reconcile", 3)["load_status"] == "PENDING"
    r.board.down = True
    assert act(r, "reconcile", 4)["load_status"] == "unavailable"
    r.board.down, r.board.records, r.board.details = False, [], {}
    assert act(r, "reconcile", 5) == {
        "status": "reconciled",
        "state": "ACK_PENDING",
        "load_status": "missing",
        "http": 200,
    }
    assert (booking(r)["state"], len(r.board.sends)) == ("ACK_PENDING", 1)
    r.twin.interfere = True
    assert act(r, "reconcile", 6)["status"] == "stale"


def test_reconcile_never_touches_a_reservation() -> None:
    r = reserved()
    assert act(r, "reconcile")["status"] == "not_allowed"
    assert act(r, "reconcile", 2)["status"] == "stale"


@pytest.mark.parametrize(
    ("load_id", "body"),
    [
        ("LD09001", {"version": 0}),
        ("LD09001", {"rep": " "}),
        ("LD09001", {"version": "1"}),
        ("LD09001", {"extra": True}),
        ("LD|1", {}),
    ],
)
def test_malformed_rep_actions_are_refused(load_id: str, body: dict[str, Any]) -> None:
    r = reserved()
    assert act(r, "confirm", load_id=load_id, **body)["http"] in (400, 404)
    assert r.board.sends == []


def test_only_the_ops_key_can_act() -> None:
    r = reserved()
    for key in ("", AGENT):
        response = r.client.post(
            "/bookings/LD09001/confirm",
            json={"version": 1, "rep": REP},
            headers={"Authorization": f"Bearer {key}"},
        )
        assert response.status_code == 401
    assert r.board.sends == []


@pytest.mark.parametrize("cohort", ["synthetic", "", None])
def test_only_a_record_stamped_real_can_reach_the_tms(cohort: str | None) -> None:
    r = reserved()
    booking(r)["cohort"] = cohort
    r.board.reading = lambda _: pytest.fail("record guard must precede TMS access")
    assert act(r, "confirm")["status"] == "record_read_only"
    assert booking(r)["state"] == "RESERVED"
    assert not r.board.sends


def test_raw_receipts_stay_in_twin_and_never_enter_the_ops_snapshot() -> None:
    r = reserved()
    assert act(r, "confirm")["state"] == "ACK_PENDING"
    assert "raw_reply" in booking(r) and "raw_reply" not in str(r.get("/ops/snapshot"))


@pytest.mark.parametrize("route", [None, "demo_inbox", "unrecognized"])
def test_enabling_writes_later_cannot_submit_an_old_demo_inbox_reservation(
    route: str | None,
) -> None:
    r = reserved()
    booking(r)["otp_route"] = route
    assert act(r, "confirm")["status"] == "record_read_only"
    assert booking(r)["state"] == "RESERVED" and not r.board.sends


def test_rep_cannot_send_an_interrupted_acceptance_even_after_terminal_recovery() -> None:
    r = reserved()
    call = r.row()
    b = booking(r)
    claim = {"id": b["claim_id"], "mc": b["mc"], "load_id": "LD09001", "rate": b["rate"]}
    call.update(accepting=claim, agreement=None)
    assert act(r, "confirm")["status"] == "agreement_incomplete"
    assert r.post("/calls/ended", ended_by="caller")["status"] == "ended"
    assert r.row()["agreement_needs_review"] and r.row()["accepting"] is None
    assert act(r, "confirm")["status"] == "agreement_incomplete"
    snapshot = r.get("/ops/snapshot")
    assert snapshot["bookings"][0]["agreement_needs_review"]
    assert snapshot["calls"][0]["booking"] is None
    assert not r.board.sends
    assert act(r, "decline")["status"] == "released"
