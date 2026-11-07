"""Challenge sends preserve identity boundaries, consent, rechecks and one-shot writes."""

import asyncio
from datetime import timedelta
from typing import Any

import pytest

from service.tests.fake_tms import make_load
from service.tests.rig import AGENT, START, Rig, rig, sent
from service.tests.test_rep_actions import LANE, REP, act, booking, version


def sandbox() -> Rig:
    r = rig(live_booking=False, sandbox_mc="138328", cohort="synthetic", trusted_contacts=False)
    r.board.records = [make_load()]
    r.verified()
    assert r.post("/loads/search", **LANE)["status"] == "found"
    assert r.post("/negotiate", load_id="LD09001", rate=1850)["status"] == "agreed"
    return r


def test_demo_call_can_submit_only_to_opted_in_challenge_mode_once() -> None:
    r = sandbox()
    snapshot = r.get("/ops/snapshot")
    assert snapshot["live_booking"] is False and snapshot["sandbox_booking_mc"] == "138328"
    assert booking(r)["otp_route"] == "demo_inbox"  # never masquerades as carrier identity
    assert act(r, "confirm")["state"] == "ACK_PENDING"
    assert booking(r)["send_mode"] == "challenge_sandbox"
    assert act(r, "confirm")["status"] == "stale"
    assert act(r, "confirm", version(r))["status"] == "not_allowed"
    assert r.board.sends == [("LD09001", "138328", 1850)]


def test_two_sandbox_rep_actions_still_win_one_send() -> None:
    r = sandbox()

    async def both() -> list[Any]:
        return list(await asyncio.gather(*(r.desk.confirm("LD09001", 1, REP) for _ in range(2))))

    replies = asyncio.run(both())
    assert sorted(reply["status"] for reply in replies) == ["sent", "stale"]
    assert len(r.board.sends) == 1


@pytest.mark.parametrize("table", ["calls", "bookings"])
@pytest.mark.parametrize(
    "change",
    [
        {"read_only": True},
        {"cohort": "real"},
        {"otp_route": "trusted_contact"},
        {"otp_route": None},
        {"mc": "132354"},
    ],
)
def test_sandbox_rejects_imported_or_mismatched_provenance(
    table: str, change: dict[str, Any]
) -> None:
    r = sandbox()
    key = booking(r)["call_id"] if table == "calls" else "LD09001"
    r.twin.data(table, key).update(change)
    assert act(r, "confirm")["status"] in {"record_read_only", "agreement_incomplete"}
    assert r.board.sends == []


@pytest.mark.parametrize(
    "change",
    [
        {"verified_at": None},
        {"eligible": False},
        {"agreement": None},
        {"agreement_needs_review": True},
        {"accepting": {"rate": 1850}},
    ],
)
def test_sandbox_still_requires_verified_and_completed_consent(change: dict[str, Any]) -> None:
    r = sandbox()
    r.twin.data("calls", booking(r)["call_id"]).update(change)
    assert act(r, "confirm")["status"] == "agreement_incomplete"
    assert not r.board.sends


@pytest.mark.parametrize(
    "change",
    [
        {"MAX_BUY": "1825"},
        {"STATUS": "PENDING"},
        {"DEST_STATE": "NY"},
    ],
)
def test_sandbox_still_rechecks_the_shipment_and_ceiling(change: dict[str, str]) -> None:
    r = sandbox()
    r.board.records[0].update(change)
    assert act(r, "confirm")["status"] == "failed"
    assert not r.board.sends


def test_voice_key_cannot_trigger_a_sandbox_confirmation() -> None:
    r = sandbox()
    response = r.client.post(
        "/bookings/LD09001/confirm",
        json={"version": 1, "rep": REP},
        headers={"Authorization": f"Bearer {AGENT}"},
    )
    assert response.status_code == 401
    assert not r.board.sends


