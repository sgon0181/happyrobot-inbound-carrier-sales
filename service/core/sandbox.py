"""Temporary permission for challenge sandbox sends, separate from carrier identity."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any


def utc_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.utcoffset() == timedelta(0) else None
    except ValueError:
        return None


@dataclass(frozen=True)
class SandboxScope:
    mc: str
    since: datetime
    until: datetime

    def active(self, now: datetime) -> bool:
        return self.since <= now < self.until

    def source(self, data: dict[str, Any]) -> bool:
        return (
            data.get("mc") == self.mc
            and data.get("cohort") == "synthetic"
            and data.get("otp_route") == "demo_inbox"
        )

    def includes(self, value: object) -> bool:
        at = utc_time(value)
        return at is not None and self.since <= at < self.until

    def permits(self, call: dict[str, Any], booking: dict[str, Any], now: datetime) -> bool:
        """Use the latest reservation's own event, never a recent edit to an old hold."""
        reserved: dict[str, Any] = next(
            (
                event
                for event in reversed(booking.get("events", []))
                if event.get("action") == "reserved"
            ),
            {},
        )
        return (
            self.active(now)
            and self.source(call)
            and self.source(booking)
            and self.includes(call.get("started_at"))
            and self.includes(reserved.get("at"))
            and reserved.get("call_id") == booking.get("call_id")
        )


def read_scope(mc: str, since: str, until: str) -> SandboxScope | None:
    """Absent settings keep sends off; partial or excessive windows stop startup."""
    if not any((mc, since, until)):
        return None
    start, end = utc_time(since), utc_time(until)
    if (
        not mc
        or start is None
        or end is None
        or not timedelta(0) < end - start <= timedelta(hours=48)
    ):
        raise ValueError("Sandbox sends require an MC and a UTC window of at most 48 hours")
    return SandboxScope(mc, start.astimezone(UTC), end.astimezone(UTC))
