"""The legacy TMS line protocol: encoding requests and strictly parsing replies.

See docs/tms/README.md. The TMS does not signal its faults, so a reply is only
complete if it is one terminated ERR line, or finishes with a whole terminated
line equal to END. Nothing here touches the network.
"""

from dataclasses import dataclass
import re

COMMANDS = frozenset({"LOAD_QUERY", "LOAD_GET", "LOAD_BOOK", "DEBUG_ECHO"})
MAX_LINE_BYTES = 4096
MAX_REPLY_BYTES = 256 * 1024

_KEY = re.compile(r"[A-Z][A-Z0-9_]*")


class InvalidRequest(ValueError):
    """A request we refuse to send. Never includes field values."""


class MalformedReply(Exception):
    """A reply that broke the framing rules."""


@dataclass(frozen=True)
class TmsError:
    code: str
    message: str


@dataclass(frozen=True)
class Reply:
    records: tuple = ()
    error: TmsError | None = None


def _printable(value):
    return value.isascii() and all(32 <= ord(char) < 127 for char in value)


def encode_request(command, token, fields=None):
    if command not in COMMANDS:
        raise InvalidRequest("Unknown command.")
    pairs = [("CMD", command), ("AUTH", token)]
    for key, value in (fields or {}).items():
        if key in ("CMD", "AUTH") or not _KEY.fullmatch(key):
            raise InvalidRequest("Reserved or invalid field name.")
        pairs.append((key, str(value)))
    for key, value in pairs:
        if "|" in value or not _printable(value):
            raise InvalidRequest(f"Invalid value for {'AUTH' if key == 'AUTH' else key}.")
    request = ("|".join(f"{key}:{value}" for key, value in pairs) + "\r\n").encode("ascii")
    if len(request) > MAX_LINE_BYTES:
        raise InvalidRequest("Request exceeds the frame limit.")
    return request


def check_bounds(buffer):
    """Fail early on a reply that can never be valid, without waiting for the rest."""
    if len(buffer) > MAX_REPLY_BYTES:
        raise MalformedReply("Reply exceeds the total size limit.")
    last_line_end = buffer.rfind(b"\r\n")
    tail = last_line_end + 2 if last_line_end >= 0 else 0
    if len(buffer) - tail > MAX_LINE_BYTES:
        raise MalformedReply("Line exceeds the frame limit.")


def frame_complete(buffer):
    """True once a whole reply has arrived, so we can stop without waiting for close."""
    if buffer.startswith(b"ERR|"):
        return b"\r\n" in buffer
    return b"END" in bytes(buffer).split(b"\r\n")[:-1]


def _fields(segments):
    fields = {}
    for segment in segments:
        key, colon, value = segment.partition(":")
        if not colon or not _KEY.fullmatch(key) or key in fields:
            raise MalformedReply("Bad field.")
        fields[key] = value.rstrip(" ")
    return fields


def parse_reply(data, echo=False):
    """Parse a complete reply. Set echo for DEBUG_ECHO, whose records start with a bare ECHO."""
    if len(data) > MAX_REPLY_BYTES:
        raise MalformedReply("Reply exceeds the total size limit.")
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError:
        raise MalformedReply("Reply is not ASCII.") from None

    *lines, tail = text.split("\r\n")
    if not lines or tail:
        raise MalformedReply("Reply is not terminated.")
    for line in lines:
        if len(line) + 2 > MAX_LINE_BYTES or not (line == "" or _printable(line)):
            raise MalformedReply("Bad line.")

    if text.startswith("ERR|"):
        if len(lines) != 1:
            raise MalformedReply("An error is exactly one line.")
        fields = _fields(lines[0].split("|")[1:])
        if not fields.get("CODE") or "MSG" not in fields:
            raise MalformedReply("Error without a code and message.")
        return Reply(error=TmsError(fields["CODE"], fields["MSG"]))

    if lines.pop() != "END" or "END" in lines:
        raise MalformedReply("Reply does not finish with one END line.")
    records = []
    for line in lines:
        segments = line.split("|")
        if echo:
            if segments[0] != "ECHO":
                raise MalformedReply("Expected an ECHO record.")
            segments = segments[1:]
        records.append(_fields(segments))
    return Reply(records=tuple(records))
