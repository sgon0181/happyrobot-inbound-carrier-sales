"""Load search over HTTP: verified calls only, open loads only, our offer and never the ceiling."""

import asyncio
import json
from typing import Any

from service.bookings import Bookings
from service.sale_decisions import abandon as _abandon
from service.sale_decisions import settle as _settle
from service.tests.fake_tms import make_load
from service.tests.rig import RUN, START, Rig, rig

LANE = {"equipment": "dry van", "origin_state": "tx", "dest_state": "GA"}
PUBLIC = {
    "load_id",
    "origin",
    "destination",
    "pickup_datetime",
    "delivery_datetime",
    "pickup_time_display",
    "delivery_time_display",
    "equipment_type",
    "miles",
    "weight",
    "commodity_type",
    "num_of_pieces",
    "dimensions",
    "notes",
    "offer",
}


def selling(*records: dict[str, str], verified: bool = True) -> Rig:
    r = rig()
    r.board.records = list(records)
    if verified:
        r.verified()
    return r


def search(r: Rig, **terms: Any) -> Any:
    return r.post("/loads/search", **(LANE | terms))


def test_no_load_is_read_until_the_call_has_passed_its_code() -> None:
    r = selling(make_load(), verified=False)
    assert search(r)["status"] == "not_verified"
    r.verified_with_code()  # eligible, but the code is not checked yet
    assert search(r)["status"] == "not_verified"
    assert r.board.queries == []


def test_open_loads_on_the_lane_come_earliest_first_with_our_offer() -> None:
    r = selling(
        make_load("LD09001"),
        make_load("LD09002", PICKUP_DT="20990601080000"),
        make_load("LD09003", STATUS="PENDING"),
        make_load("LD09004", PICKUP_DT="20000101080000"),
        make_load("LD09005", DEST_STATE="FL"),
        make_load("LD01086"),  # on the blocked list
    )
    reply = search(r)
    assert reply["status"] == "found"
    assert [load["load_id"] for load in reply["loads"]] == ["LD09002", "LD09001"]
    assert all(set(load) == PUBLIC and load["offer"] == 1900 for load in reply["loads"])
    assert r.board.queries == [{"equipment": "DRY_VAN", "origin": "TX", "dest": "GA"}]
    row = r.row()
    assert row["offers"] == {"LD09002": 1900, "LD09001": 1900}
    assert row["search"] == {"equipment": "DRY_VAN", "origin_state": "TX", "dest_state": "GA"}
    assert row["events"][-1]["loads"] == reply["loads"]  # what was pitched, as pitched


def test_the_ceiling_reaches_neither_the_agent_nor_the_row() -> None:
    r = selling(make_load(MAX_BUY="2345"))
    reply = search(r)
    assert reply["status"] == "found"
    for text in (json.dumps(reply), json.dumps(r.row())):
        assert "2345" not in text
        assert "max_rate" not in text
        assert "loadboard_rate" not in text


def test_every_ask_and_answer_survives_on_the_call_s_events() -> None:
    r = offered()
    replies = [counter(r, 9000), counter(r, "nine thousand one hundred"), counter(r, 9100)]
    asks = [e for e in r.row()["events"] if e["action"] == "negotiate"]
    assert [(e["heard"], e["ask"], e["load_id"]) for e in asks] == [
        ("9000", 9000, "LD09001"),
        ("nine thousand one hundred", None, "LD09001"),
        ("9100", 9100, "LD09001"),
    ]
    assert [e["status"] for e in asks] == [x["status"] for x in replies]
    assert [e.get("offer") for e in asks] == [x.get("offer") for x in replies]
    assert "ask" not in replies[0] and "heard" not in replies[0]  # kept for the record only


def test_a_call_that_changes_mc_during_the_search_gets_no_offers() -> None:
    r = selling(make_load())

    def caller_gives_another_mc() -> None:
        version, data = r.twin.tables["calls"][RUN]
        r.twin.tables["calls"][RUN] = (version + 1, data | {"mc": "1515", "eligible": False})

    r.board.during = caller_gives_another_mc
    assert search(r)["status"] == "not_verified"
    assert r.row()["offers"] == {}


