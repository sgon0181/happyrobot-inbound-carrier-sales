"""Delayed work must still belong to the call's current carrier and cohort."""

import copy
from typing import Any

import pytest

from service.bookings import Bookings
from service.calls import CallRows
from service.core import codes
from service.tests.rig import RUN, START, FakeMailer, Rig, rig
from service.tests.test_selling import counter, offered


def change_call(r: Rig, **changes: Any) -> None:
    version, data = r.twin.tables["calls"][RUN]
    r.twin.tables["calls"][RUN] = (version + 1, data | changes)


def test_an_agreement_locks_the_carrier_without_a_lookup_or_write() -> None:
    r = offered()
    assert counter(r, 1850)["status"] == "agreed"
    before = copy.deepcopy(r.twin.tables)
    lookups = list(r.fmcsa.seen)
    assert r.post("/carriers/verify", mc="777777")["status"] == "carrier_locked"
    assert r.twin.tables == before
    assert r.fmcsa.seen == lookups
    assert r.row()["mc"] == r.row()["agreement"]["mc"] == "138328"
    assert r.post("/carriers/verify", mc="138328")["status"] == "eligible"
    assert counter(r, 1850)["status"] == "agreed"  # the original carrier can still recover


def test_a_claim_locks_the_carrier_before_reserving(monkeypatch: pytest.MonkeyPatch) -> None:
    r = offered()
    reserve = Bookings.reserve

    async def delayed(self: Bookings, *args: Any, **kwargs: Any) -> Any:
        before = copy.deepcopy(r.row())
        assert r.post("/carriers/verify", mc="777777")["status"] == "carrier_locked"
        assert r.row() == before
        return await reserve(self, *args, **kwargs)

    monkeypatch.setattr(Bookings, "reserve", delayed)
    assert counter(r, 1850)["status"] == "agreed"
    assert r.row()["agreement"]["mc"] == "138328"
    assert r.twin.data("bookings", "LD09001")["mc"] == "138328"


@pytest.mark.parametrize("changes", [{"mc": "777777"}, {"eligible": False}, {"verified_at": None}])
def test_settlement_rechecks_identity_and_verification(
    monkeypatch: pytest.MonkeyPatch, changes: dict[str, Any]
) -> None:
    r = offered()
    reserve = Bookings.reserve
    held = None

    async def delayed(self: Bookings, *args: Any, **kwargs: Any) -> Any:
        nonlocal held
        result = await reserve(self, *args, **kwargs)
        held = copy.deepcopy(r.twin.tables["bookings"])
        change_call(r, **changes)  # a legacy writer or same-MC recheck won before settlement
        return result

    monkeypatch.setattr(Bookings, "reserve", delayed)
    assert counter(r, 1850)["status"] == "not_verified"
    assert r.row()["agreement"] is None
    assert r.row()["accepting"]["mc"] == "138328"
    assert r.twin.tables["bookings"] == held
    if "mc" not in changes:
        change_call(r, eligible=True, verified_at=START.isoformat())
        r.board.down = True  # recovery uses the held booking, without another TMS read
        assert counter(r, 1850)["status"] == "agreed"
        assert r.row()["accepting"] is None
        assert r.twin.tables["bookings"] == held


@pytest.mark.parametrize("changes", [{"eligible": False}, {"mc": "777777"}])
def test_agreement_replay_rechecks_the_call_inside_its_write(
    monkeypatch: pytest.MonkeyPatch, changes: dict[str, Any]
) -> None:
    r = offered()
    assert counter(r, 1850)["status"] == "agreed"
    booking = copy.deepcopy(r.twin.tables["bookings"])
    read = CallRows.read

    async def delayed(self: CallRows, run_id: str) -> Any:
        snapshot = await read(self, run_id)
        change_call(r, **changes)
        return snapshot

    monkeypatch.setattr(CallRows, "read", delayed)
    assert counter(r, 1850)["status"] == "not_verified"
    assert r.twin.tables["bookings"] == booking


