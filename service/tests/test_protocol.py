"""Wire protocol rules from docs/tms/README.md, and the sanitized live replies."""

import json
from pathlib import Path
import unittest

from service.adapters.tms.client import classify_booking_reply
from service.adapters.tms.protocol import (
    MAX_LINE_BYTES,
    MAX_REPLY_BYTES,
    InvalidRequest,
    MalformedReply,
    check_bounds,
    encode_request,
    frame_complete,
    parse_reply,
)
from service.core.ports import BookingOutcome

FIXTURES = Path(__file__).resolve().parents[2] / "docs/tms/fixtures/booking-replies.json"


class EncodeTests(unittest.TestCase):
    def test_exact_bytes(self):
        self.assertEqual(
            encode_request("LOAD_GET", "tok", {"LOAD_ID": "LD01023"}),
            b"CMD:LOAD_GET|AUTH:tok|LOAD_ID:LD01023\r\n",
        )

    def test_rejects_anything_that_could_change_the_request(self):
        for fields in (
            {"LOAD_ID": "LD1|CMD:LOAD_BOOK"},
            {"LOAD_ID": "LD1\r\nCMD:LOAD_BOOK"},
            {"LOAD_ID": "LDé"},
            {"CMD": "LOAD_BOOK"},
            {"AUTH": "other"},
            {"lower": "x"},
        ):
            with self.subTest(fields=fields), self.assertRaises(InvalidRequest):
                encode_request("LOAD_GET", "tok", fields)

    def test_rejects_unknown_commands_and_oversized_requests(self):
        with self.assertRaises(InvalidRequest):
            encode_request("LOAD_CANCEL", "tok")
        with self.assertRaises(InvalidRequest):
            encode_request("LOAD_GET", "tok", {"LOAD_ID": "L" * MAX_LINE_BYTES})

    def test_errors_never_include_the_token(self):
        with self.assertRaises(InvalidRequest) as caught:
            encode_request("LOAD_GET", "secret|token")
        self.assertNotIn("secret", str(caught.exception))


