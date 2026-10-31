"""Negotiation rounds (architecture 6.5). Rounds are counted per call, across loads (INV-4)."""

from dataclasses import dataclass
from enum import Enum

from service.core.money import parse_ask

MAX_ROUNDS = 3


class Action(Enum):
    ACCEPT = "accept"
    COUNTER = "counter"
    FINAL_OFFER = "final_offer"
    FAILED = "failed"
    ASK_AGAIN = "ask_again"


@dataclass(frozen=True)
class Step:
    action: Action
    rate: int | None
    rounds_used: int


def respond(terms, rounds_used, current_offer, ask):
    """Answer a carrier's ask. An ask at or below our current offer is an acceptance."""
    amount = parse_ask(ask)
    if amount is None:
        return Step(Action.ASK_AGAIN, None, rounds_used)
    if amount <= current_offer:
        return Step(Action.ACCEPT, amount, rounds_used)
    if rounds_used >= MAX_ROUNDS:
        return Step(Action.FAILED, None, rounds_used)

    target = terms.targets[rounds_used]
    round_number = rounds_used + 1
    if amount <= target:
        return Step(Action.ACCEPT, amount, round_number)
    action = Action.FINAL_OFFER if round_number == MAX_ROUNDS else Action.COUNTER
    return Step(action, target, round_number)
