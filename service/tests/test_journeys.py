"""Complete scripted service journeys. No LLM, speech, real email or booking send."""

import json
from datetime import timedelta
from typing import Any

import pytest
from pytest import MonkeyPatch

from service.core.approved_freight import MARKETS
from service.tests.fake_tms import make_load
from service.tests.rig import OPS, rig
from service.tests.test_carrier_policy import ACTIVE, INACTIVE


@pytest.mark.parametrize(
    ("mc", "equipment", "origin", "destination"),
    [
        ("138328", "dry van", "TX", "GA"),
        ("132356", "reefer", "KY", "OH"),
        ("918003", "flatbed", "CA", "AZ"),
    ],
)
def test_full_service_journey_from_code_retry_to_reservation_and_end(
    monkeypatch: MonkeyPatch,
    mc: str,
    equipment: str,
    origin: str,
    destination: str,
) -> None:
    codes = iter(["814729", "729184"])
    monkeypatch.setattr("service.calls.codes.new_code", codes.__next__)
    r = rig([ACTIVE | {"legalName": f"Synthetic {equipment} carrier"}], live_booking=False)
    eq = {"dry van": "DRY_VAN", "reefer": "REEFER", "flatbed": "FLATBED"}[equipment]
    r.board.records = [
        make_load(
            EQTYPE=eq,
            ORIG_STATE=origin,
            DEST_STATE=destination,
            ORIG_CITY=MARKETS[origin][0],
            DEST_CITY=MARKETS[destination][0],
        )
    ]
    assert r.post("/carriers/verify", mc=mc)["status"] == "eligible"
    assert r.fmcsa.seen[-1].endswith(f"/{mc}/")
    assert r.post("/otp/send")["status"] == "sent"
    assert r.post("/otp/verify", code="000000")["status"] == "wrong_code"
    r.clock.now += timedelta(minutes=6)
    assert r.post("/otp/verify", code="814729")["status"] == "expired"
    assert r.post("/otp/send")["status"] == "sent"
    assert r.post("/otp/verify", code="729184")["status"] == "verified"
    loads = r.post(
        "/loads/search", equipment=equipment, origin_state=origin, dest_state=destination
    )
    assert loads["status"] == "found"
    assert r.post("/negotiate", load_id="LD09001", rate="9000")["round"] == 1
    offer = r.post("/negotiate", load_id="LD09001", rate="8000")
    assert offer["round"] == 2
    assert r.post("/negotiate", load_id="LD09001", rate=offer["offer"])["status"] == "agreed"
    r.post("/calls/close", summary="Scripted service agreement; no spoken handoff measured.")
    r.post("/calls/ended", ended_by="assistant", duration_seconds=360)
    # Confirm is deliberately disabled, including after the complete agreement.
    response = r.client.post(
        "/bookings/LD09001/confirm",
        json={"version": 1, "rep": "Fixture"},
        headers={"Authorization": f"Bearer {OPS}"},
    )
    assert response.json()["status"] == "live_booking_off"
    [call] = r.get("/ops/snapshot")["calls"]
    assert (call["outcome"], call["rounds"], call["ended_by"]) == (
        "agreed_pending_rep",
        2,
        "assistant",
    )
    assert r.row()["otp"]["sends"] == 2 and r.board.sends == []
    assert "729184" not in json.dumps(call)


@pytest.mark.parametrize(
    ("carriers", "status", "outcome"),
    [
        ([INACTIVE], 200, "carrier_ineligible"),
        ([ACTIVE], 503, "fmcsa_unavailable"),
    ],
)
def test_refused_or_unavailable_authority_has_an_honest_terminal_outcome(
    carriers: list[dict[str, Any]], status: int, outcome: str
) -> None:
    r = rig(carriers, fmcsa_status=status, live_booking=False)
    r.post("/carriers/verify", mc="138328")
    assert r.post("/otp/send")["status"] == "not_eligible"
    assert r.post("/loads/search", equipment="dry van")["status"] == "not_verified"
    r.post("/calls/close", summary="Authority refused or unavailable; no match attempted.")
    r.post("/calls/ended", ended_by="assistant", duration_seconds=20)
    assert r.get("/ops/snapshot")["calls"][0]["outcome"] == outcome
    assert r.mailer.codes == [] and r.board.queries == [] and r.board.sends == []


