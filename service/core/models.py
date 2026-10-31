"""Load types. These use the PDF's field names; the TMS adapter owns the mapping."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Place:
    city: str
    state: str
    zip_code: str

    def __str__(self):
        return f"{self.city}, {self.state} {self.zip_code}".strip()


@dataclass(frozen=True)
class BookingEvidence:
    """Identifying fields, if the TMS ever exposes them on a read. None do today."""

    reference: str
    mc: str
    agreed_rate: int


@dataclass(frozen=True)
class LoadSummary:
    load_id: str
    origin: Place
    destination: Place
    pickup_datetime: datetime | None
    equipment_type: str
    loadboard_rate: int | None
    miles: int | None
    status: str


@dataclass(frozen=True)
class Load(LoadSummary):
    delivery_datetime: datetime | None
    weight: int | None
    commodity_type: str
    num_of_pieces: int | None
    dimensions: str
    notes: str
    # Candidate mapping from MAX_BUY (D-10). Kept out of repr so it cannot reach a log.
    max_rate: int | None = field(repr=False)
    evidence: BookingEvidence | None = None
