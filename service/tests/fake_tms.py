"""A fake TMS for tests: a real local TCP server that speaks the protocol and injects faults.

It follows observed behaviour, not only the handbook: search also returns PENDING
loads, an unknown load is NOT_FOUND, and a booking is acknowledged PENDING with a
reference (docs/tms-contract.md). It never touches the real TMS.
"""

import asyncio
import re
from collections import deque
from collections.abc import Awaitable, Callable, Iterable

from service.adapters.tms.client import TmsClient, TmsSettings

TOKEN = "fake-token"
HOLD_SECONDS = 30.0  # how long a silent fault keeps the connection open

# Faults, each used up by one command. DEBUG_ECHO skips them, as the handbook says.
SILENT = "silent"  # handle the request, never reply
LOST = "lost"  # drop the request, never reply
PARTIAL = "partial"  # send half the reply, then close
CUT_AT_LINE = "cut_at_line"  # send whole lines but no END, then close
MALFORMED = "malformed"  # break the framing
TRAILING = "trailing"  # send bytes after a complete reply
DELAYED_CLOSE = "delayed_close"  # send a complete reply, then hold the connection open
SERVER_ERROR = "server_error"  # reply with ERR|CODE:SERVER_ERROR
SPLIT = "split"  # send a valid reply a few bytes at a time

