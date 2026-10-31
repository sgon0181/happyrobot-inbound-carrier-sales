"""A local fake TMS: a real TCP server that speaks the protocol and injects faults.

It follows observed behaviour, not only the handbook: bookings reply PENDING by
default, search still returns PENDING loads, and an unknown load is NOT_FOUND.
Any final confirmation it produces is a simulation, not evidence of a real
command. See docs/tms-contract.md.
"""

import asyncio
from collections import deque
from dataclasses import dataclass, field
import re

SILENT = "silent"  # Process the request, then never reply.
LOST = "lost"  # Drop the request unprocessed, then never reply.
PARTIAL = "partial"  # Send part of the reply, then close.
CUT_AT_LINE = "cut_at_line"  # Send whole lines, but no END, then close.
MALFORMED = "malformed"  # Send a reply that breaks the framing rules.
TRAILING = "trailing"  # Send bytes after a complete reply.
DELAYED_CLOSE = "delayed_close"  # Send a complete reply, then hold the connection open.
SERVER_ERROR = "server_error"  # Reply with ERR|CODE:SERVER_ERROR.
SPLIT = "split"  # Send a valid reply a few bytes at a time.

EQUIPMENT = {"DRY_VAN", "REEFER", "FLATBED", "STEP_DECK", "POWER_ONLY"}
SUMMARY_FIELDS = (
    "LOAD_ID", "ORIG_CITY", "ORIG_STATE", "ORIG_ZIP", "DEST_CITY", "DEST_STATE",
    "DEST_ZIP", "PICKUP_DT", "EQTYPE", "RATE", "MILES", "STATUS",
)
FULL_FIELDS = (
    "LOAD_ID", "ORIG_CITY", "ORIG_STATE", "ORIG_ZIP", "DEST_CITY", "DEST_STATE",
    "DEST_ZIP", "PICKUP_DT", "DELIVERY_DT", "EQTYPE", "RATE", "WEIGHT", "COMMODITY",
    "PIECES", "MILES", "DIMS", "NOTES", "STATUS", "MAX_BUY",
)
WIDTHS = {"LOAD_ID": 12, "ORIG_CITY": 30, "DEST_CITY": 30, "EQTYPE": 10, "RATE": 8, "STATUS": 8}


def make_load(load_id="LD09001", **overrides):
    load = {
        "LOAD_ID": load_id, "ORIG_CITY": "Dallas", "ORIG_STATE": "TX", "ORIG_ZIP": "75201",
        "DEST_CITY": "Atlanta", "DEST_STATE": "GA", "DEST_ZIP": "30303",
        "PICKUP_DT": "20991231080000", "DELIVERY_DT": "20991231200000", "EQTYPE": "DRY_VAN",
        "RATE": "2000", "WEIGHT": "42000", "COMMODITY": "General Freight", "PIECES": "24",
        "MILES": "780", "DIMS": "53ft x 8ft x 9ft", "NOTES": "", "STATUS": "OPEN",
        "MAX_BUY": "2300",
    }
    load.update(overrides)
    return load


def _line(load, keys):
    return "|".join(
        f"{key}:{str(load[key]).ljust(WIDTHS.get(key, 0))}" for key in keys if key in load
    )


