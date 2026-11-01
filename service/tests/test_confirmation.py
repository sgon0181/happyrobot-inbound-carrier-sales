"""SIMULATED dialogue evidence. No external API or live booking."""

import unittest
from service.adapters.confirmation import consent_evidence as check


def consent_evidence(messages, rate, anchor):
    return check(messages, rate, anchor, "LD1")


class ConfirmationTests(unittest.TestCase):
    def messages(self, answer, question="May I book load LD1 at $1,075 total?", interrupted=False):
        return [
            {"id": "u1", "role": "user", "content": "1075 please"},
            {"id": "a1", "role": "assistant", "content": question, "is_interrupted": interrupted},
            {"id": "u2", "role": "user", "content": answer},
        ]

    def test_explicit_yes_after_exact_total_passes(self):
        self.assertTrue(consent_evidence(self.messages("Yes please"), 1075, "u1")["approved"])

    def test_clarification_hesitation_and_negation_fail(self):
        for answer in [
            "I just want the initial one plus 25 dollars more",
            "yes but wait",
            "no",
            "I think so",
            "1075",
            "yes $1200",
            "yes 1200",
            "yes?",
        ]:
            self.assertFalse(consent_evidence(self.messages(answer), 1075, "u1")["approved"])

    def test_stale_answer_wrong_total_and_interrupted_question_fail(self):
        self.assertFalse(consent_evidence(self.messages("Yes"), 1075, "u2")["approved"])
        self.assertFalse(consent_evidence(self.messages("Yes"), 1075, None)["approved"])
        self.assertFalse(consent_evidence(self.messages("Yes"), 1075, "missing-id")["approved"])
        self.assertFalse(
            consent_evidence(self.messages("Yes", "May I book it at $1050?"), 1075, "u1")[
                "approved"
            ]
        )
        self.assertFalse(
            consent_evidence(self.messages("Yes", interrupted=True), 1075, "u1")["approved"]
        )

    def test_rate_agreement_question_is_not_booking_consent(self):
        self.assertFalse(
            consent_evidence(self.messages("Yes", "Is $1075 the rate you want?"), 1075, "u1")[
                "approved"
            ]
        )

    def test_fragmented_clarification_cannot_be_treated_as_yes(self):
        messages = self.messages("Yes")
        messages.append({"id": "u3", "role": "user", "content": "but hold on"})
        self.assertFalse(consent_evidence(messages, 1075, "u1")["approved"])

    def test_negated_alternative_and_different_load_questions_fail(self):
        for question in [
            "May I not book load LD1 at $1075 total?",
            "May I book load LD10 at $1075 total?",
            "May I book load LD1 at $10.75 total?",
            "May I book load LD1 at $1075 or $1200 total?",
        ]:
            self.assertFalse(
                consent_evidence(self.messages("Yes", question), 1075, "u1")["approved"]
            )

    def test_interrupted_affirmation_fails(self):
        messages = self.messages("Yes")
        messages[-1]["is_interrupted"] = True
        self.assertFalse(consent_evidence(messages, 1075, "u1")["approved"])
