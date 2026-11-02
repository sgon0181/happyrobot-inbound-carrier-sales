"""Reservations: one booking row per load, keyed by load ID (D-24, architecture section 10).

Creating the row is the reservation, so the primary key lets only one call hold a load.
Nothing here talks to the TMS. Rep actions and LOAD_BOOK arrive in slice 4.
"""

from collections.abc import Iterable
from datetime import datetime

from service.adapters.twin import Data, Twin

FREE = frozenset({"FAILED", "RELEASED"})  # every other state holds the load, unknown ones too


class Bookings:
    def __init__(self, twin: Twin) -> None:
        self.twin = twin

    async def held(self, load_ids: Iterable[str]) -> frozenset[str]:
        """The loads among these that a booking row holds."""
        rows = await self.twin.get_many("bookings", load_ids)
        return frozenset(key for key, row in rows.items() if row.data.get("state") not in FREE)

    async def reserve(
        self, load_id: str, *, call_id: str, mc: str, rate: int, cohort: str, now: datetime
    ) -> bool:
        """Hold the load for this call. True if this call holds it, a repeat included.

        A freed row is reused, carrying its earlier events forward (section 10).
        """

        def edit(current: Data | None) -> tuple[Data | None, bool]:
            if current is not None and current.get("state") not in FREE:
                return None, current.get("call_id") == call_id
            events = list(current["events"]) if current else []
            events.append({"seq": len(events) + 1, "at": now.isoformat(), "action": "reserved"})
            return new_booking(call_id, mc, rate, cohort) | {"events": events}, True

        return await self.twin.change("bookings", load_id, edit)


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
