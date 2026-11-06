"""Adversarial negotiation journeys, all offline, using the actual CAS adapter."""

import asyncio
from copy import deepcopy
from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest

from service import negotiation_memory as memory
from service.adapters.twin import TwinUnavailable
from service.core.negotiation import Action, Step, respond
from service.core.pricing import Terms
from service.tests.fake_tms import make_load
from service.tests.rig import RUN, START, Rig
from service.tests.test_selling import LANE, counter, offered, search

TERMS = Terms(
    load_id="LD01125", policy_version="fixture", opening=4600, targets=(4725, 4850, 5000), cap=5000
)


def ladder(asks: list[int]) -> list[Step]:
    offer, rounds, best = 4600, 0, None
    results = []
    for ask in asks:
        step = respond(TERMS, rounds, offer, ask, best)
        results.append(step)
        rounds = step.rounds_used
        best = min(best or ask, ask)
        offer = step.rate or offer
    return results


@pytest.mark.parametrize(
    ("asks", "offers"),
    [
        ([15000, 14000, 13000], [4600, 4600, 4600]),
        ([6000, 5500, 5200], [4600, 4600, 4600]),
        ([5000, 4900, 4800], [4675, 4725, 4775]),
        ([5000, 5100, 5200], [4675, 4675, 4675]),
        ([5000, 4999, 4998], [4675, 4675, 4675]),
        ([15000, 5000, 4900], [4600, 4675, 4725]),
    ],
)
def test_business_scenarios(asks: list[int], offers: list[int]) -> None:
    steps = ladder(asks)
    assert [step.rate for step in steps] == offers
    assert steps[-1].action is Action.FINAL_OFFER


def reconnect(r: Rig, mc: str = "138328") -> str:
    run = str(uuid4())
    # Independently verified call fixture, not a production verification shortcut.
    data = deepcopy(r.row())
    data.update(
        mc=mc,
        offers={},
        rounds=0,
        outcome=None,
        agreement=None,
        accepting=None,
        counter_replies={},
        last_counter=None,
        events=[],
        closed_at=None,
        ended_at=None,
    )
    r.twin.tables["calls"][run] = (1, data)
    return run


def ask(r: Rig, run: str, amount: int) -> Any:
    return r.post("/negotiate", run_id=run, load_id="LD09001", rate=str(amount))


def test_redial_resumes_quote_and_budget_but_requires_own_verification() -> None:
    r = offered()
    first = counter(r, 2050)
    run = reconnect(r)
    found = r.post("/loads/search", run_id=run, **LANE)
    assert found["loads"][0]["offer"] == first["offer"]
    assert ask(r, run, 2050)["offer"] == first["offer"]
    assert ask(r, run, 2050)["round"] == 1
    second = ask(r, run, 2000)
    assert second["round"] == 2
    assert second["offer"] == first["offer"] + 25
    third = ask(r, RUN, 1975)
    assert third["status"] == "final_offer" and third["round"] == 3
    another = reconnect(r)
    r.post("/loads/search", run_id=another, **LANE)
    assert ask(r, another, 1960)["status"] == "negotiation_failed"
    assert ask(r, run, third["offer"])["status"] == "agreed"
    fresh = str(uuid4())
    assert ask(r, fresh, third["offer"])["status"] == "not_verified"


def test_long_wait_does_not_reset_budget_and_other_carrier_is_separate() -> None:
    r = offered()
    for amount in [9000, 8000, 7000]:
        counter(r, amount)
    r.clock.now += timedelta(days=1)
    run = reconnect(r)
    r.post("/loads/search", run_id=run, **LANE)
    assert ask(r, run, 6000)["status"] == "negotiation_failed"
    other = reconnect(r, "1515")
    r.post("/loads/search", run_id=other, **LANE)
    assert ask(r, other, 6000)["round"] == 1


def test_no_memory_created_before_verification_or_valid_search() -> None:
    r = offered()
    assert ask(r, str(uuid4()), 2000)["status"] == "not_verified"
    run = reconnect(r)
    assert ask(r, run, 2000)["status"] == "search_required"
    assert not r.twin.tables["negotiations"]


