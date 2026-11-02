"""Reservations: one booking row per load, keyed by load ID (D-24, architecture section 10).

Creating the row is the reservation, so the primary key lets only one call hold a load.
Nothing here talks to the TMS. Rep actions and LOAD_BOOK arrive in slice 4.
"""

from collections.abc import Iterable

from service.adapters.twin import Twin

FREE = frozenset({"FAILED", "RELEASED"})  # every other state holds the load, unknown ones too


class Bookings:
    def __init__(self, twin: Twin) -> None:
        self.twin = twin

    async def held(self, load_ids: Iterable[str]) -> frozenset[str]:
        """The loads among these that a booking row holds."""
        rows = await self.twin.get_many("bookings", load_ids)
        return frozenset(key for key, row in rows.items() if row.data.get("state") not in FREE)
