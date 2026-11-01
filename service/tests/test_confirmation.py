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

    def test_neutral_acknowledgement_after_permission_keeps_original_proof(self):
        for text in ("One moment...", "Just a moment.", "Let me check.", "Let me see..."):
            messages = self.messages("Yeah, go ahead.")
            messages.append({"id": "ack", "role": "assistant", "content": text})
            proof = consent_evidence(messages, 1075, "u1")
            self.assertTrue(proof["approved"])
            self.assertEqual(proof["question_id"], "a1")
            self.assertEqual(proof["answer_id"], "u2")
            self.assertEqual(proof["ignored_acknowledgement_ids"], ["ack"])
        messages = self.messages("Yes please.")
        messages.extend(
            [
                {"id": "ack1", "role": "assistant", "content": "One"},
                {"id": "ack2", "role": "assistant", "content": "moment..."},
            ]
        )
        proof = consent_evidence(messages, 1075, "u1")
        self.assertTrue(proof["approved"])
        self.assertEqual(proof["ignored_acknowledgement_ids"], ["ack1", "ack2"])

    def test_substantive_speech_and_interrupted_acknowledgement_still_fail(self):
        for text in (
            "One moment, the total is $1200.",
            "One moment. Is that right?",
            "One moment. Let me check.",
            "One moment, please.",
            "Booking confirmed.",
            "Okay.",
        ):
            messages = self.messages("Yes please.")
            messages.append({"id": "ack", "role": "assistant", "content": text})
            self.assertFalse(consent_evidence(messages, 1075, "u1")["approved"])
        messages = self.messages("Yes please.")
        messages.append(
            {"id": "ack", "role": "assistant", "content": "One moment...", "is_interrupted": True}
        )
        self.assertFalse(consent_evidence(messages, 1075, "u1")["approved"])

    def test_neutral_acknowledgement_cannot_rescue_invalid_permission(self):
        for answer in ("Yes but wait", "Is that the total?", "No", "1075", "Maybe"):
            messages = self.messages(answer)
            messages.append({"id": "ack", "role": "assistant", "content": "One moment..."})
            self.assertFalse(consent_evidence(messages, 1075, "u1")["approved"])
        messages = self.messages("Yes please.", interrupted=True)
        messages.append({"id": "ack", "role": "assistant", "content": "One moment..."})
        self.assertFalse(consent_evidence(messages, 1075, "u1")["approved"])
        self.assertFalse(consent_evidence(messages, 1075, "u2")["approved"])
        messages = self.messages("Yes please.")
        messages.append({"id": "ack", "role": "assistant", "content": "One moment..."})
        self.assertFalse(consent_evidence(messages, 1075, "u2")["approved"])
        messages.append({"id": "withdraw", "role": "user", "content": "Wait, do not book it."})
        self.assertFalse(consent_evidence(messages, 1075, "u1")["approved"])

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

    def test_required_natural_approval_answers(self):
        approvals = [
            "Yes.",
            "Yes please.",
            "Go ahead.",
            "Book it.",
            "Yes, book it.",
            "Yeah.",
            "Yeah, go ahead.",
            "Yep.",
            "Sure.",
            "Correct.",
            "Okay.",
            "Okay, perfect.",
            "Sounds good.",
            "That works.",
            "Yes, that's fine.",
            "Yes, please do.",
            "Yes sir.",
            "Yes, thanks.",
        ]
        for answer in approvals:
            with self.subTest(answer=answer):
                self.assertTrue(consent_evidence(self.messages(answer), 1075, "u1")["approved"])
        self.assertFalse(
            consent_evidence(self.messages("Yeah. That sounds about right."), 1075, "u1")[
                "approved"
            ]
        )

    def test_canonical_question_can_be_last_sentence_after_price_or_fragment(self):
        for prefix in ["Yes, I can do $1075. ", "Okay. ", "The total is $1,075. "]:
            self.assertTrue(
                consent_evidence(
                    self.messages(
                        "Yeah, go ahead.", prefix + "May I book load LD1 at $1075 total?"
                    ),
                    1075,
                    "u1",
                )["approved"]
            )
        self.assertFalse(
            consent_evidence(
                self.messages("Yes.", "May I book load LD1 at $1075 total? Please confirm."),
                1075,
                "u1",
            )["approved"]
        )

    def test_unknown_or_conditional_tails_and_long_answers_fail(self):
        for answer in [
            "Sure if you can",
            "Okay but wait",
            "Yes actually",
            "Yeah maybe",
            "Correct only",
            "Yes don't",
            "Yes not",
            "Yep hold",
            "Yes no",
            "Yes ١",
            "Please book it",
            "Yeah that sounds about right",
            "Yes please thanks perfect sir please thanks perfect please",
        ]:
            with self.subTest(answer=answer):
                self.assertFalse(consent_evidence(self.messages(answer), 1075, "u1")["approved"])
        self.assertTrue(
            consent_evidence(
                self.messages("Yes please thanks perfect sir please thanks perfect"), 1075, "u1"
            )["approved"]
        )