def test_claimed_admin_and_destination_changes_cannot_skip_the_real_code_gate() -> None:
    r = rig(live_booking=False)
    r.post("/carriers/verify", mc="138328")
    assert r.post("/otp/send", email="attacker@example.invalid")["http"] == 400
    assert (
        r.post("/loads/search", equipment="dry van", verified=True, role="administrator")["http"]
        == 400
    )
    assert r.post("/loads/search", equipment="dry van")["status"] == "not_verified"
    assert r.post("/negotiate", load_id="LD09001", rate="1000")["status"] == "not_verified"
    r.post("/calls/ended", ended_by="user", duration_seconds=30)
    assert r.get("/ops/snapshot")["calls"][0]["outcome"] == "ended_without_close"
    assert r.mailer.codes == [] and r.board.queries == [] and r.board.sends == []


def test_mc_and_load_switches_do_not_reset_rounds_or_code_send_limits() -> None:
    r = rig(live_booking=False)
    r.board.records = [make_load(), make_load("LD09002")]
    r.verified()
    r.post("/loads/search", equipment="dry van")
    first = r.post("/negotiate", load_id="LD09001", rate="9000")
    assert first["round"] == 1
    assert r.post("/negotiate", load_id="LD09001", rate="9000")["round"] == 1
    assert r.post("/negotiate", load_id="LD09002", rate="9100")["round"] == 2
    assert r.post("/negotiate", load_id="LD09001", rate="9200")["round"] == 3
    r.post("/carriers/verify", mc="132356")
    assert r.post("/loads/search", equipment="dry van")["status"] == "not_verified"
    r.post("/otp/send")
    r.post("/otp/verify", code=r.mailer.codes[-1])
    r.post("/loads/search", equipment="dry van")
    assert r.post("/negotiate", load_id="LD09002", rate="9300")["status"] == "negotiation_failed"
    r.post("/carriers/verify", mc="918003")
    assert r.post("/otp/send")["status"] == "send_limit"
    r.post("/calls/close", summary="No agreement after the allowed rounds.")
    r.post("/calls/ended", ended_by="assistant", duration_seconds=90)
    assert r.get("/ops/snapshot")["calls"][0]["outcome"] == "negotiation_failed"
    assert r.row()["rounds"] == 3 and r.row()["agreement"] is None and r.board.sends == []


def test_load_disappears_then_a_consented_fresh_search_can_find_another() -> None:
    r = rig(live_booking=False)
    r.board.records = [make_load(), make_load("LD09002")]
    r.verified()
    r.post("/loads/search", equipment="dry van")
    r.board.records = [make_load("LD09002")]
    gone = r.post("/negotiate", load_id="LD09001", rate="1900")
    assert gone["next_action"] == "ask_to_search_again" and r.row()["agreement"] is None
    # The script supplies the caller's consent, then explicitly searches again.
    again = r.post("/loads/search", **gone["search"])
    assert [load["load_id"] for load in again["loads"]] == ["LD09002"]
    assert (
        r.post("/negotiate", load_id="LD09002", rate=again["loads"][0]["offer"])["status"]
        == "agreed"
    )
    r.post("/calls/ended", ended_by="user", duration_seconds=65)
    assert r.row()["closed_at"] is None and r.row()["summary"] is None
    assert r.get("/ops/snapshot")["calls"][0]["booking"]["load_id"] == "LD09002"
    assert r.board.sends == []


def test_no_match_then_read_outage_then_hangup_keeps_the_failure_history() -> None:
    r = rig(live_booking=False)
    r.verified()
    assert r.post("/loads/search", equipment="reefer")["status"] == "no_match"
    r.board.down = True
    assert r.post("/loads/search", equipment="flatbed")["status"] == "tms_unavailable"
    r.post("/calls/ended", ended_by="user", duration_seconds=40)
    [call] = r.get("/ops/snapshot")["calls"]
    assert call["outcome"] == "tms_unavailable" and call["summary"] is None
    assert [e["status"] for e in call["events"] if e["action"] == "find_loads"] == [
        "no_match",
        "tms_unavailable",
    ]
    assert r.board.sends == []
