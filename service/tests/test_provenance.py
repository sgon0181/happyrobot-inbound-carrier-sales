"""Fresh native links come from the trusted integration, and imported rows are immutable."""

import asyncio
import copy

from service.bookings import Bookings
from service.tests.rig import RUN, START, rig
from service.tests.test_rep_actions import act, booking, reserved

NATIVE = {"workspace": "our-workspace", "workflow_id": "6oaskq84xpfc"}


def test_provenance_is_assigned_only_at_creation_and_cannot_be_supplied_by_a_caller() -> None:
    native = dict(NATIVE)
    r = rig(native_workflow=native)
    native["workspace"] = "changed-after-configuration"
    r.verified()
    assert r.row()["native_workflow"] == NATIVE
    assert r.get("/ops/snapshot")["calls"][0]["native_workflow"] == NATIVE
    bad = r.post("/carriers/verify", mc="138328", native_workflow={"workspace": "evil"})
    assert bad["http"] == 400
    newer = rig(native_workflow={"workspace": "new", "workflow_id": "new"})
    newer.twin.tables = r.twin.tables
    newer.post("/carriers/verify", mc="138328")
    assert newer.row()["native_workflow"] == NATIVE


def test_older_calls_do_not_acquire_configured_native_provenance_on_an_update() -> None:
    old = rig()
    old.verified()
    new = rig(native_workflow=NATIVE)
    new.twin.tables = old.twin.tables
    new.post("/carriers/verify", mc="138328")
    assert new.row().get("native_workflow") is None


def test_imported_call_terminal_retries_and_booking_actions_are_read_only() -> None:
    r = reserved()
    r.row()["read_only"] = True
    booking(r)["read_only"] = True
    before = r.twin.tables["calls"][RUN][0]
    for path in ("/calls/close", "/calls/ended"):
        assert r.post(path)["status"] == "call_closed"
    assert r.post("/otp/send")["status"] == "call_closed"
    for action in ("confirm", "decline", "reconcile"):
        assert act(r, action)["status"] == "record_read_only"
    assert r.twin.tables["calls"][RUN][0] == before
    assert r.twin.tables["bookings"]["LD09001"][0] == 1
    assert not r.board.sends
    assert r.get("/ops/snapshot")["bookings"][0]["read_only"]


def test_released_imported_load_is_never_reused_or_voided_by_a_fresh_call() -> None:
    r = rig()
    historical = {"state": "RELEASED", "read_only": True, "call_id": "old", "events": []}
    r.twin.tables["bookings"]["LD09001"] = (1, copy.deepcopy(historical))

    async def run() -> None:
        bookings = Bookings(r.twin.twin())
        assert await bookings.held(["LD09001"]) == frozenset({"LD09001"})
        assert (
            await bookings.reserve(
                "LD09001",
                claim_id="new",
                call_id=RUN,
                mc="138328",
                rate=1850,
                cohort="real",
                now=START,
            )
            is None
        )
        assert await bookings.void("LD09001", claim_id="new", call_id=RUN, now=START) is None

    asyncio.run(run())
    assert r.twin.tables["bookings"]["LD09001"] == (1, historical)


def test_imported_source_call_cannot_authorize_a_booking_without_its_own_import_marker() -> None:
    r = reserved()
    r.row()["read_only"] = True
    assert not booking(r).get("read_only")
    assert act(r, "confirm")["status"] == "agreement_incomplete"
    assert not r.board.sends and booking(r)["state"] == "RESERVED"
