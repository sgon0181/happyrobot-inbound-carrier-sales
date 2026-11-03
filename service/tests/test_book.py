"""LOAD_BOOK against a real local TCP server: sent once, never retried, nothing discarded."""

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from service.adapters.tms.client import Sent, TmsClient, TmsSettings
from service.adapters.tms.protocol import InvalidRequest, Reply, TmsError
from service.tests import fake_tms as fake
from service.tests.fake_tms import FakeTMS, make_load, run

FIXTURES = Path(__file__).parents[2] / "docs" / "tms" / "fixtures" / "booking-replies.json"
REQUEST = "CMD:LOAD_BOOK|AUTH:<token>|LOAD_ID:LD1|MC_NUM:138328|AGREED_RATE:1850"


def book(tms: FakeTMS, load_id: str = "LD1", rate: int = 1850, budget: float = 0.3) -> Sent:
    return run(tms, lambda client: client.book(load_id, "138328", rate), budget=budget)


def test_a_booking_is_one_exact_request_and_its_receipt_is_kept_whole() -> None:
    tms = FakeTMS([make_load("LD1")])
    sent = book(tms)
    assert tms.requests == [REQUEST]
    assert (sent.step, sent.error) == ("received", None)
    assert sent.raw.startswith(b"LOAD_ID:LD1") and sent.raw.endswith(b"\r\nEND\r\n")
    assert sent.sha256 == hashlib.sha256(sent.raw).hexdigest()
    assert sent.reply is not None
    [record] = sent.reply.records
    assert (record["BOOKING_REF"], record["STATUS"]) == ("FAKE0001", "PENDING")
    assert tms.board["LD1"]["STATUS"] == "PENDING"


def test_a_refusal_is_a_parsed_error_and_is_never_resent() -> None:
    tms = FakeTMS([make_load("LD1", STATUS="PENDING")])
    sent = book(tms)
    assert sent.reply is not None and sent.reply.error == TmsError(
        "ALREADY_BOOKED", "Already booked by this token"
    )
    failed = book(FakeTMS([make_load("LD1")], faults=[fake.SERVER_ERROR, fake.SERVER_ERROR]))
    assert failed.reply == Reply(error=TmsError("SERVER_ERROR", "internal error"))


@pytest.mark.parametrize(
    ("fault", "step", "error"),
    [
        (fake.SILENT, "receive", "TimeoutError"),
        (fake.DELAYED_CLOSE, "received", None),  # whole reply, so no need to wait for close
        (fake.PARTIAL, "received", "MalformedReply"),
        (fake.CUT_AT_LINE, "received", "MalformedReply"),
        (fake.MALFORMED, "received", "MalformedReply"),
        (fake.SPLIT, "received", None),
    ],
)
def test_every_fault_keeps_its_step_error_and_bytes_after_one_request(
    fault: str, step: str, error: str | None
) -> None:
    tms = FakeTMS([make_load("LD1")], faults=[fault, fault])
    sent = book(tms)
    assert (sent.step, sent.error, len(tms.requests)) == (step, error, 1)
    assert (sent.reply is None) == (error is not None)
    if fault != fake.SILENT:
        assert sent.raw.startswith(b"LOAD_ID:LD1")  # every byte that arrived


def test_an_oversized_reply_stops_while_receiving_with_its_bytes() -> None:
    tms = FakeTMS([make_load("LD1")])
    tms.book_reply = b"LOAD_ID:" + b"X" * 5000
    sent = book(tms)
    assert (sent.step, sent.error, len(sent.raw)) == ("receive", "MalformedReply", 5008)


def test_a_connection_that_never_opens_sent_nothing() -> None:
    client = TmsClient(TmsSettings(host="127.0.0.1", port=9, token="t", book_seconds=0.5))
    sent = asyncio.run(client.book("LD1", "138328", 1850))
    assert (sent.step, sent.error, sent.raw, sent.reply) == (
        "connect",
        "ConnectionRefusedError",
        b"",
        None,
    )


@pytest.mark.parametrize(
    ("load_id", "mc", "rate"),
    [("LD1", "138328", 0), ("LD1", "138328", 18.5), ("LD1", "MC1", 1850), ("LD|1", "1", 1)],
)
def test_a_request_we_refuse_to_build_is_never_sent(load_id: str, mc: str, rate: Any) -> None:
    tms = FakeTMS([make_load("LD1")])
    with pytest.raises(InvalidRequest):
        run(tms, lambda client: client.book(load_id, mc, rate))
    assert tms.requests == []


@pytest.mark.parametrize("case", json.loads(FIXTURES.read_text())["cases"])
def test_every_recorded_booking_reply_parses_as_it_was_observed(case: dict[str, str]) -> None:
    tms = FakeTMS([make_load(case["load_id"])])
    tms.book_reply = case["raw"].encode("ascii")
    sent = book(tms, case["load_id"])
    assert (sent.raw, sent.error) == (tms.book_reply, None)
    assert sent.reply is not None
    if sent.reply.error is None:
        [record] = sent.reply.records
        assert (record["LOAD_ID"], record["STATUS"]) == (case["load_id"], "PENDING")
    else:
        assert sent.reply.error.code in {"INVALID_RATE", "ALREADY_BOOKED"}
