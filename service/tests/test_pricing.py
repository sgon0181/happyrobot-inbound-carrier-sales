"""Pricing and negotiation rules from architecture section 6.5."""

import random
import unittest

from service.core.money import parse_ask, parse_tms_amount
from service.core.negotiation import MAX_ROUNDS, Action, respond
from service.core.pricing import PricingPolicy, Terms, price_load

POLICY = PricingPolicy.load()
SECRET = b"test-pricing-secret"


class MoneyTests(unittest.TestCase):
    def test_tms_amounts(self):
        self.assertEqual(parse_tms_amount("2709"), 2709)
        self.assertEqual(parse_tms_amount("0002150"), 2150)
        for text in (None, "", "0", "-1", "12.5", "abc", "1e3", " 12"):
            with self.subTest(text=text):
                self.assertIsNone(parse_tms_amount(text))

    def test_asks_are_never_rounded(self):
        for value, expected in ((1500, 1500), ("1500", 1500), ("1500.00", 1500), (1500.0, 1500)):
            with self.subTest(value=value):
                self.assertEqual(parse_ask(value), expected)
        for value in (1500.5, "1500.50", "0", 0, -5, "abc", "1e3", True, None, ""):
            with self.subTest(value=value):
                self.assertIsNone(parse_ask(value))


class PricingTests(unittest.TestCase):
    def test_policy_file_loads(self):
        self.assertEqual(POLICY.version, "pricing-v1")
        self.assertEqual(POLICY.rounding_step, 25)

    def test_same_load_and_policy_give_the_same_numbers(self):
        self.assertEqual(price_load("LD1", 2000, 2300, POLICY, SECRET),
                         price_load("LD1", 2000, 2300, POLICY, SECRET))

    def test_without_the_secret_the_policy_does_not_reveal_the_gap(self):
        loads = [f"LD{i}" for i in range(200)]
        ours = [price_load(load, 5000, 6000, POLICY, SECRET).cap for load in loads]
        theirs = [price_load(load, 5000, 6000, POLICY, b"other").cap for load in loads]
        self.assertNotEqual(ours, theirs)

    def test_the_cap_is_not_a_fixed_percentage_of_the_ceiling(self):
        caps = {price_load(f"LD{i}", 5000, 6000, POLICY, SECRET).cap for i in range(200)}
        self.assertGreater(len(caps), 3)

    def test_the_rules_hold_across_many_loads(self):
        rng = random.Random(7)
        priced = 0
        for index in range(20000):
            posted = rng.randint(100, 12000)
            ceiling = int(posted * rng.uniform(0.7, 1.3))
            terms = price_load(f"LD{index}", posted, ceiling, POLICY, SECRET)
            if terms is None:
                continue
            priced += 1
            numbers = (terms.opening, *terms.targets)
            self.assertTrue(all(number % 25 == 0 and number > 0 for number in numbers))
            self.assertEqual(terms.targets[-1], terms.cap)
            self.assertEqual(list(terms.targets), sorted(terms.targets))
            self.assertLess(terms.opening, terms.cap)
            self.assertLess(terms.cap, ceiling)
            self.assertGreaterEqual(terms.cap, int(ceiling * 0.94) - 25)
        self.assertGreater(priced, 19000)

    def test_opens_from_the_posted_rate_when_there_is_room(self):
        terms = price_load("LD1", 2000, 2400, POLICY, SECRET)
        self.assertEqual(terms.opening, 1900)

    def test_uses_the_spread_when_the_posted_rate_is_above_the_cap(self):
        terms = price_load("LD1", 2150, 1950, POLICY, SECRET)
        self.assertLess(terms.opening, terms.cap)
        self.assertLess(terms.cap, 1950)

    def test_a_missing_posted_rate_uses_the_spread(self):
        self.assertIsNotNone(price_load("LD1", None, 2300, POLICY, SECRET))

    def test_unusable_loads_go_to_pricing_review(self):
        for ceiling in (None, 0, -5, 10, 25):
            with self.subTest(ceiling=ceiling):
                self.assertIsNone(price_load("LD1", 2000, ceiling, POLICY, SECRET))

    def test_a_secret_is_required(self):
        with self.assertRaises(ValueError):
            price_load("LD1", 2000, 2300, POLICY, b"")


class NegotiationTests(unittest.TestCase):
    terms = Terms("LD1", "pricing-v1", 2000, (2100, 2200, 2300), 2300)

    def test_an_ask_at_or_below_the_offer_is_accepted_without_a_round(self):
        for ask in (2000, 1800):
            with self.subTest(ask=ask):
                step = respond(self.terms, 0, 2000, ask)
                self.assertEqual((step.action, step.rate, step.rounds_used),
                                 (Action.ACCEPT, ask, 0))

    def test_an_ask_at_or_below_the_target_is_accepted_at_the_carriers_number(self):
        step = respond(self.terms, 0, 2000, 2050)
        self.assertEqual((step.action, step.rate, step.rounds_used), (Action.ACCEPT, 2050, 1))

    def test_rounds_climb_to_a_final_offer_at_the_cap(self):
        first = respond(self.terms, 0, 2000, 5000)
        second = respond(self.terms, first.rounds_used, first.rate, 5000)
        third = respond(self.terms, second.rounds_used, second.rate, 5000)
        self.assertEqual(
            [(s.action, s.rate) for s in (first, second, third)],
            [(Action.COUNTER, 2100), (Action.COUNTER, 2200), (Action.FINAL_OFFER, 2300)],
        )

    def test_after_the_final_offer_only_acceptance_succeeds(self):
        accepted = respond(self.terms, MAX_ROUNDS, 2300, 2300)
        self.assertEqual((accepted.action, accepted.rate), (Action.ACCEPT, 2300))
        self.assertIs(respond(self.terms, MAX_ROUNDS, 2300, 2301).action, Action.FAILED)

    def test_rounds_carry_across_loads_on_a_call(self):
        other_load = Terms("LD2", "pricing-v1", 1000, (1100, 1200, 1300), 1300)
        self.assertIs(respond(other_load, MAX_ROUNDS, 1000, 1500).action, Action.FAILED)
        self.assertEqual(respond(other_load, 2, 1000, 5000).rate, 1300)

    def test_a_fractional_ask_is_not_rounded_or_counted(self):
        step = respond(self.terms, 1, 2100, "2150.50")
        self.assertEqual((step.action, step.rate, step.rounds_used), (Action.ASK_AGAIN, None, 1))

    def test_no_accepted_or_offered_rate_ever_exceeds_the_cap(self):
        rng = random.Random(11)
        for index in range(5000):
            terms = price_load(f"LD{index}", rng.randint(500, 9000), rng.randint(600, 11000),
                               POLICY, SECRET)
            if terms is None:
                continue
            rounds, offer = 0, terms.opening
            for _ in range(5):
                step = respond(terms, rounds, offer, rng.randint(1, 20000))
                if step.rate is not None:
                    self.assertLessEqual(step.rate, terms.cap)
                    offer = step.rate
                self.assertLessEqual(step.rounds_used, MAX_ROUNDS)
                rounds = step.rounds_used
                if step.action in (Action.ACCEPT, Action.FAILED):
                    break


if __name__ == "__main__":
    unittest.main()