_CHANGE: dict[str | None, Callable[[bytes], bytes]] = {
    PARTIAL: lambda reply: reply[: max(1, len(reply) // 2)],
    CUT_AT_LINE: lambda reply: reply.removesuffix(b"END\r\n"),
    MALFORMED: lambda reply: reply.replace(b"|", b"||", 1),
    TRAILING: lambda reply: reply + b"LOAD_ID:EXTRA\r\n",
    SERVER_ERROR: lambda _: b"ERR|CODE:SERVER_ERROR|MSG:internal error\r\n",
}
EQUIPMENT = {"DRY_VAN", "REEFER", "FLATBED", "STEP_DECK", "POWER_ONLY"}
SUMMARY = (
    *("LOAD_ID", "ORIG_CITY", "ORIG_STATE", "ORIG_ZIP", "DEST_CITY", "DEST_STATE"),
    *("DEST_ZIP", "PICKUP_DT", "EQTYPE", "RATE", "MILES", "STATUS"),
)
ECHO = "ECHO|AUTH:OK|FIELDS_PARSED:{count}|MSG:{message}\r\nEND\r\n"
NOT_FOUND = b"ERR|CODE:NOT_FOUND|MSG:load not found\r\n"
WIDTHS = {"LOAD_ID": 12, "ORIG_CITY": 30, "DEST_CITY": 30, "EQTYPE": 10, "RATE": 8, "STATUS": 8}


def make_load(load_id: str = "LD09001", **overrides: str) -> dict[str, str]:
    """A TMS record shaped like a live LOAD_GET reply after the protocol trims padding."""
    load = {
        "LOAD_ID": load_id,
        "ORIG_CITY": "Dallas",
        "ORIG_STATE": "TX",
        "ORIG_ZIP": "75201",
        "DEST_CITY": "Atlanta",
        "DEST_STATE": "GA",
        "DEST_ZIP": "30303",
        "PICKUP_DT": "20991231080000",
        "DELIVERY_DT": "20991231200000",
        "EQTYPE": "DRY_VAN",
        "RATE": "2000",
        "WEIGHT": "42000",
        "COMMODITY": "General Freight",
        "PIECES": "24",
        "MILES": "780",
        "DIMS": "53ft x 8ft x 9ft",
        "NOTES": "",
        "STATUS": "OPEN",
        "MAX_BUY": "2300",
    }
    return load | overrides


class FakeTMS:
    def __init__(self, loads: Iterable[dict[str, str]] = (), faults: Iterable[str] = ()) -> None:
        self.board = {load["LOAD_ID"]: load for load in loads}
        self.faults = deque(faults)
        self.requests: list[str] = []  # every request received, token hidden
        self.booked_status = "PENDING"  # what a booking turns into; BOOKED was never observed
        self.book_reply: bytes | None = None  # a recorded reply to answer LOAD_BOOK with
        self.port = 0
        self._server: asyncio.Server | None = None
        self._handlers: set[asyncio.Task[None]] = set()

    async def __aenter__(self) -> "FakeTMS":
        self._server = await asyncio.start_server(self._serve, "127.0.0.1", 0)
        self.port = self._server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._server:
            self._server.close()
        for handler in list(self._handlers):
            handler.cancel()
        await asyncio.gather(*self._handlers, return_exceptions=True)

    async def _serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        task = asyncio.current_task()
        assert task is not None
        self._handlers.add(task)
        try:
            line = await asyncio.wait_for(reader.readuntil(b"\r\n"), HOLD_SECONDS)
            await self._respond(line.decode("ascii")[:-2], writer)
        except (asyncio.IncompleteReadError, asyncio.CancelledError, ConnectionError, TimeoutError):
            pass
        finally:
            self._handlers.discard(task)
            writer.close()

    async def _respond(self, line: str, writer: asyncio.StreamWriter) -> None:
        self.requests.append(line.replace(TOKEN, "<token>"))
        fields = dict(part.split(":", 1) for part in line.split("|") if ":" in part)
        skip = not self.faults or fields.get("CMD") == "DEBUG_ECHO"
        fault = None if skip else self.faults.popleft()
        if fault in (LOST, SILENT):  # the fake keeps no state, so the two look alike
            await asyncio.sleep(HOLD_SECONDS)
            return
        reply = self._dispatch(fields)
        if fault in _CHANGE:
            reply = _CHANGE[fault](reply)
        size = 7 if fault == SPLIT else max(1, len(reply))
        for start in range(0, len(reply), size):
            writer.write(reply[start : start + size])
            await writer.drain()
            await asyncio.sleep(0)
        if fault == DELAYED_CLOSE:
            await asyncio.sleep(HOLD_SECONDS)

    def _dispatch(self, fields: dict[str, str]) -> bytes:
        if fields.get("AUTH") != TOKEN:
            return b"ERR|CODE:AUTH_FAILED|MSG:invalid or missing auth token\r\n"
        command = fields.get("CMD")
        if command == "DEBUG_ECHO":
            return ECHO.format(count=len(fields), message=fields.get("MSG", "")).encode()
        if command == "LOAD_QUERY":
            return self._query(fields)
        if command == "LOAD_GET":
            load = self.board.get(fields.get("LOAD_ID", ""))
            return _line(load, tuple(load)) + b"END\r\n" if load else NOT_FOUND
        if command == "LOAD_BOOK":
            return self.book_reply or self._book(fields)
        return b"ERR|CODE:UNKNOWN_CMD|MSG:unknown command\r\n"

    def _book(self, fields: dict[str, str]) -> bytes:
        load = self.board.get(fields.get("LOAD_ID", ""))
        if load is None:
            return NOT_FOUND
        if not re.fullmatch(r"[1-9][0-9]*(\.00)?", fields.get("AGREED_RATE", "")):
            return b"ERR|CODE:INVALID_RATE|MSG:AGREED_RATE must be a positive integer\r\n"
        if load["STATUS"] != "OPEN":
            return b"ERR|CODE:ALREADY_BOOKED|MSG:Already booked by this token\r\n"
        load["STATUS"] = self.booked_status
        receipt = {"LOAD_ID": load["LOAD_ID"], "BOOKING_REF": "FAKE0001"}
        stamp = {"STATUS": self.booked_status, "TIMESTAMP": "20261103010203"}
        return (
            _line(receipt | stamp, ("LOAD_ID", "BOOKING_REF", "STATUS", "TIMESTAMP")) + b"END\r\n"
        )

    def _query(self, fields: dict[str, str]) -> bytes:
        filters = {
            key: fields[key] for key in ("EQTYPE", "ORIG_STATE", "DEST_STATE") if key in fields
        }
        limit = fields.get("MAX_RESULTS", "20")
        if not filters or filters.get("EQTYPE", "DRY_VAN") not in EQUIPMENT:
            return b"ERR|CODE:MISSING_FIELD|MSG:invalid or missing filter\r\n"
        if not re.fullmatch(r"[1-9][0-9]*", limit):
            return b"ERR|CODE:MISSING_FIELD|MSG:Invalid MAX_RESULTS\r\n"
        rows = [
            load
            for load in self.board.values()
            if load["STATUS"] in ("OPEN", "PENDING")
            and all(load[key] == value for key, value in filters.items())
        ]
        return b"".join(_line(load, SUMMARY) for load in rows[: int(limit)]) + b"END\r\n"


def _line(load: dict[str, str], keys: tuple[str, ...]) -> bytes:
    """One record, padded as the live TMS pads it."""
    padded = (f"{key}:{load[key].ljust(WIDTHS.get(key, 0))}" for key in keys if key in load)
    return ("|".join(padded) + "\r\n").encode("ascii")


def client_for(
    tms: FakeTMS, *, token: str = TOKEN, budget: float = 1.5, attempt: float = 0.25
) -> TmsClient:  # a booking gets the read budget too, so a silent fault ends quickly
    """A client with short timeouts, pointed at the fake."""
    settings = TmsSettings(
        host="127.0.0.1",
        port=tms.port,
        token=token,
        read_budget_seconds=budget,
        attempt_seconds=attempt,
        book_seconds=budget,
    )
    return TmsClient(settings)


def run[T](
    tms: FakeTMS,
    action: Callable[[TmsClient], Awaitable[T]],
    *,
    token: str = TOKEN,
    budget: float = 1.5,
    attempt: float = 0.25,
) -> T:
    """Start the fake, run one client action against it, then stop it."""

    async def scenario() -> T:
        async with tms:
            return await action(client_for(tms, token=token, budget=budget, attempt=attempt))

    return asyncio.run(scenario())
