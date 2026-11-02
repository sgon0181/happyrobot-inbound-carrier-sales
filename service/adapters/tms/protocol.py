"""The legacy TMS line protocol: building requests and strictly reading replies.

A reply is complete only if it is one CRLF-terminated ERR line, or ends with a
whole CRLF-terminated line equal to END. The TMS does not mark its faults, so
anything else is refused rather than guessed (docs/tms/README.md). Nothing here
touches the network.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass

COMMANDS = frozenset({"LOAD_QUERY", "LOAD_GET", "LOAD_BOOK", "DEBUG_ECHO"})
MAX_LINE_BYTES = 4096  # the handbook's frame limit, per line including CRLF
MAX_REPLY_BYTES = 256 * 1024  # our own bound on a whole reply; live replies reached 7,941 bytes

_KEY = re.compile(r"[A-Z][A-Z0-9_]*")
_PRINTABLE = re.compile(r"[\x20-\x7e]*")


class InvalidRequest(ValueError):
    """A request we refuse to send. The message never includes a field value."""


class MalformedReply(Exception):
    """A reply that broke the framing rules."""


@dataclass(frozen=True)
class TmsError:
    code: str
    message: str


@dataclass(frozen=True)
class Reply:
    records: tuple[dict[str, str], ...] = ()
    error: TmsError | None = None


def encode_request(
    command: str, token: str, fields: Mapping[str, str | int] | None = None
) -> bytes:
    """Build one request line, refusing anything that could change what it asks for."""
    if command not in COMMANDS:
        raise InvalidRequest("Unknown command.")
    pairs = {"CMD": command, "AUTH": token}
    for key, value in (fields or {}).items():
        if key in pairs or not _KEY.fullmatch(key):
            raise InvalidRequest("Reserved or invalid field name.")
        pairs[key] = str(value)
    for key, value in pairs.items():
        if not _safe(value):
            raise InvalidRequest(f"Invalid value for {key}.")
    request = "|".join(f"{key}:{value}" for key, value in pairs.items()) + "\r\n"
    if len(request) > MAX_LINE_BYTES:
        raise InvalidRequest("Request exceeds the frame limit.")
    return request.encode("ascii")


def _safe(value: str) -> bool:
    """Printable ASCII without a pipe, so a value cannot add a field or a second request."""
    return "|" not in value and _PRINTABLE.fullmatch(value) is not None


def frame_complete(buffer: bytes) -> bool:
    """True once a whole reply has arrived, so reading can stop without waiting for close."""
    if buffer.startswith(b"ERR|"):
        return b"\r\n" in buffer
    return b"END" in buffer.split(b"\r\n")[:-1]


def check_bounds(buffer: bytes) -> None:
    """Fail early on a partial reply that can never become valid."""
    if len(buffer) > MAX_REPLY_BYTES:
        raise MalformedReply("Reply exceeds the total size limit.")
    unfinished = len(buffer) - (buffer.rfind(b"\r\n") + 2 if b"\r\n" in buffer else 0)
    if unfinished > MAX_LINE_BYTES:
        raise MalformedReply("Line exceeds the frame limit.")


def parse_reply(data: bytes, *, echo: bool = False) -> Reply:
    """Parse a complete reply. Set echo for DEBUG_ECHO, whose records start with a bare ECHO."""
    lines = _lines(data)
    if lines[0].startswith("ERR|"):
        return Reply(error=_error(lines))
    if lines[-1] != "END" or "END" in lines[:-1]:
        raise MalformedReply("Reply does not finish with one END line.")
    return Reply(records=tuple(_record(line, echo) for line in lines[:-1]))


def _lines(data: bytes) -> list[str]:
    """Split a whole reply into lines, refusing anything unterminated, oversized or unprintable."""
    if len(data) > MAX_REPLY_BYTES:
        raise MalformedReply("Reply exceeds the total size limit.")
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError:
        raise MalformedReply("Reply is not ASCII.") from None
    *lines, tail = text.split("\r\n")
    if not lines or tail:
        raise MalformedReply("Reply is not terminated.")
    if any(len(line) + 2 > MAX_LINE_BYTES or not _PRINTABLE.fullmatch(line) for line in lines):
        raise MalformedReply("Bad line.")
    return lines


def _error(lines: list[str]) -> TmsError:
    if len(lines) != 1:
        raise MalformedReply("An error is exactly one line.")
    fields = _fields(lines[0].split("|")[1:])
    if not fields.get("CODE") or "MSG" not in fields:
        raise MalformedReply("Error without a code and message.")
    return TmsError(fields["CODE"], fields["MSG"])


def _record(line: str, echo: bool) -> dict[str, str]:
    segments = line.split("|")
    if echo:
        if segments[0] != "ECHO":
            raise MalformedReply("Expected an ECHO record.")
        segments = segments[1:]
    return _fields(segments)


def _fields(segments: list[str]) -> dict[str, str]:
    """KEY:VALUE pairs. Values keep inner colons and lose the TMS's right-padding."""
    fields: dict[str, str] = {}
    for segment in segments:
        key, colon, value = segment.partition(":")
        if not colon or not _KEY.fullmatch(key) or key in fields:
            raise MalformedReply("Bad field.")
        fields[key] = value.rstrip(" ")
    return fields
