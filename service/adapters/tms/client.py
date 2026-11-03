"""TMS client: one request per fresh connection, and reads retried inside a time budget.

Reads change nothing, so a fault is retried. LOAD_BOOK spends a load for good, so it is
sent once and never retried, and everything it left behind is kept (INV-7, INV-10).
"""

import asyncio
import hashlib
import random
import re
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass, field

from service.adapters.tms.mapping import to_load, to_summary
from service.adapters.tms.protocol import (
    InvalidRequest,
    MalformedReply,
    Reply,
    check_bounds,
    encode_request,
    frame_complete,
    parse_reply,
)
from service.core.models import Load, LoadSummary

EQUIPMENT = frozenset({"DRY_VAN", "REEFER", "FLATBED", "STEP_DECK", "POWER_ONLY"})
NOT_FOUND = frozenset({"NOT_FOUND", "UNKNOWN_LOAD"})  # live TMS, then handbook
RETRYABLE = frozenset({"SERVER_ERROR"})
_STATE = re.compile(r"[A-Z]{2}")


class TmsUnavailable(Exception):
    """The TMS gave no usable answer within the read budget. Report it honestly (D-5)."""


@dataclass(frozen=True, kw_only=True)
class TmsSettings:
    host: str
    port: int
    token: str = field(repr=False)
    read_budget_seconds: float = 6.0  # everything a read may take, retries included
    attempt_seconds: float = 2.0
    read_attempts: int = 3
    book_seconds: float = 10.0  # the one LOAD_BOOK exchange, connecting included


@dataclass
class Wire:
    """How far one exchange got, kept even when it fails part way."""

    step: str = "connect"  # then send, receive, and received once reading stops
    received: bytes = b""


@dataclass(frozen=True)
class Sent:
    """What one LOAD_BOOK left behind: the step reached, the error type, every byte."""

    step: str
    error: str | None  # the exception's type, never its message
    raw: bytes
    reply: Reply | None  # None unless the reply was complete and well formed

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.raw).hexdigest()


class TmsClient:
    def __init__(self, settings: TmsSettings) -> None:
        self.settings = settings

    async def echo(self) -> None:
        """Prove the TMS is reachable and accepts our token. DEBUG_ECHO skips fault injection."""
        reply = await self._read("DEBUG_ECHO", {"MSG": "HELLO"}, echo=True)
        if reply.error or len(reply.records) != 1 or reply.records[0].get("AUTH") != "OK":
            raise TmsUnavailable("TMS echo failed.")

    async def query(
        self,
        *,
        equipment: str | None = None,
        origin_state: str | None = None,
        dest_state: str | None = None,
        limit: int = 20,
    ) -> list[LoadSummary]:
        """Search by lane and equipment. Results keep their real status, PENDING included."""
        fields = search_fields(equipment, origin_state, dest_state, limit)
        reply = await self._read("LOAD_QUERY", fields)
        if reply.error:
            raise TmsUnavailable(f"TMS search failed: {reply.error.code}.")
        try:
            return [to_summary(record) for record in reply.records]
        except MalformedReply:
            raise TmsUnavailable("TMS search returned a record without a load ID.") from None

    async def get(self, load_id: str) -> Load | None:
        """One load in full, or None if the TMS does not know it."""
        reply = await self._read("LOAD_GET", {"LOAD_ID": load_id})
        if reply.error:
            if reply.error.code in NOT_FOUND:
                return None
            raise TmsUnavailable(f"TMS lookup failed: {reply.error.code}.")
        if len(reply.records) != 1 or reply.records[0].get("LOAD_ID") != load_id:
            raise TmsUnavailable("TMS lookup returned the wrong record.")
        return to_load(reply.records[0])

    async def book(self, load_id: str, mc: str, rate: int) -> Sent:
        """Send LOAD_BOOK once on one fresh connection. Never retried, whatever happens.

        A request we refuse to build raises InvalidRequest before anything is sent.
        Otherwise this never raises: a fault is returned with the step it reached.
        """
        if type(rate) is not int or rate <= 0 or not mc.isdigit():
            raise InvalidRequest("A booking needs a positive whole rate and a numeric MC.")
        fields: dict[str, str | int] = {"LOAD_ID": load_id, "MC_NUM": mc, "AGREED_RATE": rate}
        request = encode_request("LOAD_BOOK", self.settings.token, fields)
        wire = Wire()
        try:
            async with asyncio.timeout(self.settings.book_seconds):
                reply = parse_reply(await self._exchange(request, wire))
        except (TimeoutError, OSError, MalformedReply) as error:
            return Sent(wire.step, type(error).__name__, wire.received, None)
        return Sent(wire.step, None, wire.received, reply)

    async def _read(
        self, command: str, fields: Mapping[str, str | int], *, echo: bool = False
    ) -> Reply:
        """Retry faults and SERVER_ERROR until the budget or the attempts run out."""
        settings = self.settings
        request = encode_request(command, settings.token, fields)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + settings.read_budget_seconds
        for attempt in range(settings.read_attempts):
            if attempt:
                jitter = random.uniform(0.05, 0.25)  # noqa: S311 - spacing retries, not a secret
                await asyncio.sleep(min(jitter, max(0.0, deadline - loop.time())))
            remaining = deadline - loop.time()
            if remaining <= 0:
                break
            try:
                async with asyncio.timeout(min(settings.attempt_seconds, remaining)):
                    raw = await self._exchange(request, Wire())
                reply = parse_reply(raw, echo=echo)
            except (TimeoutError, OSError, MalformedReply):
                continue
            if reply.error is None or reply.error.code not in RETRYABLE:
                return reply
        raise TmsUnavailable("The TMS did not answer in time.")

    async def _exchange(self, request: bytes, wire: Wire) -> bytes:
        """One request on a fresh connection. Stops at a whole reply, without waiting for close.

        The wire records each step before it starts and every byte as it arrives.
        """
        reader, writer = await asyncio.open_connection(self.settings.host, self.settings.port)
        try:
            wire.step = "send"
            writer.write(request)
            await writer.drain()
            wire.step = "receive"
            while not frame_complete(wire.received):
                chunk = await reader.read(4096)
                if not chunk:
                    break
                wire.received += chunk
                check_bounds(wire.received)
            wire.step = "received"
            return wire.received
        finally:
            writer.close()
            with suppress(OSError, TimeoutError):
                await asyncio.wait_for(writer.wait_closed(), 0.05)


def search_fields(
    equipment: str | None, origin_state: str | None, dest_state: str | None, limit: int
) -> dict[str, str | int]:
    """Only filters established live; the TMS silently ignores names it does not know."""
    fields: dict[str, str | int] = {}
    if equipment is not None:
        eqtype = equipment.strip().upper()
        if eqtype not in EQUIPMENT:
            raise ValueError("Unsupported equipment.")
        fields["EQTYPE"] = eqtype
    for key, state in (("ORIG_STATE", origin_state), ("DEST_STATE", dest_state)):
        if state is None:
            continue
        code = state.strip().upper()
        if not _STATE.fullmatch(code):
            raise ValueError("Use a two-letter state.")
        fields[key] = code
    if not fields:
        raise ValueError("At least one search filter is required.")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("Use a limit from 1 to 1000.")
    fields["MAX_RESULTS"] = limit
    return fields
