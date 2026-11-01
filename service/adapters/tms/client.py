"""Async TMS client: bounded read retries, and one guarded send for bookings."""

import asyncio
import base64
import contextvars
from contextlib import suppress
from dataclasses import dataclass, field, replace
import hashlib
import random
import re

from service.adapters.tms.mapping import to_load, to_summary
from service.adapters.tms.protocol import (
    MalformedReply,
    check_bounds,
    encode_request,
    frame_complete,
    parse_reply,
)
from service.core.ports import BookingOutcome, BookingReceipt, TmsUnavailable

EQUIPMENT = frozenset({"DRY_VAN", "REEFER", "FLATBED", "STEP_DECK", "POWER_ONLY"})
NOT_FOUND = frozenset({"NOT_FOUND", "UNKNOWN_LOAD"})
REJECTED = NOT_FOUND | {"INVALID_RATE"}
RETRYABLE = frozenset({"SERVER_ERROR"})


class BookingDisabled(Exception):
    """Live LOAD_BOOK is off. Raised before any connection opens."""


@dataclass(frozen=True)
class TmsSettings:
    host: str
    port: int
    token: str = field(repr=False)
    read_budget_seconds: float = 6.0
    attempt_seconds: float = 2.0
    read_attempts: int = 3
    write_seconds: float = 5.0
    booking_enabled: bool = False


def classify_booking_reply(raw, load_id):
    """Turn a LOAD_BOOK reply into a receipt. Anything unclear is UNKNOWN."""
    text = raw.decode("ascii", errors="replace")

    def unknown(reason, tms_status=None):
        return BookingReceipt(
            BookingOutcome.UNKNOWN, tms_status=tms_status, raw_reply=text, reason=reason
        )

    try:
        reply = parse_reply(raw)
    except MalformedReply:
        return unknown("malformed_reply")
    if reply.error:
        if reply.error.code in REJECTED:
            return BookingReceipt(
                BookingOutcome.REJECTED, raw_reply=text, reason=reply.error.code.lower()
            )
        return unknown(reply.error.code.lower())

    if len(reply.records) != 1:
        return unknown("unexpected_record_count")
    record = reply.records[0]
    reference = record.get("BOOKING_REF")
    status = record.get("STATUS")
    if record.get("LOAD_ID") != load_id or not reference:
        return unknown("receipt_does_not_match", status)
    from service.adapters.tms.mapping import parse_timestamp
    if parse_timestamp(record.get("TIMESTAMP")) is None:
        return unknown("invalid_receipt_timestamp", status)
    outcomes = {"PENDING": BookingOutcome.ACK_PENDING, "BOOKED": BookingOutcome.CONFIRMED}
    if status not in outcomes:
        return unknown("unexpected_status", status)
    return BookingReceipt(outcomes[status], reference, status, text)


