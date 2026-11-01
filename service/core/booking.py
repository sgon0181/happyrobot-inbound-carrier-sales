"""Tentative bookings (architecture 6.6, D-8).

Once a rate is agreed, the service sends LOAD_BOOK once while the carrier is on
the call and records the actual reply. The rep's decision is a separate local
fact. Nothing here resends a booking, and nothing counts as confirmed without
authoritative TMS evidence (INV-7).
"""

import asyncio
from dataclasses import dataclass, replace, field
from datetime import datetime, timezone
import json
import logging
from enum import Enum
import hashlib
from typing import Protocol
import uuid

from service.core.ports import BookingOutcome, BookingReceipt, TmsUnavailable


class State(Enum):
    AGREED = "AGREED"
    SUBMITTING = "SUBMITTING"
    ACK_PENDING = "ACK_PENDING"
    CONFIRMED = "CONFIRMED"
    UNKNOWN = "UNKNOWN"
    FAILED = "FAILED"


class RepDecision(Enum):
    AWAITING = "awaiting"
    CONFIRMED = "confirmed"
    DECLINED = "declined"


ACTIVE = frozenset(state for state in State if state is not State.FAILED)
REVIEWABLE = frozenset({State.ACK_PENDING, State.UNKNOWN})
RESULT_STATES = {
    BookingOutcome.ACK_PENDING: State.ACK_PENDING,
    BookingOutcome.CONFIRMED: State.CONFIRMED,
    BookingOutcome.REJECTED: State.FAILED,
    BookingOutcome.UNKNOWN: State.UNKNOWN,
}


@dataclass(frozen=True)
class Booking:
    id: str
    call_id: str
    load_id: str
    mc: str
    rate: int
    agreement_version: str
    state: State = State.AGREED
    write_intent_id: str | None = None
    reference: str | None = None
    tms_status: str | None = None
    raw_reply: str | None = None
    rep_decision: RepDecision = RepDecision.AWAITING
    rep: str | None = None
    review_required: bool = False
    reason: str | None = None
    diagnostic: dict = field(default_factory=dict, repr=False)
    persistence_pending: bool = False


class BookingConflict(Exception):
    """The load or call already has an active booking (INV-6)."""


class OperationConflict(Exception):
    """An operation ID was reused with different inputs (INV-9)."""


class BookingStore(Protocol):
    """Durable coordination. T-1 decides how Twin provides these two guarantees."""

    async def create(self, booking: Booking, operation_id: str, fingerprint: str) -> tuple:
        """Atomically claim the load and record the operation.

        Returns (booking, created). A repeated operation returns its existing
        booking with created False. Raises BookingConflict or OperationConflict.
        """

    async def update(self, booking_id: str, expected: frozenset, **changes) -> Booking | None:
        """Apply changes only if the state is still expected. Returns None otherwise."""

    async def get(self, booking_id: str) -> Booking: ...

    async def in_states(self, states: frozenset) -> list: ...

    async def blocked_load_ids(self) -> frozenset: ...


class InMemoryBookingStore:
    """For tests and local runs only. It says nothing about Twin."""

    def __init__(self):
        self.bookings = {}
        self.operations = {}

    async def create(self, booking, operation_id, fingerprint):
        key = (booking.call_id, operation_id)
        if key in self.operations:
            known_fingerprint, booking_id = self.operations[key]
            if known_fingerprint != fingerprint:
                raise OperationConflict("Operation ID reused with different inputs.")
            return self.bookings[booking_id], False
        for other in self.bookings.values():
            if other.state in ACTIVE and booking.load_id == other.load_id:
                raise BookingConflict("Load already has an active booking.")
            if other.state in ACTIVE and booking.call_id == other.call_id:
                raise BookingConflict("Call already has an active booking.")
        self.bookings[booking.id] = booking
        self.operations[key] = (fingerprint, booking.id)
        return booking, True

    async def update(self, booking_id, expected, **changes):
        booking = self.bookings[booking_id]
        if booking.state not in expected:
            return None
        if 'rep_decision' in changes and booking.rep_decision not in {RepDecision.AWAITING,changes['rep_decision']}:
            raise ValueError('The rep has already decided.')
        self.bookings[booking_id] = replace(booking, **changes)
        return self.bookings[booking_id]

    async def get(self, booking_id):
        return self.bookings[booking_id]

    async def in_states(self, states):
        return [booking for booking in self.bookings.values() if booking.state in states]

    async def blocked_load_ids(self):
        return frozenset(b.load_id for b in self.bookings.values() if b.state in ACTIVE)