class ParseTests(unittest.TestCase):
    def test_accepts_valid_replies(self):
        cases = {
            "END\r\n": 0,
            "LOAD_ID:LD1|RATE:2709\r\nEND\r\n": 1,
            "LOAD_ID:LD1|NOTES:WEEKEND\r\nEND\r\n": 1,
            "LOAD_ID:LD1\r\nLOAD_ID:LD2\r\nEND\r\n": 2,
        }
        for raw, count in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(len(parse_reply(raw.encode()).records), count)

    def test_parses_by_key_and_trims_padding(self):
        record = parse_reply(b"RATE:751     |LOAD_ID:LD01001     |NEW_FIELD:x\r\nEND\r\n").records[0]
        self.assertEqual(record, {"RATE": "751", "LOAD_ID": "LD01001", "NEW_FIELD": "x"})

    def test_keeps_blank_values_and_colons_in_values(self):
        record = parse_reply(b"NOTES:     |DIMS:1:2\r\nEND\r\n").records[0]
        self.assertEqual(record, {"NOTES": "", "DIMS": "1:2"})

    def test_requires_a_whole_terminated_end_line(self):
        for raw in (
            b"",
            b"LOAD_ID:LD1|NOTES:WEEKEND\r\n",
            b"NOTES:END\r\n",
            b"LOAD_ID:LD1\r\nNOTES:LEGEND\r\n",
            b"LOAD_ID:LD1|RATE:27",
            b"LOAD_ID:LD1\r\nEND",
            b"LOAD_ID:LD1\r\nEND\r",
            b"LOAD_ID:LD1\r\nEND\n",
            b"LOAD_ID:LD1\nEND\r\n",
            b"LOAD_ID:LD1\r\nEND  \r\n",
            b"LOAD_ID:LD1\r\nend\r\n",
        ):
            with self.subTest(raw=raw), self.assertRaises(MalformedReply):
                parse_reply(raw)

    def test_rejects_anything_around_the_end_line(self):
        for raw in (
            b"END\r\nEND\r\n",
            b"END\r\nLOAD_ID:LD1\r\n",
            b"END\r\nextra",
            b"LOAD_ID:LD1\r\n\r\nEND\r\n",
        ):
            with self.subTest(raw=raw), self.assertRaises(MalformedReply):
                parse_reply(raw)

    def test_rejects_malformed_records(self):
        for raw in (
            b"LOAD_ID:LD1||RATE:2709\r\nEND\r\n",
            b"LOAD_ID:LD1|LOAD_ID:LD2\r\nEND\r\n",
            b"load_id:LD1\r\nEND\r\n",
            b"LOAD_ID:LD\xff\r\nEND\r\n",
            b"LOAD_ID:LD\x011\r\nEND\r\n",
            b"ECHO|AUTH:OK\r\nEND\r\n",
        ):
            with self.subTest(raw=raw), self.assertRaises(MalformedReply):
                parse_reply(raw)

    def test_an_error_is_exactly_one_terminated_line(self):
        self.assertEqual(
            parse_reply(b"ERR|CODE:NOT_FOUND|MSG:Load not found\r\n").error.code, "NOT_FOUND"
        )
        for raw in (
            b"ERR|CODE:NOT_FOUND",
            b"ERR|CODE:NOT_FOUND\r",
            b"ERR|\r\n",
            b"ERR|CODE:X\r\n",
            b"ERR|CODE:X|MSG:y\r\nEND\r\n",
        ):
            with self.subTest(raw=raw), self.assertRaises(MalformedReply):
                parse_reply(raw)

    def test_echo_has_a_bare_prefix(self):
        reply = parse_reply(b"ECHO|AUTH:OK|FIELDS_PARSED:3|MSG:HELLO\r\nEND\r\n", echo=True)
        self.assertEqual(reply.records[0]["FIELDS_PARSED"], "3")
        with self.assertRaises(MalformedReply):
            parse_reply(b"AUTH:OK\r\nEND\r\n", echo=True)

    def test_size_limits_apply_per_line_and_in_total(self):
        allowed = b"NOTES:" + b"x" * (MAX_LINE_BYTES - 8) + b"\r\nEND\r\n"
        self.assertEqual(len(parse_reply(allowed).records), 1)
        with self.assertRaises(MalformedReply):
            parse_reply(b"NOTES:" + b"x" * MAX_LINE_BYTES + b"\r\nEND\r\n")
        line = b"NOTES:" + b"x" * 1000 + b"\r\n"
        with self.assertRaises(MalformedReply):
            parse_reply(line * (MAX_REPLY_BYTES // len(line) + 1) + b"END\r\n")

    def test_a_reply_over_one_frame_in_total_is_valid(self):
        line = b"NOTES:" + b"x" * 500 + b"\r\n"
        self.assertEqual(len(parse_reply(line * 20 + b"END\r\n").records), 20)


class StreamingTests(unittest.TestCase):
    def test_frame_complete_needs_a_whole_end_line(self):
        self.assertTrue(frame_complete(b"LOAD_ID:LD1\r\nEND\r\n"))
        self.assertTrue(frame_complete(b"END\r\n"))
        self.assertTrue(frame_complete(b"ERR|CODE:X|MSG:y\r\n"))
        for buffer in (b"", b"LOAD_ID:LD1\r\n", b"LOAD_ID:LD1\r\nEND", b"NOTES:WEEKEND\r\n", b"ERR|CODE"):
            with self.subTest(buffer=buffer):
                self.assertFalse(frame_complete(buffer))

    def test_check_bounds_fails_early(self):
        check_bounds(bytearray(b"x" * MAX_LINE_BYTES))
        with self.assertRaises(MalformedReply):
            check_bounds(bytearray(b"x" * (MAX_LINE_BYTES + 1)))
        with self.assertRaises(MalformedReply):
            check_bounds(bytearray(b"x\r\n" * (MAX_REPLY_BYTES // 3 + 1)))


class BookingReplyTests(unittest.TestCase):
    def test_sanitized_live_replies(self):
        expected = {
            "ack_pending": BookingOutcome.ACK_PENDING,
            "rejected": BookingOutcome.REJECTED,
            "already_booked_not_confirmation": BookingOutcome.UNKNOWN,
        }
        cases = json.loads(FIXTURES.read_text())["cases"]
        self.assertEqual(len(cases), 6)
        for case in cases:
            with self.subTest(case=case["case"]):
                receipt = classify_booking_reply(case["raw"].encode("ascii"), case["load_id"])
                self.assertIs(receipt.outcome, expected[case["expected_outcome"]])
                self.assertEqual(receipt.raw_reply, case["raw"])
                if receipt.outcome is BookingOutcome.ACK_PENDING:
                    self.assertTrue(receipt.reference)
                    self.assertEqual(receipt.tms_status, "PENDING")

    def test_a_direct_booked_receipt_is_confirmed(self):
        raw = b"LOAD_ID:LD1  |BOOKING_REF:BR1|STATUS:BOOKED  |TIMESTAMP:20261031010210\r\nEND\r\n"
        receipt = classify_booking_reply(raw, "LD1")
        self.assertIs(receipt.outcome, BookingOutcome.CONFIRMED)
        self.assertEqual(receipt.reference, "BR1")

    def test_definitive_rejections(self):
        for code in ("INVALID_RATE", "NOT_FOUND", "UNKNOWN_LOAD"):
            with self.subTest(code=code):
                raw = f"ERR|CODE:{code}|MSG:no\r\n".encode()
                self.assertIs(classify_booking_reply(raw, "LD1").outcome, BookingOutcome.REJECTED)

    def test_anything_unclear_is_unknown(self):
        for raw in (
            b"",
            b"LOAD_ID:LD1|BOOKING_REF:BR1|STATUS:PENDING\r\n",
            b"LOAD_ID:OTHER|BOOKING_REF:BR1|STATUS:PENDING\r\nEND\r\n",
            b"LOAD_ID:LD1|STATUS:PENDING\r\nEND\r\n",
            b"LOAD_ID:LD1|BOOKING_REF:|STATUS:PENDING\r\nEND\r\n",
            b"LOAD_ID:LD1|BOOKING_REF:BR1|STATUS:HELD\r\nEND\r\n",
            b"LOAD_ID:LD1|BOOKING_REF:BR1|STATUS:PENDING\r\nLOAD_ID:LD1\r\nEND\r\n",
            b"END\r\n",
            b"ERR|CODE:ALREADY_BOOKED|MSG:load not available\r\n",
            b"ERR|CODE:SERVER_ERROR|MSG:internal error\r\n",
            b"ERR|CODE:SOMETHING_NEW|MSG:unknown\r\n",
        ):
            with self.subTest(raw=raw):
                self.assertIs(classify_booking_reply(raw, "LD1").outcome, BookingOutcome.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
