"""What a senior rep can do to a reservation: confirm, decline or reconcile (section 10).

The only code that sends LOAD_BOOK. Each action carries the booking version the rep saw
and is refused if the row has moved on (D-31). Confirm wins a version-checked write to
SUBMITTING before it sends, so a double click or two reps cannot send twice, and the
send is never retried (INV-7). Each state change and its event are one write, and the
event records the new state (INV-9), which is how the dashboard follows a reservation.
"""

import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from service.adapters.tms.client import Sent, TmsUnavailable
from service.adapters.tms.mapping import parse_timestamp
from service.adapters.tms.protocol import InvalidRequest
from service.adapters.twin import Data, Row, Twin, TwinUnavailable
from service.bookings import with_event
from service.calls import Reply
from service.core.loads import is_offerable, same_shipment
from service.core.models import Load

STALE_SEND = timedelta(seconds=60)  # a SUBMITTING row this old lost the request sending it
NOTHING_CREATED = frozenset({"INVALID_RATE", "UNKNOWN_LOAD", "NOT_FOUND"})
RECEIPT_STATES = {"PENDING": "ACK_PENDING", "BOOKED": "CONFIRMED"}
STALE: Reply = {"status": "stale"}  # the row moved on since the rep's screen: refresh
log = logging.getLogger("service")
Edit = Callable[[Data | None], tuple[Data | None, None]]


class Booker(Protocol):
    """The TMS calls a rep's actions need. TmsClient is the real one."""

    async def get(self, load_id: str) -> Load | None: ...

    async def book(self, load_id: str, mc: str, rate: int) -> Sent: ...


@dataclass(frozen=True)
class Receipt:
    """The booking state a send leads to, and what the TMS said."""

    state: str
    reason: str | None = None
    reference: str | None = None
    tms_status: str | None = None


class RepActions:
    def __init__(
        self,
        *,
        twin: Twin,
        tms: Booker,
        live: bool,
        blocked: frozenset[str],
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        save_attempts: int = 5,
        save_pause: float = 2.0,
    ) -> None:
        self.twin, self.tms, self.live, self.blocked, self.now = twin, tms, live, blocked, now
        self.save_attempts, self.save_pause = save_attempts, save_pause
        self._sending: set[asyncio.Task[Reply]] = set()

    async def confirm(self, load_id: str, version: int, rep: str) -> Reply:
        """Recheck the load, win the write to SUBMITTING, send once and save the reply."""
        if not self.live:
            return {"status": "live_booking_off"}  # each send spends a load for good
        row = await self._current(load_id, version, "RESERVED")
        if not isinstance(row, Row):
            return row
        if row.data.get("cohort") != "real":
            return {"status": "record_read_only"}
        try:
            load = await self.tms.get(load_id)
        except TmsUnavailable:
            return {"status": "tms_unavailable"}  # still RESERVED, nothing sent: retry
        reason = recheck(load, row.data, self.now(), self.blocked)
        if reason is not None:
            failed = {"state": "FAILED", "reason": reason, "rep": rep}
            written = await self._write(load_id, row, "recheck_failed", failed)
            return {"status": "failed", "reason": reason} if written else STALE
        send_id, now = uuid.uuid4().hex, self.now().isoformat()
        intent = {"state": "SUBMITTING", "rep": rep, "send_id": send_id, "submitted_at": now}
        if not await self._write(load_id, row, "confirm", intent):
            return STALE  # another click or rep won, so this one sends nothing
        task = asyncio.ensure_future(self._send(load_id, row.data, send_id))
        self._sending.add(task)  # held, so a closed screen cannot stop the save
        task.add_done_callback(self._sending.discard)
        return await asyncio.shield(task)

    async def decline(self, load_id: str, version: int, rep: str) -> Reply:
        """Release the reservation the rep saw. Nothing was sent, so the load is free."""
        row = await self._current(load_id, version, "RESERVED")
        if not isinstance(row, Row):
            return row
        if not await self._write(load_id, row, "decline", {"state": "RELEASED", "rep": rep}):
            return STALE
        return {"status": "released"}

    async def reconcile(self, load_id: str, version: int, rep: str) -> Reply:
        """Read the load from the TMS and record what it says. Never sends.

        A read shows no reference or owner, so it never changes a booking's state. The
        one change is a SUBMITTING row whose sender died: after 60 seconds it is UNKNOWN.
        """
        row = await self._current(load_id, version, "SUBMITTING", "ACK_PENDING", "UNKNOWN")
        if not isinstance(row, Row):
            return row
        fields: Data = {}
        if row.data["state"] == "SUBMITTING":
            if self.now() - datetime.fromisoformat(row.data["submitted_at"]) < STALE_SEND:
                return {"status": "too_early"}
            fields = {"state": "UNKNOWN", "reason": "interrupted_send"}
        try:
            load = await self.tms.get(load_id)
            seen = "missing" if load is None else load.status
        except TmsUnavailable:
            seen = "unavailable"
        if not await self._write(load_id, row, "reconcile", fields, rep=rep, load_status=seen):
            return STALE
        state = fields.get("state", row.data["state"])
        return {"status": "reconciled", "state": state, "load_status": seen}

    async def _current(self, load_id: str, version: int, *states: str) -> Row | Reply:
        """The row, if it is still the version the rep saw and in a state this action takes."""
        row = await self.twin.get("bookings", load_id)
        if row is None or row.version != version:
            return STALE
        if row.data.get("state") not in states:
            return {"status": "not_allowed", "state": row.data.get("state")}
        return row

    async def _write(
        self, load_id: str, row: Row, action: str, fields: Data, **detail: str
    ) -> bool:
        """The change and its event, only if the row is still at the version read."""
        data = row.data | fields
        data["events"] = with_event(row.data, self.now(), action, fields | detail)
        return await self.twin.update("bookings", load_id, row.version, data)

    async def _send(self, load_id: str, booking: Data, send_id: str) -> Reply:
        try:
            sent = await self.tms.book(load_id, booking["mc"], booking["rate"])
        except InvalidRequest:
            sent = Sent("build", "InvalidRequest", b"", None)
        receipt = classify(sent, load_id)
        evidence = {
            "step": sent.step,
            "error": sent.error,
            "bytes": len(sent.raw),
            "sha256": sent.sha256,
        }
        fields = vars(receipt) | {"send": evidence, "raw_reply": sent.raw.decode("latin-1")}
        reply = {"status": "sent", **vars(receipt)}
        for attempt in range(self.save_attempts):
            if attempt:
                await asyncio.sleep(self.save_pause)
            try:
                await self.twin.change("bookings", load_id, _save(send_id, fields, self.now()))
                return reply
            except TwinUnavailable:
                continue
        log.error(
            "Booking receipt not saved for %s: state=%s sha256=%s",
            load_id,
            receipt.state,
            sent.sha256,
        )
        return reply | {"status": "receipt_not_saved", "send": evidence}


