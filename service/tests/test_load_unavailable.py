"""Unavailable loads get a truthful continuation, not an invented booking or reason."""

import pytest

from service.tests.fake_tms import make_load
from service.tests.rig import RUN, rig


@pytest.mark.parametrize(
    "details",
    [
        {"STATUS": "PENDING"},
        {"PICKUP_DT": "20000101000000"},
        {"MAX_BUY": "0"},
    ],
)
def test_unavailability_has_one_truthful_next_step_without_extra_reads(
    details: dict[str, str],
) -> None:
    r = rig(live_booking=False)
    r.board.records = [make_load(), make_load("LD09002")]
    r.verified()
    r.post("/loads/search", equipment="dry van", origin_state="TX", dest_state="GA")
    queries = len(r.board.queries)
    r.board.details["LD09001"] = make_load(**details)
    reply = r.post("/negotiate", load_id="LD09001", rate="1900")
    assert reply["status"] == "load_gone"
    assert reply["message"] == "That load is no longer available. No reservation was made."
    assert reply["next_action"] == "ask_to_search_again"
    assert reply["search"] == {"equipment": "DRY_VAN", "origin_state": "TX", "dest_state": "GA"}
    assert "loads" not in reply  # never pitch old alternatives as freshly available
    assert len(r.board.queries) == queries and r.row()["rounds"] == 0
    assert r.row()["events"][-1]["message"] == reply["message"]
    assert r.board.sends == []


def test_verification_lost_during_the_read_does_not_continue_selling() -> None:
    r = rig(live_booking=False)
    r.board.records = [make_load()]
    r.verified()
    r.post("/loads/search", equipment="dry van")
    r.board.records = []

    def lose_verification(load_id: str) -> None:
        version, data = r.twin.tables["calls"][RUN]
        r.twin.tables["calls"][RUN] = (
            version + 1,
            {**data, "verified_at": None},
        )

    r.board.reading = lose_verification
    assert r.post("/negotiate", load_id="LD09001", rate="1900")["status"] == "not_verified"
    assert r.row()["rounds"] == 0 and r.board.sends == []
