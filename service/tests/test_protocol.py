"""The TMS wire format: exact requests, and replies that are complete or refused."""

import json
from pathlib import Path

import pytest

from service.adapters.tms.protocol import (
    MAX_LINE_BYTES,
    MAX_REPLY_BYTES,
    InvalidRequest,
    MalformedReply,
    TmsError,
    check_bounds,
    encode_request,
    frame_complete,
    parse_reply,
)

FIXTURES = Path(__file__).parents[2] / "docs/tms/fixtures/booking-replies.json"


def test_a_request_is_one_exact_line() -> None:
    request = encode_request("LOAD_GET", "tok", {"LOAD_ID": "LD01023"})
    assert request == b"CMD:LOAD_GET|AUTH:tok|LOAD_ID:LD01023\r\n"


@pytest.mark.parametrize(
    "fields",
    [
        {"LOAD_ID": "LD1|CMD:LOAD_BOOK"},  # a pipe would add a field
        {"LOAD_ID": "LD1\r\nCMD:LOAD_BOOK"},  # a line break would add a request
        {"LOAD_ID": "LDé"},  # not ASCII
        {"CMD": "LOAD_BOOK"},
        {"AUTH": "other"},
        {"lower": "x"},
    ],
)
def test_anything_that_could_change_a_request_is_refused(fields: dict[str, str]) -> None:
    with pytest.raises(InvalidRequest):
        encode_request("LOAD_GET", "tok", fields)


def test_unknown_commands_and_oversized_requests_are_refused() -> None:
    with pytest.raises(InvalidRequest):
        encode_request("LOAD_CANCEL", "tok")
    with pytest.raises(InvalidRequest):
        encode_request("LOAD_GET", "tok", {"LOAD_ID": "L" * MAX_LINE_BYTES})


def test_a_refusal_never_includes_the_token() -> None:
    with pytest.raises(InvalidRequest) as caught:
        encode_request("LOAD_GET", "secret|token")
    assert "secret" not in str(caught.value)


@pytest.mark.parametrize(
    ("raw", "records"),
    [
        (b"END\r\n", ()),  # an empty search
        (b"LOAD_ID:LD1|RATE:2709\r\nEND\r\n", ({"LOAD_ID": "LD1", "RATE": "2709"},)),
        (b"LOAD_ID:LD1|NOTES:WEEKEND\r\nEND\r\n", ({"LOAD_ID": "LD1", "NOTES": "WEEKEND"},)),
        (b"LOAD_ID:LD1\r\nLOAD_ID:LD2\r\nEND\r\n", ({"LOAD_ID": "LD1"}, {"LOAD_ID": "LD2"})),
        (
            b"RATE:751     |LOAD_ID:LD01001  |NEW:x\r\nEND\r\n",
            ({"RATE": "751", "LOAD_ID": "LD01001", "NEW": "x"},),
        ),
        (b"NOTES:     |DIMS:1:2\r\nEND\r\n", ({"NOTES": "", "DIMS": "1:2"},)),  # blank kept
    ],
)
def test_valid_replies_are_read_by_key(raw: bytes, records: tuple[dict[str, str], ...]) -> None:
    assert parse_reply(raw).records == records


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"LOAD_ID:LD1|NOTES:WEEKEND\r\n",  # no END line at all
        b"NOTES:END\r\n",
        b"LOAD_ID:LD1\r\nNOTES:LEGEND\r\n",
        b"LOAD_ID:LD1|RATE:27",  # cut off mid-line
        b"LOAD_ID:LD1\r\nEND",
        b"LOAD_ID:LD1\r\nEND\r",
        b"LOAD_ID:LD1\r\nEND\n",
        b"LOAD_ID:LD1\nEND\r\n",
        b"LOAD_ID:LD1\r\nEND  \r\n",
        b"LOAD_ID:LD1\r\nend\r\n",
        b"END\r\nEND\r\n",  # anything around the END line
        b"END\r\nLOAD_ID:LD1\r\n",
        b"END\r\nextra",
        b"LOAD_ID:LD1\r\n\r\nEND\r\n",
        b"LOAD_ID:LD1||RATE:2709\r\nEND\r\n",  # malformed records
        b"LOAD_ID:LD1|LOAD_ID:LD2\r\nEND\r\n",
        b"load_id:LD1\r\nEND\r\n",
        b"LOAD_ID:LD\xff\r\nEND\r\n",
        b"LOAD_ID:LD\x011\r\nEND\r\n",
        b"ECHO|AUTH:OK\r\nEND\r\n",
    ],
)
def test_incomplete_or_malformed_replies_are_refused(raw: bytes) -> None:
    with pytest.raises(MalformedReply):
        parse_reply(raw)