def agent_view(booking):
    """The only booking fields the voice agent may see.

    ACK_PENDING and UNKNOWN read the same, so the carrier never hears a stronger
    claim than we can prove. No reference, raw reply or internal state.
    """
    if booking.state is State.FAILED:
        return {"status": "not_booked", "reason": booking.reason}
    if booking.state in (State.AGREED, State.SUBMITTING):
        return {"status": "in_progress"}
    return {"status": "senior_review", "agreed_rate": booking.rate}


class BookingService:
    def __init__(self, store, tms, new_id=lambda: str(uuid.uuid4())):
        self.store = store
        self.tms = tms
        self.new_id = new_id
        self.pending = set()

    async def request(self, *, call_id, operation_id, load_id, mc, rate, agreement_version, deadline=None):
        """Create the booking, recheck the load, send once, and record the actual reply."""
        if type(rate) is not int or rate <= 0:
            raise ValueError("Use a positive whole rate.")
        fingerprint = hashlib.sha256(
            f"{load_id}|{mc}|{rate}|{agreement_version}".encode()
        ).hexdigest()
        booking = Booking(self.new_id(), call_id, load_id, mc, rate, agreement_version)
        booking, created = await self.store.create(booking, operation_id, fingerprint)
        if not created:
            return booking
        task = asyncio.create_task(self._submit(booking, deadline))
        self.pending.add(task)
        task.add_done_callback(self.pending.discard)
        return await asyncio.shield(task)

    async def _fail(self, booking, reason):
        updated = await self.store.update(
            booking.id, frozenset({State.AGREED}), state=State.FAILED, reason=reason
        )
        return updated or await self.store.get(booking.id)

    async def _submit(self, booking, deadline=None):
        if not self.tms.booking_enabled:
            return await self._fail(booking, "live_booking_disabled")
        try:
            load = await self.tms.get(booking.load_id)
        except TmsUnavailable:
            return await self._fail(booking, "tms_unavailable")
        if load is None or load.status != "OPEN":
            return await self._fail(booking, "load_gone")
        if load.pickup_datetime is None or load.pickup_datetime <= datetime.now(timezone.utc):
            return await self._fail(booking, "pickup_ineligible")
        if load.max_rate is None:
            return await self._fail(booking, "ceiling_unavailable")
        if booking.rate > load.max_rate:
            return await self._fail(booking, "ceiling_fell")
        if deadline is not None and deadline-asyncio.get_running_loop().time()<6:
            return await self._fail(booking,"deadline_before_send")

        # The intent must be durable before the write can happen.
        claimed = await self.store.update(
            booking.id, frozenset({State.AGREED}),
            state=State.SUBMITTING, write_intent_id=self.new_id(),
        )
        if claimed is None:
            return await self.store.get(booking.id)
        if deadline is not None and deadline-asyncio.get_running_loop().time()<5:
            recorded=await self.store.update(booking.id,frozenset({State.SUBMITTING}),
                state=State.FAILED,reason='deadline_before_send',
                diagnostic={'send_started':False,'phase':'intent_saved'})
            return recorded or await self.store.get(booking.id)
        kwargs={'intent_id':claimed.write_intent_id} if getattr(self.tms,'accepts_intent_id',False) else {}
        receipt = await self.tms.book(booking.load_id, booking.mc, booking.rate,**kwargs)
        return await self._record(booking.id, receipt, claimed)

    async def _record(self, booking_id, receipt, fallback=None):
        for attempt in range(3):
            try:
                return await self._record_once(booking_id, receipt)
            except Exception:
                try:
                    saved = await self.store.get(booking_id)
                    if (saved.state in {State.ACK_PENDING, State.CONFIRMED}
                            and saved.reference == receipt.reference):
                        return saved
                except Exception:
                    pass
                await asyncio.sleep(.05 * attempt)
        # This restricted service log is the INV-10 fallback. No outbound AUTH,
        # expected OTP, ceiling or contact is ever included in this event.
        logging.getLogger("receipt_evidence").error(json.dumps({
            "event": "receipt_persistence_failure", "booking_id": booking_id,
            "outcome": receipt.outcome.value, "reference": receipt.reference,
            "tms_status": receipt.tms_status, "raw_reply": receipt.raw_reply,
            "diagnostic": receipt.diagnostic,
        }))
        booking = fallback or await self.store.get(booking_id)
        return replace(booking, state=RESULT_STATES[receipt.outcome], reference=receipt.reference,
                       tms_status=receipt.tms_status, raw_reply=receipt.raw_reply,
                       diagnostic=receipt.diagnostic, review_required=True, persistence_pending=True)

    async def _record_once(self, booking_id, receipt):
        state = RESULT_STATES[receipt.outcome]
        recorded = await self.store.update(
            booking_id, frozenset({State.SUBMITTING}),
            state=state,
            reference=receipt.reference,
            tms_status=receipt.tms_status,
            raw_reply=receipt.raw_reply,
            reason=receipt.reason,
            review_required=state is State.UNKNOWN,
            diagnostic=receipt.diagnostic,
        )
        if recorded is not None:
            return recorded
        # A late reply never overwrites newer state, but it is kept for the operator.
        booking = await self.store.get(booking_id)
        late = await self.store.update(
            booking_id, frozenset({State.UNKNOWN}),
            state=state if receipt.outcome in {BookingOutcome.ACK_PENDING,BookingOutcome.CONFIRMED}
                           and (not booking.reference or booking.reference==receipt.reference) else State.UNKNOWN,
            reference=booking.reference or receipt.reference,
            raw_reply=receipt.raw_reply or booking.raw_reply,
            tms_status=receipt.tms_status or booking.tms_status,
            diagnostic=receipt.diagnostic or booking.diagnostic,
            review_required=True,
            reason="late_reply",
        )
        return late or booking

    async def recover(self):
        """After a restart: AGREED sent nothing, but SUBMITTING may have. Never resends."""
        recovered = []
        for booking in await self.store.in_states(frozenset({State.AGREED})):
            recovered.append(await self._fail(booking, "interrupted_before_send"))
        for booking in await self.store.in_states(frozenset({State.SUBMITTING})):
            proof=self.tms.recover_receipt(booking) if hasattr(self.tms,'recover_receipt') else None
            if proof:
                recovered.append(await self._record(booking.id,proof,booking))
                continue
            updated = await self.store.update(
                booking.id, frozenset({State.SUBMITTING}),
                state=State.UNKNOWN, review_required=True, reason="interrupted_send",
            )
            recovered.append(updated or await self.store.get(booking.id))
        return recovered

    async def _decide(self, booking_id, decision, rep, **changes):
        booking = await self.store.get(booking_id)
        if booking.state not in REVIEWABLE | {State.CONFIRMED}:
            raise ValueError("This booking is not awaiting the rep.")
        if booking.rep_decision not in (RepDecision.AWAITING, decision):
            raise ValueError("The rep has already decided.")
        updated = await self.store.update(
            booking_id, frozenset({booking.state}), rep_decision=decision, rep=rep, **changes
        )
        return updated or await self.store.get(booking_id)

    async def confirm(self, booking_id, rep):
        """Record the rep's confirmation. Never writes to the TMS."""
        if (await self.store.get(booking_id)).state not in {State.ACK_PENDING, State.CONFIRMED}:
            raise ValueError("A matching acknowledgement is required before rep confirmation.")
        return await self._decide(booking_id, RepDecision.CONFIRMED, rep)

    async def decline(self, booking_id, rep):
        """Record the decline. With no cancel, the load stays blocked and flagged."""
        return await self._decide(
            booking_id, RepDecision.DECLINED, rep, review_required=True, reason="needs_release"
        )

    def _matches(self, booking, evidence):
        return (
            evidence is not None
            and evidence.mc == booking.mc
            and evidence.agreed_rate == booking.rate
            and (booking.reference is None or evidence.reference == booking.reference)
        )

    async def reconcile(self, booking_id):
        """Read-only check. A bare status never confirms, and nothing is ever sent."""
        booking = await self.store.get(booking_id)
        if booking.state not in REVIEWABLE:
            return booking
        try:
            load = await self.tms.get(booking.load_id)
        except TmsUnavailable:
            return booking

        status = load.status if load else "NOT_FOUND"
        expected = frozenset({booking.state})
        if load and status == "BOOKED" and self._matches(booking, load.evidence):
            confirmed = await self.store.update(
                booking_id, expected, state=State.CONFIRMED,
                reference=load.evidence.reference, tms_status=status, reason=None,
            )
            return confirmed or await self.store.get(booking_id)

        steady = booking.state is State.ACK_PENDING and status == "PENDING"
        updated = await self.store.update(
            booking_id, expected,
            tms_status=status,
            review_required=booking.review_required or not steady,
            reason=booking.reason if steady else (booking.reason or "unexpected_tms_status"),
        )
        return updated or await self.store.get(booking_id)
