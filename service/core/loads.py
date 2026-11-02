"""Which loads may be offered. TMS search also returns PENDING loads, so each match is rechecked."""

from collections.abc import Iterable
from datetime import datetime

from service.core.models import LoadSummary

MAX_OFFERS = 3


def is_offerable(load: LoadSummary, now: datetime, excluded: frozenset[str] = frozenset()) -> bool:
    """Explicitly OPEN, picking up in the future, and not blocked or already reserved."""
    return (
        load.status == "OPEN"
        and load.pickup_datetime is not None
        and load.pickup_datetime > now
        and load.load_id not in excluded
    )


def select_offers[L: LoadSummary](
    loads: Iterable[L],
    now: datetime,
    excluded: frozenset[str] = frozenset(),
    *,
    equipment: str | None = None,
    origin_state: str | None = None,
    dest_state: str | None = None,
) -> list[L]:
    """Up to MAX_OFFERS loads that are offerable and on the asked lane, earliest pickup first."""
    wanted = (equipment, origin_state, dest_state)
    offers = [
        load for load in loads if is_offerable(load, now, excluded) and _on_lane(load, *wanted)
    ]
    offers.sort(key=lambda load: load.pickup_datetime or now)  # always set once offerable
    return offers[:MAX_OFFERS]


def _on_lane(
    load: LoadSummary, equipment: str | None, origin_state: str | None, dest_state: str | None
) -> bool:
    """A criterion left as None matches anything."""
    pairs = (
        (equipment, load.equipment_type),
        (origin_state, load.origin.state),
        (dest_state, load.destination.state),
    )
    return all(wanted is None or wanted == actual for wanted, actual in pairs)