def test_a_held_load_is_skipped_and_a_freed_one_is_offered() -> None:
    r = selling(make_load("LD09001"), make_load("LD09002"))
    r.booking("LD09001", "RESERVED")
    r.booking("LD09002", "RELEASED")
    assert [load["load_id"] for load in search(r)["loads"]] == ["LD09002"]


def test_no_match_is_recorded_with_what_was_asked() -> None:
    r = selling()
    assert search(r)["status"] == "no_match"
    assert (r.row()["outcome"], r.row()["search"]["dest_state"]) == ("no_match", "GA")


def test_a_load_without_a_usable_ceiling_goes_to_pricing_review() -> None:
    r = selling(make_load(MAX_BUY=""))
    assert search(r)["status"] == "pricing_review_required"
    assert (r.row()["outcome"], r.row()["offers"]) == ("pricing_review_required", {})


def test_a_tms_outage_is_reported_not_hidden() -> None:
    r = selling(make_load("LD09001"), make_load("LD09002"))
    r.board.unreadable = {"LD09001"}
    assert [load["load_id"] for load in search(r)["loads"]] == ["LD09002"]  # one read failed
    r.board.unreadable = {"LD09001", "LD09002"}
    assert search(r)["status"] == "tms_unavailable"  # every read failed
    r.board.down = True
    assert search(r)["status"] == "tms_unavailable"
    assert r.row()["outcome"] == "tms_unavailable"


def test_unreadable_terms_are_refused_before_the_tms_is_asked() -> None:
    r = selling(make_load())
    for terms in ({"equipment": "spaceship"}, {"origin_state": "Texas"}, dict.fromkeys(LANE, "")):
        assert search(r, **terms)["status"] == "invalid_search"
    assert r.board.queries == []


def test_a_repeat_search_keeps_the_offer_already_made() -> None:
    r = selling(make_load())
    search(r)
    version, data = r.twin.tables["calls"][RUN]
    r.twin.tables["calls"][RUN] = (version + 1, data | {"offers": {"LD09001": 2050}})
    assert search(r)["loads"][0]["offer"] == 2050


def test_a_new_mc_clears_the_offers() -> None:
    r = selling(make_load())
    search(r)
    r.post("/carriers/verify", mc="1515")
    assert r.row()["offers"] == {}


def test_a_kept_offer_never_exceeds_a_lowered_ceiling() -> None:
    r = selling(make_load())
    assert search(r)["loads"][0]["offer"] == 1900
    r.board.records = [make_load(MAX_BUY="1800", RATE="1500")]
    offer = search(r)["loads"][0]["offer"]
    assert offer < 1800 and r.row()["offers"]["LD09001"] == offer


def test_details_that_differ_from_the_search_result_are_rechecked() -> None:
    r = selling(make_load())
    summary = make_load()
    r.board.records = [summary]
    detail = make_load(EQTYPE="REEFER", ORIG_STATE="CA")
    r.board.details = {"LD09001": detail}
    assert search(r)["status"] == "no_match"


def test_a_failed_search_on_a_call_that_lost_verification_changes_nothing() -> None:
    r = selling(make_load())

    def caller_gives_another_mc() -> None:
        version, data = r.twin.tables["calls"][RUN]
        update = {"mc": "1515", "eligible": False, "outcome": "carrier_ineligible"}
        r.twin.tables["calls"][RUN] = (version + 1, data | update)

    r.board.during, r.board.unreadable = caller_gives_another_mc, {"LD09001"}
    assert search(r)["status"] == "not_verified"
    assert r.row()["outcome"] == "carrier_ineligible"


def test_a_tms_outage_records_what_was_asked() -> None:
    r = selling()
    r.board.down = True
    search(r)
    assert r.row()["search"]["origin_state"] == "TX"


def offered(*records: dict[str, str]) -> Rig:
    r = selling(*(records or (make_load(),)))
    assert search(r)["status"] == "found"
    return r


