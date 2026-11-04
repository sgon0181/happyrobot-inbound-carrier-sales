"""Which loads may be offered, and what the agent may say about them.

TMS search also returns PENDING loads, so each match is rechecked.
"""

import re
from collections.abc import Iterable
from datetime import datetime, tzinfo
from typing import TypedDict

from service.core.models import Load, LoadSummary, Place

MAX_OFFERS = 3


class Search(TypedDict):
    """What the carrier asked for. None matches anything."""

    equipment: str | None
    origin_state: str | None
    dest_state: str | None


# What a caller may say, mapped to the TMS's equipment codes.
EQUIPMENT_NAMES = {
    "dry van": "DRY_VAN",
    "van": "DRY_VAN",
    "reefer": "REEFER",
    "refrigerated": "REEFER",
    "flatbed": "FLATBED",
    "flat bed": "FLATBED",
    "step deck": "STEP_DECK",
    "stepdeck": "STEP_DECK",
    "power only": "POWER_ONLY",
}
_STATE = re.compile(r"[A-Z]{2}")


def search_terms(
    equipment: str | None, origin_state: str | None, dest_state: str | None
) -> Search | None:
    """Normalized terms, or None if a term is unreadable or none is given. Blank means unset."""
    try:
        terms = Search(
            equipment=_equipment(equipment),
            origin_state=_state(origin_state),
            dest_state=_state(dest_state),
        )
    except ValueError:
        return None
    return terms if any(terms.values()) else None


def public_view(load: Load, offer: int, *, display_timezone: tzinfo) -> dict[str, object]:
    """What the agent may say about a load, as an explicit allowlist (INV-2).

    max_rate and any field added later stay private by default. The posted rate is left
    out too, so the agent quotes our offer and never anchors the carrier above it.
    """
    return {
        "load_id": load.load_id,
        "origin": _place(load.origin),
        "destination": _place(load.destination),
        "pickup_datetime": load.pickup_datetime and load.pickup_datetime.isoformat(),
        "delivery_datetime": load.delivery_datetime and load.delivery_datetime.isoformat(),
        "pickup_time_display": _speech_time(load.pickup_datetime, display_timezone),
        "delivery_time_display": _speech_time(load.delivery_datetime, display_timezone),
        "equipment_type": load.equipment_type,
        "miles": load.miles,
        "weight": load.weight,
        "commodity_type": load.commodity_type,
        "num_of_pieces": load.num_of_pieces,
        "dimensions": load.dimensions,
        "notes": load.notes,
        "offer": offer,
    }


def _speech_time(value: datetime | None, display_timezone: tzinfo) -> str | None:
    """The App's Central Time policy; the adapter's source-UTC assumption still applies."""
    if value is None:
        return None
    local = value.astimezone(display_timezone)
    hour = local.hour % 12 or 12
    period = "AM" if local.hour < 12 else "PM"
    return (
        f"{local:%B} {local.day} at {hour}:{local.minute:02d} {period} Central ({local.tzname()})"
    )


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
    limit: int = MAX_OFFERS,
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
    return offers[:limit]


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


def _equipment(text: str | None) -> str | None:
    if text is None or not text.strip():
        return None
    code = EQUIPMENT_NAMES.get(re.sub(r"[\s_-]+", " ", text.strip().lower()))
    if code is None:
        raise ValueError("Unknown equipment.")
    return code


def _state(text: str | None) -> str | None:
    if text is None or not text.strip():
        return None
    code = text.strip().upper()
    if not _STATE.fullmatch(code):
        raise ValueError("Use a two-letter state.")
    return code


def _place(place: Place) -> str:
    return f"{place.city}, {place.state}"


def shipment_terms(load: Load) -> dict[str, object]:
    """Carrier-facing shipment conditions whose change requires new consent."""
    return {
        "origin": {
            "city": load.origin.city,
            "state": load.origin.state,
            "zip": load.origin.zip_code,
        },
        "destination": {
            "city": load.destination.city,
            "state": load.destination.state,
            "zip": load.destination.zip_code,
        },
        "pickup_datetime": load.pickup_datetime and load.pickup_datetime.isoformat(),
        "delivery_datetime": load.delivery_datetime and load.delivery_datetime.isoformat(),
        "equipment_type": load.equipment_type,
        "miles": load.miles,
        "weight": load.weight,
        "commodity_type": load.commodity_type,
        "num_of_pieces": load.num_of_pieces,
        "dimensions": load.dimensions,
        "notes": load.notes,
    }


def reservation_view(load: Load) -> dict[str, object]:
    """Capture exactly what the rep reviews, including the separately identified posted rate."""
    return shipment_terms(load) | {"loadboard_rate": load.loadboard_rate}


def same_shipment(load: Load, recorded: object) -> bool:
    """An incomplete pre-proposal quote cannot authorize an irreversible send."""
    return isinstance(recorded, dict) and all(
        key in recorded and recorded[key] == value for key, value in shipment_terms(load).items()
    )
