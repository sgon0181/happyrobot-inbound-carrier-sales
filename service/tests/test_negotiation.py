"""Negotiation: at most three rounds, and no rate above the cap is ever offered or accepted."""

import random

import pytest

from service.core.negotiation import Action, Step, respond
from service.core.pricing import MAX_ROUNDS, Terms, price_load
from service.tests.test_pricing import POLICY, SECRET

TERMS = Terms(
    load_id="LD1", policy_version="pricing-v1", opening=2000, targets=(2100, 2200, 2300), cap=2300
)


@pytest.mark.parametrize(
    ("rounds_used", "current_offer", "ask", "expected"),
    [
        (0, 2000, 2000, Step(Action.ACCEPT, 2000, 0)),  # at our offer: agreed, no round used
        (0, 2000, 1800, Step(Action.ACCEPT, 1800, 0)),  # below it: agreed at their number
        (0, 2000, 2050, Step(Action.ACCEPT, 2050, 1)),  # under round 1's target
        (0, 2000, 5000, Step(Action.COUNTER, 2100, 1)),
        (1, 2100, 5000, Step(Action.COUNTER, 2200, 2)),
        (2, 2200, 5000, Step(Action.FINAL_OFFER, 2300, 3)),
        (3, 2300, 2300, Step(Action.ACCEPT, 2300, 3)),  # the final offer accepted
        (3, 2300, 2301, Step(Action.FAILED, None, 3)),  # anything else ends it
        (1, 2100, "2150.50", Step(Action.ASK_AGAIN, None, 1)),  # never rounded, no round used
    ],
)
def test_answers(rounds_used: int, current_offer: int, ask: int | str, expected: Step) -> None:
    assert respond(TERMS, rounds_used, current_offer, ask) == expected


def test_rounds_carry_across_loads_on_a_call() -> None:
    other = Terms(
        load_id="LD2",
        policy_version="pricing-v1",
        opening=1000,
        targets=(1100, 1200, 1300),
        cap=1300,
    )
    assert respond(other, MAX_ROUNDS, 1000, 1500).action is Action.FAILED
    assert respond(other, 2, 1000, 5000).rate == 1300  # straight to the final offer


@pytest.mark.parametrize(
    ("rounds_used", "current_offer"),
    [(4, 2300), (-1, 2000), (0, 2400), (0, 0)],  # too many rounds, or an offer off the terms
)
def test_an_impossible_state_is_refused(rounds_used: int, current_offer: int) -> None:
    with pytest.raises(ValueError):
        respond(TERMS, rounds_used, current_offer, 2000)


def test_terms_without_a_target_per_round_are_refused() -> None:
    two_rounds = Terms(
        load_id="LD1", policy_version="x", opening=2000, targets=(2200, 2300), cap=2300
    )
    with pytest.raises(ValueError):
        respond(two_rounds, 0, 2000, 2100)


def test_no_rate_above_the_cap_is_ever_offered_or_accepted() -> None:
    rng = random.Random(11)
    for index in range(5000):
        terms = price_load(
            f"LD{index}", rng.randint(500, 9000), rng.randint(600, 11_000), POLICY, SECRET
        )
        if terms is None:
            continue
        rounds, offer = 0, terms.opening
        for _ in range(5):
            step = respond(terms, rounds, offer, rng.randint(1, 20_000))
            assert step.rounds_used <= MAX_ROUNDS
            if step.rate is not None:
                assert step.rate <= terms.cap
            if step.action in (Action.ACCEPT, Action.FAILED):
                break
            offer = step.rate or offer
            rounds = step.rounds_used