def counter(r: Rig, rate: Any, load_id: str = "LD09001") -> Any:
    return r.post("/negotiate", load_id=load_id, rate=rate)


def test_an_ask_at_or_below_our_offer_reserves_the_load_at_that_rate() -> None:
    r = offered()
    assert counter(r, 1850) == {"status": "agreed", "load_id": "LD09001", "rate": 1850, "http": 200}
    booking = r.twin.data("bookings", "LD09001")
    assert (booking["state"], booking["call_id"], booking["rate"]) == ("RESERVED", RUN, 1850)
    assert r.row()["agreement"] == {"load_id": "LD09001", "rate": 1850, "mc": "138328"}
    assert counter(r, 1850)["status"] == "agreed"  # a repeat finds its own reservation


def test_three_rounds_at_most_then_the_call_fails_without_a_handoff() -> None:
    r = offered()
    replies = [counter(r, 9000 + n) for n in range(4)]
    assert [x["status"] for x in replies] == [
        "counter",
        "counter",
        "final_offer",
        "negotiation_failed",
    ]
    offers = [x["offer"] for x in replies[:3]]
    assert offers == sorted(offers) and offers[-1] < 2300  # rising, never past the ceiling
    assert (r.row()["rounds"], r.row()["outcome"]) == (3, "negotiation_failed")
    assert counter(r, 1000)["status"] == "negotiation_failed"
    assert "LD09001" not in r.twin.tables["bookings"]


def test_the_same_ask_twice_uses_one_round() -> None:
    r = offered()
    first = counter(r, 9000)
    assert counter(r, "9000.00") == first | {"http": 200}
    assert r.row()["rounds"] == 1


def test_rounds_count_across_loads() -> None:
    r = offered(make_load("LD09001"), make_load("LD09002"))
    counter(r, 9000, "LD09001")
    counter(r, 9001, "LD09001")
    assert counter(r, 9000, "LD09002")["status"] == "final_offer"


def test_a_load_another_call_reserved_is_gone() -> None:
    r = offered()
    r.booking("LD09001", "RESERVED")
    assert counter(r, 1800)["status"] == "load_gone"
    assert r.row()["offers"] == {} and r.row()["agreement"] is None


def test_negotiation_needs_a_verified_call_and_an_offered_load() -> None:
    r = selling(make_load(), verified=False)
    assert counter(r, 1800)["status"] == "not_verified"
    r = offered()
    assert counter(r, 1800, "LD09999")["status"] == "search_required"


def test_a_load_that_closed_or_lost_its_ceiling_is_dropped() -> None:
    r = offered()
    r.board.records = [make_load(STATUS="PENDING")]
    assert counter(r, 1800)["status"] == "load_gone"
    r = offered()
    r.board.down = True
    assert counter(r, 1800)["status"] == "tms_unavailable"


def test_one_agreement_per_call_and_an_unclear_ask_uses_no_round() -> None:
    r = offered(make_load("LD09001"), make_load("LD09002"))
    assert counter(r, "about two grand")["status"] == "ask_again"
    assert r.row()["rounds"] == 0
    counter(r, 1800, "LD09001")
    assert counter(r, 1800, "LD09002")["status"] == "already_agreed"
    assert "LD09002" not in r.twin.tables["bookings"]


def test_a_freed_load_can_be_reserved_again_keeping_its_history() -> None:
    r = offered()
    r.twin.tables["bookings"]["LD09001"] = (
        1,
        {"state": "RELEASED", "call_id": "old", "events": [{"seq": 1, "action": "reserved"}]},
    )
    assert counter(r, 1800)["status"] == "agreed"
    events: Any = r.twin.data("bookings", "LD09001")["events"]
    assert [e["seq"] for e in events] == [1, 2]


def meanwhile(r: Rig, **changes: Any) -> None:
    """Change the call row while the TMS read is in flight, as a concurrent request would."""

    def change(load_id: str) -> None:
        version, data = r.twin.tables["calls"][RUN]
        r.twin.tables["calls"][RUN] = (version + 1, data | changes)

    r.board.reading = change


