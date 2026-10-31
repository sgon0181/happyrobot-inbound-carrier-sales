"""What the core needs from the TMS, without depending on the wire protocol."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from service.core.models import Load


class TmsUnavailable(Exception):
    """A read failed after its bounded retries."""


class BookingOutcome(Enum):
    ACK_PENDING = "ack_pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class BookingReceipt:
    outcome: BookingOutcome
    reference: str | None = None
    tms_status: str | None = None
    raw_reply: str | None = None
    reason: str | None = None


class TmsPort(Protocol):
    booking_enabled: bool

    async def get(self, load_id: str) -> Load | None: ...

    async def book(self, load_id: str, mc: str, rate: int) -> BookingReceipt: ...
