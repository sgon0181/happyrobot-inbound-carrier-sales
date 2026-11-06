"""Commercial examples and boundary properties for reciprocal-v2, without network calls."""

import pytest

from service.core.negotiation import Action, concession, respond
from service.core.pricing import MAX_ROUNDS, Terms


def terms_for(opening: int, cap: int) -> Terms:
    return Terms(
        load_id="fixture",
        policy_version="pricing-v1",
        opening=opening,
        targets=(opening, opening, cap),
        cap=cap,
    )


@pytest.mark.parametrize(
    ("opening", "cap", "asks", "rates"),
    [
        (975, 1150, [1050, 1025], [1000, 1025]),
        (1125, 1300, [1200, 1175], [1150, 1175]),
        (1900, 2200, [2200, 2100, 2050], [2000, 2025, 2050]),
        (1900, 2200, [2050, 2000, 1975], [1950, 1975, 1975]),
    ],
)
def test_small_gap_deals_close(opening: int, cap: int, asks: list[int], rates: list[int]) -> None:
    terms = terms_for(opening, cap)
    offer, rounds, best = opening, 0, None
    for index, ask in enumerate(asks):
        step = respond(terms, rounds, offer, ask, best)
        assert step.rate == rates[index]
        assert step.action is (Action.ACCEPT if index == len(asks) - 1 else Action.COUNTER)
        offer, rounds, best = step.rate, step.rounds_used, min(best or ask, ask)


@pytest.mark.parametrize(
    ("offer", "ask", "best", "expected"),
    [
        (1000, 1250, None, 1075),  # inclusive reach boundary
        (1100, 1251, 1300, 1100),  # reach never grows with standing offer
        (1000, 1100, 1124, 1000),  # $24 improvement holds
        (1000, 1100, 1125, 1025),  # $25 improvement moves
        (1290, 1400, None, 1290),  # distant ask cannot use the small-room exception
    ],
)
def test_reach_and_reciprocity_boundaries(
    offer: int, ask: int, best: int | None, expected: int
) -> None:
    assert concession(terms_for(1000, 1300), offer, ask, best) == expected


def test_less_than_25_room_can_only_reach_the_cap() -> None:
    terms = terms_for(1000, 1020)
    assert respond(terms, 0, 1000, 1100).rate == 1020
    assert respond(terms, 0, 1000, 1020).action is Action.ACCEPT
    assert respond(terms, 3, 1000, 1020).action is Action.FAILED


def test_minimum_step_never_overpays_the_carrier() -> None:
    terms = terms_for(975, 1150)
    for ask in range(950, 1001):
        step = respond(terms, 0, 975, ask)
        assert step.action is Action.ACCEPT and step.rate == ask


def test_grid_caps_movement_reciprocity_and_round_budget() -> None:
    for opening in range(500, 6001, 25):
        for room in (0, 1, 24, 25, 100, 300, 1000):
            terms = terms_for(opening, opening + room)
            for offer in {opening, opening + room // 2, terms.cap}:
                for ask in {
                    offer + 1,
                    offer + 24,
                    offer + 25,
                    offer + 75,
                    opening * 5 // 4,
                    opening * 5 // 4 + 1,
                }:
                    if ask <= offer:
                        continue
                    for best in (None, ask + 25, ask + 24, ask, ask - 1):
                        target = concession(terms, offer, ask, best)
                        assert offer <= target <= terms.cap
                        eligible = ask * 4 <= opening * 5 and (best is None or best - ask >= 25)
                        if not eligible:
                            assert target == offer
                        elif terms.cap - offer >= 25:
                            assert target - offer >= 25
                        else:
                            assert target == terms.cap
                        check_rounds(terms, offer, ask, best, target)


def check_rounds(terms: Terms, offer: int, ask: int, best: int | None, target: int) -> None:
    for rounds in (0, 2, MAX_ROUNDS):
        step = respond(terms, rounds, offer, ask, best)
        assert step.rounds_used <= MAX_ROUNDS
        if rounds == MAX_ROUNDS:
            assert step.action is Action.FAILED and step.rate is None
        elif step.action is Action.ACCEPT:
            assert step.rate == ask <= terms.cap
        else:
            assert step.rate == target >= offer