def test_one_call_cannot_accept_two_loads_at_once() -> None:
    r = offered(make_load("LD09001"), make_load("LD09002"))
    meanwhile(r, accepting={"load_id": "LD09001", "rate": 1800, "mc": "138328"})
    assert counter(r, 1800, "LD09002")["status"] == "already_agreed"
    assert "LD09002" not in r.twin.tables["bookings"]


def test_an_acceptance_needs_verification_when_it_is_written() -> None:
    r = offered()
    meanwhile(r, mc="1515", eligible=False)
    assert counter(r, 1800)["status"] == "not_verified"
    assert r.twin.tables["bookings"] == {}


def test_a_repeated_ask_is_answered_within_todays_ceiling() -> None:
    r = offered()
    first = counter(r, 9000)
    r.board.records = [make_load(MAX_BUY="1800", RATE="1500")]
    again = counter(r, 9000)
    assert again["offer"] < min(first["offer"], 1800)  # repriced, not replayed
    assert r.row()["rounds"] == 1


CLAIM_TERMS = {"rate": 1850, "mc": "138328"}
CLAIM = {"id": "a1", "load_id": "LD09001", **CLAIM_TERMS}


def stranded(r: Rig, *, booked: bool) -> None:
    """An earlier accept claimed the load, and then a write failed."""
    version, data = r.twin.tables["calls"][RUN]
    r.twin.tables["calls"][RUN] = (version + 1, data | {"accepting": CLAIM})
    if booked:
        booking = {
            "state": "RESERVED",
            "call_id": RUN,
            "claim_id": "a1",
            "rate": 1850,
            "mc": "138328",
        }
        r.twin.tables["bookings"]["LD09001"] = (1, booking)


def test_a_retry_finishes_the_first_attempt_from_its_booking() -> None:
    r = offered()
    stranded(r, booked=True)
    r.board.records = [make_load(STATUS="PENDING")]  # recovered before the TMS is read
    assert counter(r, 1800)["rate"] == 1850
    assert r.row()["agreement"]["rate"] == 1850 and r.row()["accepting"] is None


def test_a_booking_reserved_before_claim_ids_is_recovered_not_voided() -> None:
    r = offered()
    stranded(r, booked=True)
    _, legacy = r.twin.tables["bookings"]["LD09001"]
    legacy.pop("claim_id")  # the row as 857212d wrote it
    r.board.records = [make_load(MAX_BUY="1800", RATE="1500")]  # today's cap is below 1850
    assert counter(r, 1850) == {"status": "agreed", "load_id": "LD09001", "rate": 1850, "http": 200}
    assert r.row()["agreement"]["rate"] == 1850 and r.row()["accepting"] is None
    booking = r.twin.data("bookings", "LD09001")
    assert (booking["state"], booking.get("void_claims")) == ("RESERVED", None)


def test_a_claim_without_a_booking_is_dropped_and_priced_afresh() -> None:
    r = offered()
    stranded(r, booked=False)
    r.board.records = [make_load(MAX_BUY="1800", RATE="1500")]
    assert counter(r, 1850)["status"] == "counter"  # 1850 is above today's cap
    booking = r.twin.data("bookings", "LD09001")
    assert (booking["state"], booking["void_claims"]) == ("UNCLAIMED", ["a1"])
    assert r.row()["accepting"] is None


def test_a_paused_first_request_cannot_reserve_after_its_claim_is_voided() -> None:
    r = offered(make_load("LD09001"), make_load("LD09002"))
    stranded(r, booked=False)  # request A claimed LD09001 and paused before reserving
    r.board.records = [make_load("LD09001", MAX_BUY="1800", RATE="1500"), make_load("LD09002")]
    assert counter(r, 1850)["status"] == "counter"  # a retry voids A's claim
    assert counter(r, 1800, "LD09002")["status"] == "agreed"  # then B is accepted
    resumed = asyncio.run(
        Bookings(r.twin.twin()).reserve(
            "LD09001", claim_id="a1", call_id=RUN, mc="138328", rate=1850, cohort="real", now=START
        )
    )
    assert resumed is None  # A resumes, and the booking row refuses it
    held = [k for k, (_, row) in r.twin.tables["bookings"].items() if row["state"] == "RESERVED"]
    assert held == ["LD09002"] and r.row()["agreement"]["load_id"] == "LD09002"