class TmsClient:
    def __init__(self, settings):
        self.settings = settings
        self.capture = contextvars.ContextVar("tms_capture", default=None)

    @property
    def booking_enabled(self):
        return self.settings.booking_enabled

    async def _exchange(self, request):
        """One request on a fresh connection. Stops at END, without waiting for close."""
        evidence = self.capture.get()
        if evidence is not None: evidence["phase"] = "connecting"
        reader, writer = await asyncio.open_connection(self.settings.host, self.settings.port)
        try:
            if evidence is not None: evidence.update(phase="sending", send_started=True)
            writer.write(request)
            await writer.drain()
            if evidence is not None: evidence.update(phase="reading", write_drained=True)
            buffer = bytearray()
            while True:
                chunk = await reader.read(4096)
                if not chunk:
                    return bytes(buffer)
                buffer.extend(chunk)
                if evidence is not None: evidence["received"].extend(chunk)
                check_bounds(buffer)
                if frame_complete(buffer):
                    return bytes(buffer)
        finally:
            with suppress(Exception): writer.close()
            with suppress(Exception):
                async with asyncio.timeout(.05): await writer.wait_closed()

    async def _read(self, command, fields, echo=False):
        settings = self.settings
        request = encode_request(command, settings.token, fields)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + settings.read_budget_seconds
        for attempt in range(settings.read_attempts):
            remaining = deadline - loop.time()
            if remaining <= 0:
                break
            try:
                raw = await asyncio.wait_for(
                    self._exchange(request), min(settings.attempt_seconds, remaining)
                )
                reply = parse_reply(raw, echo=echo)
            except (TimeoutError, OSError, MalformedReply):
                pass
            else:
                if not reply.error or reply.error.code not in RETRYABLE:
                    return reply
            if attempt + 1 < settings.read_attempts:
                await asyncio.sleep(min(random.uniform(0.05, 0.25), max(0, remaining)))
        raise TmsUnavailable("TMS read failed.")

    async def echo(self):
        reply = await self._read("DEBUG_ECHO", {"MSG": "HELLO"}, echo=True)
        if reply.error or len(reply.records) != 1 or reply.records[0].get("AUTH") != "OK":
            raise TmsUnavailable("TMS echo failed.")
        return reply.records[0]

    async def query(
        self, *, equipment=None, origin_state=None, dest_state=None, origin_city=None,
        pickup_date=None, limit=20,
    ):
        """Search by the established filters only. Unknown fields are silently ignored."""
        fields = {}
        if equipment is not None:
            equipment = equipment.strip().upper()
            if equipment not in EQUIPMENT:
                raise ValueError("Unsupported equipment.")
            fields["EQTYPE"] = equipment
        for key, state in (("ORIG_STATE", origin_state), ("DEST_STATE", dest_state)):
            if state is not None:
                state = state.strip().upper()
                if not re.fullmatch(r"[A-Z]{2}", state):
                    raise ValueError("Use a two-letter state.")
                fields[key] = state
        if origin_city is not None:
            fields["ORIG_CITY"] = origin_city.strip()
        if pickup_date is not None:
            if not re.fullmatch(r"[0-9]{8}", pickup_date):
                raise ValueError("Use YYYYMMDD for the pickup date.")
            fields["PICKUP_DATE"] = pickup_date
        if not fields:
            raise ValueError("At least one search filter is required.")
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("Use a limit from 1 to 1000.")
        fields["MAX_RESULTS"] = limit

        reply = await self._read("LOAD_QUERY", fields)
        if reply.error:
            raise TmsUnavailable(f"TMS search failed: {reply.error.code}.")
        try:
            return [to_summary(record) for record in reply.records]
        except MalformedReply:
            raise TmsUnavailable("TMS search returned a bad record.") from None

    async def get(self, load_id):
        """Return a full load, or None if the TMS does not know it."""
        reply = await self._read("LOAD_GET", {"LOAD_ID": load_id})
        if reply.error:
            if reply.error.code in NOT_FOUND:
                return None
            raise TmsUnavailable(f"TMS lookup failed: {reply.error.code}.")
        if len(reply.records) != 1 or reply.records[0].get("LOAD_ID") != load_id:
            raise TmsUnavailable("TMS lookup returned the wrong record.")
        return to_load(reply.records[0])

    async def book(self, load_id, mc, rate):
        """Send LOAD_BOOK exactly once. A failed or unclear reply is never retried here."""
        if not self.booking_enabled:
            raise BookingDisabled("Live LOAD_BOOK is disabled.")
        if type(rate) is not int or rate <= 0:
            raise ValueError("Use a positive whole rate.")
        if not re.fullmatch(r"[0-9]{1,8}", mc):
            raise ValueError("Use digits only for the MC number.")
        request = encode_request(
            "LOAD_BOOK",
            self.settings.token,
            {"LOAD_ID": load_id, "MC_NUM": mc, "AGREED_RATE": rate},
        )
        evidence = {"phase": "prepared", "send_started": False, "write_drained": False,
                    "received": bytearray(), "error_type": None}
        marker = self.capture.set(evidence)
        try:
            raw = await asyncio.wait_for(self._exchange(request), self.settings.write_seconds)
            receipt = classify_booking_reply(raw.replace(self.settings.token.encode(), b"[HIDDEN]"), load_id)
        except (TimeoutError, OSError, MalformedReply) as error:
            raw = bytes(evidence["received"])
            evidence["error_type"] = type(error).__name__
            receipt = BookingReceipt(BookingOutcome.UNKNOWN if evidence["send_started"] else BookingOutcome.REJECTED,
                                     raw_reply=raw.replace(self.settings.token.encode(),b"[HIDDEN]").decode("ascii",errors="replace"),
                                     reason=type(error).__name__ if evidence["send_started"] else "tms_unavailable")
        finally: self.capture.reset(marker)
        safe_raw = raw.replace(self.settings.token.encode(), b"[HIDDEN]")
        diagnostic = {k:v for k,v in evidence.items() if k != "received"}
        diagnostic.update(response_bytes=len(raw), response_sha256=hashlib.sha256(raw).hexdigest(),
                          received_b64=base64.b64encode(safe_raw).decode())
        return replace(receipt, diagnostic=diagnostic)
