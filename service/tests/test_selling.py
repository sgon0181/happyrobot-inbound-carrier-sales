"""Load search over HTTP: verified calls only, open loads only, our offer and never the ceiling."""

import json
from typing import Any

from service.tests.fake_tms import make_load
from service.tests.rig import RUN, Rig, rig

LANE = {"equipment": "dry van", "origin_state": "tx", "dest_state": "GA"}
PUBLIC = {
    "load_id",
    "origin",
    "destination",
    "pickup_datetime",
    "delivery_datetime",
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
    assert row["events"][-1]["offers"] == row["offers"]


def test_the_ceiling_reaches_neither_the_agent_nor_the_row() -> None:
    r = selling(make_load(MAX_BUY="2345"))
    reply = search(r)
    assert reply["status"] == "found"
    for text in (json.dumps(reply), json.dumps(r.row())):
        assert "2345" not in text
        assert "max_rate" not in text
        assert "loadboard_rate" not in text


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
