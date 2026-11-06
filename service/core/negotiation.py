"""Answering a carrier's counter-offer (architecture section 9).

Concessions require a reachable ask and reciprocal movement. Three rounds are a
budget, not a promise to reach the cap. The caller/load memory supplies the best
prior ask; amounts and limits remain deterministic and outside the voice model.
"""

from dataclasses import dataclass
from enum import Enum

from service.core.money import parse_ask
from service.core.pricing import MAX_ROUNDS, Terms

REACH_BPS = 11000  # asks within 10% of the standing offer can be negotiated
CONCESSION_BPS = 200  # at most 2% of opening per new round
ROUNDING = 25


class Action(Enum):
    ACCEPT = "accept"
    COUNTER = "counter"
    FINAL_OFFER = "final_offer"
    FAILED = "failed"
    ASK_AGAIN = "ask_again"  # the ask was not a whole amount, so no round is used


@dataclass(frozen=True)
class Step:
    action: Action
    rate: int | None  # the agreed rate, or our new offer
    rounds_used: int


def respond(
    terms: Terms,
    rounds_used: int,
    current_offer: int,
    ask: int | float | str | None,
    best_ask: int | None = None,
) -> Step:
    """Answer one ask. current_offer is the last number we said for this load."""
    _check(terms, rounds_used, current_offer)
    amount = parse_ask(ask)
    if amount is None:
        return Step(Action.ASK_AGAIN, None, rounds_used)
    if amount <= current_offer:
        return Step(Action.ACCEPT, amount, rounds_used)
    if rounds_used == MAX_ROUNDS:
        return Step(Action.FAILED, None, rounds_used)

    target = concession(terms, current_offer, amount, best_ask)
    round_number = rounds_used + 1
    if amount <= target:
        return Step(Action.ACCEPT, amount, round_number)
    action = Action.FINAL_OFFER if round_number == MAX_ROUNDS else Action.COUNTER
    return Step(action, target, round_number)


def concession(terms: Terms, offer: int, ask: int, best_ask: int | None) -> int:
    """Never reward distance, escalation, or a token change rounded up to money."""
    if ask * 10000 > offer * REACH_BPS:
        return offer
    budget = terms.opening * CONCESSION_BPS // 10000
    if best_ask is not None:
        budget = min(budget, max(0, best_ask - ask) // 2)
    increase = budget // ROUNDING * ROUNDING
    return min(terms.cap, offer + increase)


def _check(terms: Terms, rounds_used: int, current_offer: int) -> None:
    """Refuse a state that should be impossible, rather than risk a rate above the cap (INV-1)."""
    if len(terms.targets) != MAX_ROUNDS:
        raise ValueError("Terms need one target per round.")
    if not 0 <= rounds_used <= MAX_ROUNDS:
        raise ValueError("Rounds used is out of range.")
    # A refreshed posted rate can raise the opening without invalidating a lower spoken quote.
    if not 0 < current_offer <= terms.cap:
        raise ValueError("The current offer is outside this load's terms.")