def recheck(load: Load | None, booking: Data, now: datetime, blocked: frozenset[str]) -> str | None:
    """Why the load can no longer be booked at this rate, or None if it still can (INV-1)."""
    if load is None:
        return "load_gone"
    if not is_offerable(load, now, blocked):
        return "load_not_open"
    if not same_shipment(load, booking.get("load")):
        return "shipment_changed"
    if load.max_rate is None or load.max_rate < booking["rate"]:
        return "ceiling_below_rate"
    return None


def classify(sent: Sent, load_id: str) -> Receipt:
    """Section 10. FAILED only if the TMS refused or no byte left; anything unclear is UNKNOWN."""
    if sent.step in ("build", "connect"):
        return Receipt("FAILED", reason="not_sent")
    if sent.reply is None:
        return Receipt("UNKNOWN", reason="no_complete_reply")
    if sent.reply.error is not None:
        code = sent.reply.error.code
        return Receipt("FAILED" if code in NOTHING_CREATED else "UNKNOWN", reason=code.lower())
    records = sent.reply.records
    record = records[0] if len(records) == 1 else {}
    status, reference = record.get("STATUS"), record.get("BOOKING_REF") or None
    if (
        record.get("LOAD_ID") != load_id
        or reference is None
        or status not in RECEIPT_STATES
        or parse_timestamp(record.get("TIMESTAMP")) is None
    ):
        return Receipt("UNKNOWN", "unexpected_receipt", reference, status)
    return Receipt(RECEIPT_STATES[status], None, reference, status)


def _save(send_id: str, fields: Data, now: datetime) -> Edit:
    """Write the receipt once. A save that timed out but landed is not written twice."""

    def edit(current: Data | None) -> tuple[Data | None, None]:
        row = current or {}
        events = row.get("events", [])
        if any(event.get("send_id") == send_id and event["action"] == "sent" for event in events):
            return None, None
        # The event keeps the whole receipt, raw bytes included, because a later
        # reservation of a freed load starts the row's own fields afresh (INV-10).
        detail = {"send_id": send_id, **fields}
        return row | fields | {"events": with_event(row, now, "sent", detail)}, None

    return edit
