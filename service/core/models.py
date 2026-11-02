"""Load types, named after the PDF's fields. Only the TMS adapter knows the TMS's own names."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class Place:
    city: str
    state: str
    zip_code: str


@dataclass(frozen=True, kw_only=True)
class LoadSummary:
    """One load as a TMS search returns it."""

    load_id: str
    origin: Place
    destination: Place
    pickup_datetime: datetime | None
    equipment_type: str
    loadboard_rate: int | None
    miles: int | None
    status: str


@dataclass(frozen=True, kw_only=True)
class Load(LoadSummary):
    """One load in full detail, including the private ceiling."""

    delivery_datetime: datetime | None
    weight: int | None
    commodity_type: str
    num_of_pieces: int | None
    dimensions: str
    notes: str
    # Kept out of repr, so printing or logging a load cannot reveal the ceiling (INV-2).
    max_rate: int | None = field(repr=False)
