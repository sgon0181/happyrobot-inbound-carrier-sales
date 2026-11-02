"""Pricing: the cap stays below the ceiling, and the same load always gets the same numbers."""

import json
import random
from pathlib import Path

import pytest

from service.core.pricing import PricingPolicy, price_load

POLICY_TEXT = (Path(__file__).parents[1] / "policy" / "pricing-v1.json").read_text()
POLICY = PricingPolicy.from_json(POLICY_TEXT)
SECRET = b"test-pricing-secret"


def test_the_policy_file_loads() -> None:
    assert POLICY.version == "pricing-v1"
    assert POLICY.rounding_step == 25


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("rounding_step", 0),
        ("ceiling_gap_bps", [600, 200]),  # band upside down
        ("opening_spread_bps", [800]),  # not a band
        ("round_target_bps", [3500, 6500, 9000]),  # never reaches the cap
        ("round_target_bps", [6500, 3500, 10000]),  # out of order
        ("round_target_bps", [3500, 6500, 12000]),  # past the cap
        ("round_target_bps", [10000]),  # one target, but there are three rounds
        ("round_target_bps", [2500, 5000, 7500, 10000]),  # four targets
        ("rounding_step", 25.5),  # would produce fractional offers
        ("rounding_step", True),
        ("opening_discount_bps", 500.0),
        ("ceiling_gap_bps", [200, "600"]),
    ],
)
def test_a_broken_policy_is_refused(field: str, value: object) -> None:
    data = json.loads(POLICY_TEXT) | {field: value}
    with pytest.raises(ValueError, match="Invalid pricing policy"):
        PricingPolicy.from_json(json.dumps(data))


def test_opens_five_percent_below_the_posted_rate_when_there_is_room() -> None:
    terms = price_load("LD1", 2000, 2400, POLICY, SECRET)
    assert terms is not None
    assert terms.opening == 1900


def test_opens_below_the_cap_when_the_posted_rate_is_too_high() -> None:
    terms = price_load("LD1", 2150, 1950, POLICY, SECRET)  # the handbook's sample load
    assert terms is not None
    assert terms.opening < terms.cap < 1950


def test_a_missing_posted_rate_still_gets_an_offer() -> None:
    assert price_load("LD1", None, 2300, POLICY, SECRET) is not None


@pytest.mark.parametrize("ceiling", [None, 0, -5, 10, 25])
def test_a_load_without_a_usable_ceiling_goes_to_pricing_review(ceiling: int | None) -> None:
    assert price_load("LD1", 2000, ceiling, POLICY, SECRET) is None


def test_a_secret_is_required() -> None:
    with pytest.raises(ValueError, match="secret"):
        price_load("LD1", 2000, 2300, POLICY, b"")


def test_the_same_load_always_gets_the_same_numbers() -> None:
    assert price_load("LD1", 2000, 2300, POLICY, SECRET) == price_load(
        "LD1", 2000, 2300, POLICY, SECRET
    )


def test_the_gap_depends_on_the_secret_and_varies_by_load() -> None:
    loads = [f"LD{i}" for i in range(200)]
    ours = [price_load(load, 5000, 6000, POLICY, SECRET) for load in loads]
    theirs = [price_load(load, 5000, 6000, POLICY, b"other") for load in loads]
    caps = [terms.cap for terms in ours if terms]
    assert ours != theirs
    assert len(set(caps)) > 3  # not a fixed percentage of the ceiling


def test_the_rules_hold_across_many_loads() -> None:
    rng = random.Random(7)
    priced = 0
    for index in range(20_000):
        posted = rng.randint(100, 12_000)
        ceiling = int(posted * rng.uniform(0.7, 1.3))
        terms = price_load(f"LD{index}", posted, ceiling, POLICY, SECRET)
        if terms is None:
            continue
        priced += 1
        numbers = (terms.opening, *terms.targets)
        assert all(number > 0 and number % 25 == 0 for number in numbers)
        assert terms.opening < terms.cap < ceiling
        assert terms.opening <= terms.targets[0]
        assert list(terms.targets) == sorted(terms.targets)
        assert terms.targets[-1] == terms.cap
        assert terms.cap >= int(ceiling * 0.94) - 25  # the gap is at most 6%
    assert priced > 19_000