@pytest.mark.parametrize("hours", [-1, 12, 13])
def test_sandbox_future_or_expired_windows_send_nothing(hours: int) -> None:
    r = sandbox()
    r.clock.now = START + timedelta(hours=hours)
    assert act(r, "confirm")["status"] == "sandbox_authorization_inactive"
    assert r.get("/ops/snapshot")["sandbox_booking_mc"] is None
    assert not r.board.sends


@pytest.mark.parametrize("target", ["call", "reservation", "run", "missing_reservation"])
def test_recent_edits_do_not_authorize_old_calls_or_reservations(target: str) -> None:
    r = sandbox()
    row = booking(r)
    old = (START - timedelta(seconds=1)).isoformat()
    if target == "call":
        r.twin.data("calls", row["call_id"])["started_at"] = old
    elif target == "reservation":
        row["events"][0]["at"] = old
        row["events"].append({"action": "reviewed", "at": START.isoformat()})
    elif target == "run":
        row["events"][0]["call_id"] = "a-different-call"
    else:
        row["events"] = []
    assert not r.get("/ops/snapshot")["bookings"][0]["sandbox_eligible"]
    assert act(r, "confirm")["status"] == "sandbox_record_not_authorized"
    assert not r.board.sends


def test_expiry_during_recheck_stops_the_send(monkeypatch: pytest.MonkeyPatch) -> None:
    r = sandbox()
    get = r.board.get

    async def expires(load_id: str) -> Any:
        load = await get(load_id)
        r.clock.now = START + timedelta(hours=12)
        return load

    monkeypatch.setattr(r.board, "get", expires)
    assert act(r, "confirm")["status"] == "sandbox_authorization_inactive"
    assert booking(r)["state"] == "RESERVED" and not r.board.sends


def test_expiry_after_dispatch_keeps_the_actual_receipt(monkeypatch: pytest.MonkeyPatch) -> None:
    r = sandbox()
    book = r.board.book

    async def expires(load_id: str, mc: str, rate: int) -> Any:
        result = await book(load_id, mc, rate)
        r.clock.now = START + timedelta(hours=12)
        return result

    monkeypatch.setattr(r.board, "book", expires)
    assert act(r, "confirm")["state"] == "ACK_PENDING"
    assert booking(r)["reference"] == "FIXTURE01" and len(r.board.sends) == 1


def test_uncertain_sandbox_send_is_saved_and_never_retried() -> None:
    r = sandbox()
    r.board.receipt = sent(b"", "receive", "TimeoutError")
    assert act(r, "confirm")["state"] == "UNKNOWN"
    assert act(r, "confirm")["status"] == "stale"
    assert len(r.board.sends) == 1


@pytest.mark.parametrize(
    "value", [None, "invalid", "2026-11-02T12:00:00", "2026-11-03T00:00:00+00:00"]
)
@pytest.mark.parametrize("target", ["call", "reservation"])
def test_missing_naive_and_end_boundary_timestamps_are_not_authorized(
    target: str, value: str | None
) -> None:
    r = sandbox()
    if target == "call":
        r.twin.data("calls", booking(r)["call_id"])["started_at"] = value
    else:
        booking(r)["events"][0]["at"] = value
    assert act(r, "confirm")["status"] == "sandbox_record_not_authorized"
    assert not r.board.sends


def test_expiry_while_claiming_persists_an_explicit_no_send_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    r = sandbox()
    write = r.desk._write

    async def expires(*args: Any, **kwargs: Any) -> bool:
        result = await write(*args, **kwargs)
        if args[2] == "confirm":
            r.clock.now = START + timedelta(hours=12)
        return result

    monkeypatch.setattr(r.desk, "_write", expires)
    result = act(r, "confirm")
    assert result["state"] == "FAILED"
    assert result["reason"] == "sandbox_authorization_inactive"
    assert not r.board.sends
    assert booking(r)["state"] == "FAILED"
    assert booking(r)["send"]["step"] == "authorize" and booking(r)["send"]["bytes"] == 0