def test_service_restart_and_simultaneous_calls_share_one_cas_budget() -> None:
    r = offered()
    load = asyncio.run(r.board.get("LD09001"))
    assert load is not None
    terms = Terms(
        load_id="LD09001",
        policy_version="fixture",
        opening=1900,
        targets=(2000, 2075, 2200),
        cap=2200,
    )

    async def scenario() -> tuple[Step, Step, Step]:
        # Separate clients stand for separate service instances, with shared durable storage.
        async def call(amount: int) -> Step:
            return await memory.decide(
                r.twin.twin(),
                "138328",
                str(uuid4()),
                load,
                terms,
                r.row(),
                str(amount),
                False,
                START,
            )

        return await asyncio.gather(call(9000), call(8000), call(7000))

    steps = asyncio.run(scenario())
    assert sorted(step.rounds_used for step in steps) == [1, 2, 3]
    assert all(step.rate == 1900 for step in steps)
    events: Any = r.twin.data("negotiations", "138328:LD09001")["events"]
    assert len(events) == 3
    assert counter(r, 6000)["status"] == "negotiation_failed"


def test_memory_write_survives_lost_call_write_without_another_concession() -> None:
    r = offered()
    load = asyncio.run(r.board.get("LD09001"))
    assert load is not None
    terms = Terms(
        load_id="LD09001",
        policy_version="fixture",
        opening=1900,
        targets=(2000, 2075, 2200),
        cap=2200,
    )
    first = asyncio.run(
        memory.decide(r.twin.twin(), "138328", RUN, load, terms, r.row(), "2050", False, START)
    )
    # Crash here: call row never saw the first result. Reconstruct a client and retry.
    retry = asyncio.run(
        memory.decide(r.twin.twin(), "138328", RUN, load, terms, r.row(), "2050", False, START)
    )
    assert retry == first
    assert retry.rounds_used == 1 and retry.rate == 1925
    assert r.row()["rounds"] == 0


def test_memory_contention_fails_closed() -> None:
    r = offered()
    counter(r, 9000)
    r.twin.interfere = True
    with pytest.raises(TwinUnavailable):
        asyncio.run(r.twin.twin().change("negotiations", "138328:LD09001", lambda d: (d, None)))
    assert not r.twin.tables["bookings"]


def test_memory_never_exposes_private_prices_in_agent_payload() -> None:
    r = offered()
    for amount in [9000, 8000, 7000]:
        reply = counter(r, amount)
        assert set(reply) == {"status", "offer", "round", "http"}
    assert set(search(r)) == {"status", "loads", "http"}


def test_search_retraction_is_durable_across_reconnect_and_ceiling_recovery() -> None:
    r = offered(make_load(RATE="2000", MAX_BUY="2300"))
    counter(r, 2025)
    r.board.records = [make_load(RATE="1500", MAX_BUY="1800")]
    lower = search(r)["loads"][0]["offer"]
    r.board.records = [make_load(RATE="2200", MAX_BUY="2300")]
    assert search(r)["loads"][0]["offer"] == lower
    run = reconnect(r)
    assert r.post("/loads/search", run_id=run, **LANE)["loads"][0]["offer"] == lower


def test_material_shipment_change_allows_new_cross_call_budget() -> None:
    r = offered()
    for amount in [9000, 8000, 7000]:
        counter(r, amount)
    r.board.records = [make_load(WEIGHT="30000")]
    run = reconnect(r)
    r.post("/loads/search", run_id=run, **LANE)
    assert ask(r, run, 9000)["round"] == 1


def test_no_concession_exceeds_half_the_carrier_movement() -> None:
    for best in range(4800, 5400, 25):
        for ask_value in range(4700, best, 7):
            step = respond(TERMS, 1, 4675, ask_value, best)
            if step.rate is not None:
                assert step.rate - 4675 <= (best - ask_value) // 2
                assert step.rate <= 4750


def test_other_calls_old_quote_cannot_undo_shared_retraction() -> None:
    r = offered(make_load(RATE="2000", MAX_BUY="2300"))
    counter(r, 2025)
    run = reconnect(r)
    r.post("/loads/search", run_id=run, **LANE)
    r.board.records = [make_load(RATE="1500", MAX_BUY="1800")]
    lower = search(r)["loads"][0]["offer"]
    r.board.records = [make_load(RATE="2200", MAX_BUY="2300")]
    assert ask(r, run, 9000)["offer"] == lower
    assert ask(r, run, lower)["rate"] == lower


def test_lost_acceptance_response_replays_the_same_authorized_agreement() -> None:
    r = offered()
    load = asyncio.run(r.board.get("LD09001"))
    assert load is not None
    terms = Terms(
        load_id="LD09001",
        policy_version="fixture",
        opening=1900,
        targets=(2000, 2075, 2200),
        cap=2200,
    )
    first = asyncio.run(
        memory.decide(r.twin.twin(), "138328", RUN, load, terms, r.row(), "1920", False, START)
    )
    retry = asyncio.run(
        memory.decide(r.twin.twin(), "138328", RUN, load, terms, r.row(), "1920", False, START)
    )
    assert first == retry
    assert retry.action is Action.ACCEPT and retry.rate == 1920