def test_reservation_keeps_the_call_cohort_across_a_process_setting_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    r = offered()
    change_call(r, cohort="synthetic")
    step = CallRows.step

    async def flip(self: CallRows, *args: Any, **kwargs: Any) -> Any:
        reply = await step(self, *args, **kwargs)
        if reply["status"] == "accepting":
            self.cohort = "real"  # settings changed after the persisted claim was made
        return reply

    monkeypatch.setattr(CallRows, "step", flip)
    assert counter(r, 1850)["status"] == "agreed"
    assert r.row()["cohort"] == "synthetic"
    assert r.twin.data("bookings", "LD09001")["cohort"] == "synthetic"


def test_an_early_refusal_that_no_longer_applies_returns_busy_without_using_a_round(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    r = offered()
    verified_at = r.row()["verified_at"]
    change_call(r, verified_at=None)
    read = CallRows.read

    async def delayed(self: CallRows, run_id: str) -> Any:
        snapshot = await read(self, run_id)
        change_call(r, verified_at=verified_at)
        return snapshot

    monkeypatch.setattr(CallRows, "read", delayed)
    assert counter(r, 1850)["status"] == "busy"
    assert r.row()["rounds"] == 0 and r.row()["agreement"] is None
    assert r.twin.tables["bookings"] == {}


def test_settlement_refuses_a_booking_owned_by_a_different_mc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    r = offered()
    reserve = Bookings.reserve

    async def delayed(self: Bookings, *args: Any, **kwargs: Any) -> Any:
        result = await reserve(self, *args, **kwargs)
        assert result is not None
        return result | {"mc": "777777"}

    monkeypatch.setattr(Bookings, "reserve", delayed)
    assert counter(r, 1850)["status"] == "not_verified"
    assert r.row()["agreement"] is None and r.row()["accepting"] is not None
    assert r.twin.data("bookings", "LD09001")["state"] == "RESERVED"


@pytest.mark.parametrize("fails", [False, True])
def test_email_completion_belongs_to_the_mc_that_requested_it(
    monkeypatch: pytest.MonkeyPatch, fails: bool
) -> None:
    r = rig()
    assert r.post("/carriers/verify", mc="138328")["status"] == "eligible"
    send = FakeMailer.send

    async def delayed(self: FakeMailer, code: str) -> None:
        assert r.post("/carriers/verify", mc="777777")["status"] == "eligible"
        self.fail = fails
        await send(self, code)

    monkeypatch.setattr(FakeMailer, "send", delayed)
    assert r.post("/otp/send")["status"] == "superseded"
    event = r.row()["events"][-1]
    assert (event["mc"], event["status"]) == ("138328", "superseded")
    assert event["delivery"] == ("send_failed" if fails else "sent")
    assert r.row()["mc"] == "777777" and r.row()["otp"]["hash"] is None


def test_a_resend_with_identical_digits_still_supersedes_the_older_delivery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    r = rig()
    assert r.post("/carriers/verify", mc="138328")["status"] == "eligible"
    monkeypatch.setattr(codes, "new_code", lambda: "123456")
    send = FakeMailer.send
    deliveries = 0

    async def delayed(self: FakeMailer, code: str) -> None:
        nonlocal deliveries
        deliveries += 1
        if deliveries == 1:
            assert r.post("/otp/send")["status"] == "sent"
        await send(self, code)

    monkeypatch.setattr(FakeMailer, "send", delayed)
    assert r.post("/otp/send")["status"] == "superseded"
    events = [e for e in r.row()["events"] if e["action"] == "send_code"]
    assert [(e["send_number"], e["status"]) for e in events] == [
        (1, "code_issued"),
        (2, "code_issued"),
        (2, "sent"),
        (1, "superseded"),
    ]
    assert r.row()["otp"]["sends"] == 2
    assert "hash" not in str(events) and "123456" not in str(events)
