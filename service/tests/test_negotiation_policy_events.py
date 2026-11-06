"""Version new negotiation decisions without relabeling history or resetting budgets."""

from copy import deepcopy
from typing import Any
from uuid import uuid4

from service.core.negotiation import NEGOTIATION_POLICY_VERSION
from service.tests.rig import RUN
from service.tests.test_reciprocal_memory import ask, reconnect
from service.tests.test_selling import LANE, counter, offered


def test_all_new_call_negotiation_events_are_versioned_but_payloads_are_not() -> None:
    r = offered()
    historical = deepcopy(r.row()["events"])
    replies = [counter(r, 2200), counter(r, 2200), counter(r, "unclear"), counter(r, 1900)]
    assert [reply["status"] for reply in replies] == ["counter", "counter", "ask_again", "agreed"]
    events = r.row()["events"]
    assert events[: len(historical)] == historical
    assert {event["status"] for event in events[len(historical) :]} == {
        "counter",
        "ask_again",
        "accepting",
        "agreed",
    }
    for event in events[len(historical) :]:
        assert event["negotiation_policy_version"] == NEGOTIATION_POLICY_VERSION
    assert all("negotiation_policy_version" not in reply for reply in replies)
    unverified = str(uuid4())
    assert ask(r, unverified, 2200)["status"] == "not_verified"
    refusal_events: Any = r.twin.data("calls", unverified)["events"]
    assert refusal_events[-1]["negotiation_policy_version"] == NEGOTIATION_POLICY_VERSION


def test_policy_change_preserves_untagged_memory_and_spent_rounds() -> None:
    r = offered()
    for amount in (9000, 8000):
        counter(r, amount)
    version, data = r.twin.tables["negotiations"]["138328:LD09001"]
    old_events: Any = data["events"]
    for event in old_events:
        event.pop("negotiation_policy_version")  # an actual pre-versioning row shape
    historical = deepcopy(data["events"])
    r.twin.tables["negotiations"]["138328:LD09001"] = (version, data)
    run = reconnect(r)
    r.post("/loads/search", run_id=run, **LANE)
    assert ask(r, run, 8000)["round"] == 2  # replay retains the old budget
    assert ask(r, run, 7000)["status"] == "final_offer"
    current: Any = r.twin.data("negotiations", "138328:LD09001")
    assert current["events"][:2] == historical
    assert current["events"][-1]["negotiation_policy_version"] == NEGOTIATION_POLICY_VERSION
    assert current["rounds"] == 3 and current["best_ask"] == 7000
    assert ask(r, RUN, 6000)["status"] == "negotiation_failed"
    assert r.row()["events"][-1]["negotiation_policy_version"] == NEGOTIATION_POLICY_VERSION
