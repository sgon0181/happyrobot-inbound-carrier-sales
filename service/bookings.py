"""Reservations: one booking row per load, keyed by load ID (D-24, architecture section 10).

Creating the row is the reservation, so the primary key lets only one call hold a load.
Nothing here talks to the TMS. A rep's confirm, decline and reconcile are in rep_actions.
"""

from collections.abc import Iterable
from datetime import datetime

from service.adapters.twin import Data, Twin

FREE = frozenset({"FAILED", "RELEASED", "UNCLAIMED"})  # every other state holds the load


def agreement_recorded(call: Data | None, booking: Data, load_id: str) -> bool:
    """A durable hold can precede the call's agreement. A terminal recovery needs rep follow-up."""
    if not call or call.get("accepting") or call.get("agreement_needs_review"):
        return False
    agreement = call.get("agreement") or {}
    return (
        agreement.get("load_id") == load_id
        and agreement.get("mc") == booking.get("mc") == call.get("mc")
        and agreement.get("rate") == booking.get("rate")
    )


class Bookings:
    def __init__(self, twin: Twin) -> None:
        self.twin = twin

    async def held(self, load_ids: Iterable[str]) -> frozenset[str]:
        """The loads among these that a booking row holds."""
        rows = await self.twin.get_many("bookings", load_ids)
        return frozenset(key for key, row in rows.items() if row.data.get("state") not in FREE)

    async def reserve(
        self,
        load_id: str,
        *,
        claim_id: str,
        call_id: str,
        mc: str,
        rate: int,
        cohort: str,
        now: datetime,
        load: Data | None = None,
        otp_route: str | None = None,
    ) -> Data | None:
        """Hold the load for this claim. Returns the row if this call holds it, as stored,
        so a retry recovers the first attempt's rate and MC. None if another call holds it,
        or if the claim was voided.

        A freed row is reused, carrying its earlier events forward (section 10).
        """

        def edit(current: Data | None) -> tuple[Data | None, Data | None]:
            row = current or {}
            if claim_id in row.get("void_claims", []):
                return None, None
            if current is not None and row.get("state") not in FREE:
                return None, current if row.get("call_id") == call_id else None
            attempt = {"call_id": call_id, "claim_id": claim_id, "mc": mc, "rate": rate}
            data = new_booking(call_id, mc, rate, cohort) | {"claim_id": claim_id}
            data.update(load=load, otp_route=otp_route)
            data["void_claims"] = row.get("void_claims", [])
            data["events"] = with_event(
                row, now, "reserved", attempt | {"state": "RESERVED", "load": load}
            )
            return data, data

        return await self.twin.change("bookings", load_id, edit)

    async def void(
        self, load_id: str, *, claim_id: str, call_id: str, now: datetime
    ) -> Data | None:
        """Stop a claim from ever reserving, in the booking row's own versioned write.

        A request that claimed the load may still be about to reserve it, so reading first
        would race. Returns the row instead if the claim already reserved it, so the
        caller settles it rather than abandoning it.
        """

        def edit(current: Data | None) -> tuple[Data | None, Data | None]:
            row = current or {"state": "UNCLAIMED"}
            # Rows reserved before booking rows kept claim IDs belong to their call.
            legacy = "claim_id" not in row and row.get("call_id") == call_id
            if (row.get("claim_id") == claim_id or legacy) and row.get("state") not in FREE:
                return None, current
            voided = row.get("void_claims", [])
            if claim_id in voided:
                return None, None
            attempt = {"call_id": call_id, "claim_id": claim_id}
            events = with_event(row, now, "claim_voided", attempt)
            return row | {"void_claims": [*voided, claim_id], "events": events}, None

        return await self.twin.change("bookings", load_id, edit)


def with_event(row: Data, now: datetime, action: str, detail: Data) -> list[Data]:
    events = list(row.get("events", []))
    events.append({"seq": len(events) + 1, "at": now.isoformat(), "action": action, **detail})
    return events


def new_booking(call_id: str, mc: str, rate: int, cohort: str) -> Data:
    """A reservation: the carrier agreed and nothing has been sent (architecture section 7)."""
    return {
        "state": "RESERVED",
        "call_id": call_id,
        "mc": mc,
        "rate": rate,
        "cohort": cohort,
        "rep": None,
        "reference": None,
        "tms_status": None,
        "raw_reply": None,
        "send": {"step": None, "error": None, "bytes": 0, "sha256": None},
        "reason": None,
        "events": [],
    }
