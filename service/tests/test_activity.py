"""Reconstruct business activity from persisted rows, without the voice platform logs."""

import json
from datetime import timedelta
from typing import Any

from pytest import MonkeyPatch

from service.tests.fake_tms import make_load
from service.tests.rig import RUN, rig


def test_multi_round_history_can_be_reconstructed_from_the_stored_row() -> None:
    r = rig(live_booking=False)
    r.board.records = [make_load()]
    r.verified()
    lane = {"equipment": "dry van", "origin_state": "TX", "dest_state": "GA"}
    assert r.post("/loads/search", **lane)["status"] == "found"
    for ask in ("5000.00", "5100"):
        assert r.post("/negotiate", load_id="LD09001", rate=ask)["status"] == "counter"
    agreed = r.post("/negotiate", load_id="LD09001", rate="1900")
    assert agreed["status"] == "agreed"
    r.post("/calls/close", summary="Agreed LD09001 at 1900; mocked rep handoff.")
    r.post("/calls/ended", ended_by="assistant", duration_seconds=90)
    row = r.twin.data("calls", RUN)
    history: Any = row["events"]
    assert [e["status"] for e in history if e["action"] == "send_code"] == ["code_issued", "sent"]
    search = next(e for e in history if e["action"] == "find_loads")
    assert search["search"] == {"equipment": "DRY_VAN", "origin_state": "TX", "dest_state": "GA"}
    [load] = search["loads"]
    assert (load["origin"], load["destination"], load["offer"]) == (
        "Dallas, TX",
        "Atlanta, GA",
        1900,
    )
    counters = [e for e in history if e["status"] == "counter"]
    assert [(e["heard"], e["ask"], e["offer"], e["round"]) for e in counters] == [
        ("5000.00", 5000, 1900, 1),
        ("5100", 5100, 1900, 2),
    ]
    deal = next(e for e in history if e["status"] == "agreed")
    assert (deal["load_id"], deal["rate"], row["summary"]) == (
        "LD09001",
        1900,
        "Agreed LD09001 at 1900; mocked rep handoff.",
    )
    assert history[-1]["ended_by"] == "assistant" and row["duration_seconds"] == 90
    assert r.board.sends == []


def test_search_history_survives_a_later_lane_and_a_failed_read() -> None:
    r = rig(live_booking=False)
    r.verified()
    r.post("/loads/search", equipment="dry van", origin_state="TX")
    r.board.down = True
    r.post("/loads/search", equipment="reefer", origin_state="KY")
    searches = [e for e in r.row()["events"] if e["action"] == "find_loads"]
    assert [e["status"] for e in searches] == ["no_match", "tms_unavailable"]
    assert [e["search"]["origin_state"] for e in searches] == ["TX", "KY"]


def test_new_activity_fields_never_copy_the_expected_code_or_marked_ceiling(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr("service.calls.codes.new_code", lambda: "814729")
    r = rig(live_booking=False)
    code = r.verified_with_code()
    r.post("/otp/verify", code=code)
    r.board.records = [make_load(MAX_BUY="9876543")]
    replies = [r.post("/loads/search", equipment="dry van")]
    replies.append(r.post("/negotiate", load_id="LD09001", rate="1900"))
    replies.append(r.post("/calls/ended", ended_by="user", duration_seconds=35))
    snapshot = r.get("/ops/snapshot")
    for output in (replies, r.row()["events"], r.twin.data("bookings", "LD09001"), snapshot):
        text = json.dumps(output)
        assert "9876543" not in text and "max_rate" not in text and code not in text


def test_end_before_first_tool_records_no_invented_verification_or_summary() -> None:
    r = rig(live_booking=False)
    r.clock.now += timedelta(seconds=21)
    r.post("/calls/ended", ended_by="user", duration_seconds=21)
    [call] = r.get("/ops/snapshot")["calls"]
    assert (call["mc"], call["verified_at"], call["summary"]) == (None, None, None)
    assert call["outcome"] == "ended_without_close"
    assert [e["action"] for e in call["events"]] == ["call_ended"]
    assert r.board.queries == [] and r.board.sends == []