@dataclass
class FakeTMS:
    loads: list = field(default_factory=list)
    token: str = "fake-token"
    booking_status: str = "PENDING"
    held_open_seconds: float = 30.0

    def __post_init__(self):
        self.board = {load["LOAD_ID"]: dict(load) for load in self.loads}
        self.faults = deque()
        self.requests = []
        self.book_requests = []
        self.bookings = {}
        self.port = None
        self._server = None
        self._handlers = set()
        self._sequence = 0

    async def __aenter__(self):
        self._server = await asyncio.start_server(self._serve, "127.0.0.1", 0)
        self.port = self._server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *_):
        self._server.close()
        for handler in list(self._handlers):
            handler.cancel()
        await asyncio.gather(*self._handlers, return_exceptions=True)
        await self._server.wait_closed()

    def inject(self, *faults):
        """Queue faults for upcoming commands. DEBUG_ECHO bypasses them, as documented."""
        self.faults.extend(faults)

    def set_status(self, load_id, status):
        self.board[load_id]["STATUS"] = status

    def simulate_final_booking(self, load_id, expose_identity=False):
        """SIMULATED ONLY: there is no such real command."""
        self.board[load_id]["STATUS"] = "BOOKED"
        if expose_identity:
            self.board[load_id].update(self.bookings[load_id])

    async def _serve(self, reader, writer):
        task = asyncio.current_task()
        self._handlers.add(task)
        try:
            line = await asyncio.wait_for(reader.readuntil(b"\r\n"), 30)
            await self._respond(line.decode("ascii")[:-2], writer)
        except (asyncio.IncompleteReadError, asyncio.CancelledError, ConnectionError, TimeoutError):
            pass
        finally:
            self._handlers.discard(task)
            writer.close()

    async def _respond(self, line, writer):
        self.requests.append(line.replace(self.token, "<token>"))
        fields = dict(part.split(":", 1) for part in line.split("|") if ":" in part)
        command = fields.get("CMD")
        fault = self.faults.popleft() if self.faults and command != "DEBUG_ECHO" else None

        if fault == LOST:
            await asyncio.sleep(self.held_open_seconds)
            return
        reply = self._dispatch(command, fields)
        if fault == SERVER_ERROR:
            reply = "ERR|CODE:SERVER_ERROR|MSG:internal error\r\n"

        if fault == SILENT:
            await asyncio.sleep(self.held_open_seconds)
        elif fault == PARTIAL:
            writer.write(reply[: max(1, len(reply) // 2)].encode("ascii"))
        elif fault == CUT_AT_LINE:
            writer.write(reply.removesuffix("END\r\n").encode("ascii"))
        elif fault == MALFORMED:
            writer.write(reply.replace("|", "||", 1).encode("ascii"))
        elif fault == SPLIT:
            data = reply.encode("ascii")
            for start in range(0, len(data), 7):
                writer.write(data[start:start + 7])
                await writer.drain()
                await asyncio.sleep(0)
        elif fault == TRAILING:
            writer.write((reply + "LOAD_ID:EXTRA\r\n").encode("ascii"))
        else:
            writer.write(reply.encode("ascii"))
            await writer.drain()
            if fault == DELAYED_CLOSE:
                await asyncio.sleep(self.held_open_seconds)
                return
        await writer.drain()

    def _dispatch(self, command, fields):
        if fields.get("AUTH") != self.token:
            return "ERR|CODE:AUTH_FAILED|MSG:invalid or missing auth token\r\n"
        handlers = {
            "DEBUG_ECHO": self._echo, "LOAD_QUERY": self._query,
            "LOAD_GET": self._get, "LOAD_BOOK": self._book,
        }
        if command not in handlers:
            return "ERR|CODE:UNKNOWN_CMD|MSG:unknown command\r\n"
        return handlers[command](fields)

    def _echo(self, fields):
        return f"ECHO|AUTH:OK|FIELDS_PARSED:{len(fields)}|MSG:{fields.get('MSG', '')}\r\nEND\r\n"

    def _query(self, fields):
        filters = {key: value for key, value in fields.items()
                   if key in {"EQTYPE", "ORIG_STATE", "DEST_STATE", "ORIG_CITY", "PICKUP_DATE"}}
        if not filters:
            return "ERR|CODE:MISSING_FIELD|MSG:at least one filter required\r\n"
        if "EQTYPE" in filters and filters["EQTYPE"] not in EQUIPMENT:
            return "ERR|CODE:MISSING_FIELD|MSG:Invalid EQTYPE\r\n"
        limit = fields.get("MAX_RESULTS", "20")
        if not re.fullmatch(r"[1-9][0-9]*", limit):
            return "ERR|CODE:MISSING_FIELD|MSG:Invalid MAX_RESULTS\r\n"

        def matches(load):
            return (
                load["STATUS"] in ("OPEN", "PENDING")
                and filters.get("EQTYPE", load["EQTYPE"]) == load["EQTYPE"]
                and filters.get("ORIG_STATE", load["ORIG_STATE"]) == load["ORIG_STATE"]
                and filters.get("DEST_STATE", load["DEST_STATE"]) == load["DEST_STATE"]
                and filters.get("ORIG_CITY", "").lower() in load["ORIG_CITY"].lower()
                and load["PICKUP_DT"].startswith(filters.get("PICKUP_DATE", ""))
            )

        rows = [load for load in self.board.values() if matches(load)][: int(limit)]
        return "".join(_line(load, SUMMARY_FIELDS) + "\r\n" for load in rows) + "END\r\n"

    def _get(self, fields):
        load = self.board.get(fields.get("LOAD_ID"))
        if load is None:
            return "ERR|CODE:NOT_FOUND|MSG:load not found\r\n"
        keys = FULL_FIELDS + tuple(key for key in load if key not in FULL_FIELDS)
        return _line(load, keys) + "\r\nEND\r\n"

    def _book(self, fields):
        load_id, rate = fields.get("LOAD_ID"), fields.get("AGREED_RATE")
        if not load_id or not fields.get("MC_NUM") or rate is None:
            return "ERR|CODE:MISSING_FIELD|MSG:missing required field\r\n"
        self.book_requests.append(dict(fields, AUTH="<token>"))
        load = self.board.get(load_id)
        if load is None:
            return "ERR|CODE:NOT_FOUND|MSG:load not found\r\n"
        if load_id in self.bookings:
            return "ERR|CODE:ALREADY_BOOKED|MSG:Already booked by this token\r\n"
        if not re.fullmatch(r"[1-9][0-9]*(\.0+)?", rate):
            return "ERR|CODE:INVALID_RATE|MSG:AGREED_RATE must be a positive integer\r\n"
        self._sequence += 1
        reference = f"FAKE{self._sequence:012d}"
        self.bookings[load_id] = {
            "BOOKING_REF": reference, "MC_NUM": fields["MC_NUM"], "AGREED_RATE": rate,
        }
        load["STATUS"] = self.booking_status
        return (
            f"LOAD_ID:{load_id.ljust(12)}|BOOKING_REF:{reference}|"
            f"STATUS:{self.booking_status.ljust(8)}|TIMESTAMP:20991231000000\r\nEND\r\n"
        )