def test_an_error_is_exactly_one_terminated_line() -> None:
    reply = parse_reply(b"ERR|CODE:NOT_FOUND|MSG:Load not found\r\n")
    assert reply.error == TmsError("NOT_FOUND", "Load not found")
    for raw in (
        b"ERR|CODE:NOT_FOUND",
        b"ERR|CODE:NOT_FOUND\r",
        b"ERR|\r\n",
        b"ERR|CODE:X\r\n",
        b"ERR|CODE:X|MSG:y\r\nEND\r\n",
    ):
        with pytest.raises(MalformedReply):
            parse_reply(raw)


def test_echo_records_start_with_a_bare_prefix() -> None:
    reply = parse_reply(b"ECHO|AUTH:OK|FIELDS_PARSED:3|MSG:HELLO\r\nEND\r\n", echo=True)
    assert reply.records[0]["FIELDS_PARSED"] == "3"
    with pytest.raises(MalformedReply):
        parse_reply(b"AUTH:OK\r\nEND\r\n", echo=True)


def test_size_limits_apply_per_line_and_in_total() -> None:
    longest = b"NOTES:" + b"x" * (MAX_LINE_BYTES - 8) + b"\r\nEND\r\n"
    assert len(parse_reply(longest).records) == 1
    with pytest.raises(MalformedReply):
        parse_reply(b"NOTES:" + b"x" * MAX_LINE_BYTES + b"\r\nEND\r\n")
    line = b"NOTES:" + b"x" * 1000 + b"\r\n"
    with pytest.raises(MalformedReply):
        parse_reply(line * (MAX_REPLY_BYTES // len(line) + 1) + b"END\r\n")


def test_a_reply_larger_than_one_frame_in_total_is_valid() -> None:
    line = b"NOTES:" + b"x" * 500 + b"\r\n"
    assert len(parse_reply(line * 20 + b"END\r\n").records) == 20


def test_reading_stops_only_at_a_whole_end_line_or_error_line() -> None:
    for buffer in (b"LOAD_ID:LD1\r\nEND\r\n", b"END\r\n", b"ERR|CODE:X|MSG:y\r\n"):
        assert frame_complete(buffer)
    for buffer in (b"", b"LOAD_ID:LD1\r\n", b"LOAD_ID:LD1\r\nEND", b"NOTES:WEEKEND\r\n", b"ERR|"):
        assert not frame_complete(buffer)


def test_a_reply_that_can_never_be_valid_fails_early() -> None:
    check_bounds(b"x" * MAX_LINE_BYTES)
    with pytest.raises(MalformedReply):
        check_bounds(b"x" * (MAX_LINE_BYTES + 1))
    with pytest.raises(MalformedReply):
        check_bounds(b"x\r\n" * (MAX_REPLY_BYTES // 3 + 1))


def test_every_recorded_live_booking_reply_parses() -> None:
    cases = json.loads(FIXTURES.read_text())["cases"]
    replies = [parse_reply(case["raw"].encode("ascii")) for case in cases]
    pending = [reply.records[0] for reply in replies if reply.records]
    errors = [reply.error.code for reply in replies if reply.error]
    assert len(cases) == 6
    assert [record["STATUS"] for record in pending] == ["PENDING"] * 4
    assert all(record["BOOKING_REF"] for record in pending)
    assert sorted(errors) == ["ALREADY_BOOKED", "INVALID_RATE"]