def test_voiding_a_claim_that_already_reserved_returns_its_booking() -> None:
    r = offered()
    stranded(r, booked=True)
    bookings = Bookings(r.twin.twin())
    held = asyncio.run(bookings.void("LD09001", claim_id="a1", call_id=RUN, now=START))
    assert held is not None and held["rate"] == 1850
    assert asyncio.run(bookings.void("LD09009", claim_id="z", call_id=RUN, now=START)) is None
    again = asyncio.run(bookings.void("LD09009", claim_id="z", call_id=RUN, now=START))
    events: Any = r.twin.data("bookings", "LD09009")["events"]
    assert again is None and len(events) == 1  # voided once


def test_a_late_settlement_never_clears_a_newer_claim() -> None:
    newer = CLAIM | {"id": "b2"}
    data: dict[str, Any] = {"accepting": newer, "offers": {}}
    assert _settle("a1", None)(data, START) == {"status": "superseded"}
    assert data["accepting"] == newer
    assert _abandon("a1")(data, START) == {"status": "claim_dropped"}
    assert data["accepting"] == newer


def test_a_failed_negotiation_survives_every_other_route() -> None:
    r = offered()
    for n in range(4):
        counter(r, 9000 + n)
    r.board.down = True
    search(r)
    r.post("/carriers/verify", mc="138328")
    assert r.row()["outcome"] == "negotiation_failed"
    assert counter(r, 1000)["status"] == "negotiation_failed"


def test_concurrent_counters_each_use_their_own_round() -> None:
    r = offered()
    meanwhile(r, rounds=1)  # another counter landed during this one's read
    assert counter(r, 9000)["round"] == 2


def test_a_new_search_does_not_reopen_a_failed_negotiation() -> None:
    r = offered()
    for n in range(4):
        counter(r, 9000 + n)
    search(r)
    r.board.records = []
    search(r)  # no match either
    assert r.row()["outcome"] == "negotiation_failed"
    assert counter(r, 1000)["status"] == "negotiation_failed"


def test_each_reservation_event_names_its_call_mc_and_rate() -> None:
    r = offered()
    counter(r, 1850)
    events: Any = r.twin.data("bookings", "LD09001")["events"]
    assert {k: events[-1][k] for k in ("call_id", "mc", "rate")} == {
        "call_id": RUN,
        "mc": "138328",
        "rate": 1850,
    }


def test_close_records_the_end_once_and_a_repeat_changes_nothing() -> None:
    r = offered()
    counter(r, 1850)
    assert r.post("/calls/close", summary="Agreed LD09001 at 1850.")["status"] == "closed"
    before = r.twin.tables["calls"][RUN]
    r.clock.now = r.clock.now.replace(hour=13)
    assert r.post("/calls/close", summary="other")["status"] == "closed"
    assert r.twin.tables["calls"][RUN] == before  # same version, events and activity time
    row = r.row()
    assert row["summary"] == "Agreed LD09001 at 1850."
    assert row["agreement"]["rate"] == 1850  # closing never touches the reservation


def test_close_works_without_a_summary_on_any_call() -> None:
    r = rig()
    assert r.post("/calls/close")["status"] == "closed"
    assert r.row()["closed_at"] is not None and r.row()["summary"] is None


def test_a_second_accept_on_the_same_load_waits_for_the_first() -> None:
    r = offered()
    meanwhile(r, accepting=CLAIM)  # another request claimed this load during the read
    assert counter(r, 1800)["status"] == "busy"
    assert r.row()["accepting"] == CLAIM
