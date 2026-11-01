"""Contextual identity preservation and code redaction on synthetic dialogue."""

import unittest

from service.adapters.transcripts import redact_transcript


class TranscriptTests(unittest.TestCase):
    def message(self, role, text, **extra):
        return {"role": role, "content": text, "session_id": "session", **extra}

    def test_numeric_mc_answer_and_spoken_mc_answer_are_preserved(self):
        for identity in ("138328", "one three eight three two eight", "1 3 8 3 2 8"):
            text, _ = redact_transcript(
                [
                    self.message("assistant", "What is your MC number?"),
                    self.message("user", identity),
                ],
                mc="138328",
            )
            self.assertIn(identity, text)

    def test_code_attempt_different_from_mc_is_redacted(self):
        for attempt in ("012345", "0 1 2 3 4 5", "zero one two three four five"):
            text, _ = redact_transcript(
                [
                    self.message("assistant", "Read the six-digit code, please."),
                    self.message("user", attempt),
                ],
                mc="138328",
            )
            self.assertNotIn(attempt, text)
            self.assertIn("redacted]", text)

    def test_failed_code_equal_to_mc_does_not_hide_earlier_identity(self):
        text, _ = redact_transcript(
            [
                self.message("assistant", "What is your MC number?"),
                self.message("user", "138328"),
                self.message("assistant", "Please read the emailed code."),
                self.message("user", "138328"),
                self.message(
                    "assistant",
                    "That code was wrong.",
                    tool_calls=[{"name": "verify_code", "arguments": {"code": "138328"}}],
                ),
            ],
            mc="138328",
        )
        users = [line for line in text.splitlines() if line.startswith("user:")]
        self.assertEqual(users[0], "user: 138328")
        self.assertNotIn("138328", users[1])

    def test_mc_restatement_after_verification_is_preserved(self):
        text, _ = redact_transcript(
            [
                self.message("assistant", "You are verified. Which lane do you need?"),
                self.message("user", "My MC is one three eight three two eight. Texas to Ohio."),
            ],
            mc="138328",
        )
        self.assertIn("one three eight three two eight", text)
        self.assertIn("Texas to Ohio", text)

    def test_same_utterance_preserves_labelled_mc_but_redacts_code(self):
        text, _ = redact_transcript(
            [
                self.message("assistant", "What is your MC number?"),
                self.message("user", "My MC is 138328 and my code is 138328."),
            ],
            mc="138328",
        )
        self.assertIn("My MC is 138328", text)
        self.assertIn("my code is [code redacted]", text)

    def test_fragmented_attempt_and_leading_zero_stay_redacted(self):
        text, _ = redact_transcript(
            [
                self.message("assistant", "Read the emailed code."),
                self.message("user", "zero one two"),
                self.message("user", "three four five"),
            ],
            mc="138328",
        )
        self.assertNotIn("zero one two", text)
        self.assertNotIn("three four five", text)

    def test_fragments_never_merge_across_sessions(self):
        text, _ = redact_transcript(
            [
                self.message("assistant", "Read the code.", session_id="a"),
                self.message("user", "123", session_id="a"),
                self.message("assistant", "Read the code.", session_id="b"),
                self.message("user", "456", session_id="b"),
            ],
            mc="138328",
        )
        self.assertEqual(sum(line.startswith("user:") for line in text.splitlines()), 2)
        self.assertNotIn("123", text)
        self.assertNotIn("456", text)

    def test_nearby_lane_and_price_details_remain(self):
        text, _ = redact_transcript(
            [
                self.message("assistant", "Read the code."),
                self.message("user", "012345"),
                self.message("assistant", "You are verified. Which lane and equipment?"),
                self.message("user", "Dry van, Texas to Ohio, can you do 2950?"),
            ],
            mc="138328",
        )
        self.assertIn("Texas to Ohio", text)
        self.assertIn("2950", text)
        self.assertNotIn("012345", text)
