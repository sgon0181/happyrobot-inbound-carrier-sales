"""The operations snapshot: calls and bookings as stored, each call's derived outcome, and KPIs.

Read only. Outcomes are computed when read, never stored twice (architecture section 7),
and KPIs count real calls only (D-21). The snapshot is cached for 5 seconds, because
Twin allows about 4 statements a second and every open dashboard polls it.
"""

import asyncio
import statistics
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from service.adapters.twin import Data, Row, Twin
from service.calls import Reply

CACHE = timedelta(seconds=5)
IDLE = timedelta(minutes=30)  # a call quiet this long ended without closing
SYNTHETIC_ROWS = frozenset({"selftest-20261103-deploy"})  # a deploy check stamped real
LANE = ("equipment", "origin_state", "dest_state")
HOLDS_NOTHING = "UNCLAIMED"  # a voided claim on a load nobody reserved: not a reservation
CALL_FIELDS = (
    *("started_at", "last_activity", "closed_at", "mc", "carrier_name", "eligible"),
    *("verified_at", "search", "offers", "rounds", "agreement", "summary", "events"),
    *("ended_at", "ended_by", "duration_seconds"),
)  # never the code hash
BOOKING_FIELDS = (
    *("state", "call_id", "mc", "rate", "cohort", "rep", "reference", "tms_status"),
    *("raw_reply", "send", "reason", "events", "load"),
)


class Dashboard:
    def __init__(
        self,
        twin: Twin,
        *,
        live_booking: bool,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.twin, self.now, self.live_booking = twin, now, live_booking
        self._cached: tuple[datetime, Reply] | None = None
        self._refreshing = asyncio.Lock()
        self._generation = 0  # rises on every forget, so a refresh begun before it is not kept

    async def snapshot(self) -> Reply:
        """Two statements, one per table, at most once every 5 seconds.

        Dashboards that ask together share one refresh, so they cannot crowd out voice
        requests on Twin's 4 statements a second.
        """
        async with self._refreshing:
            now = self.now()
            if self._cached is not None and now < self._cached[0]:
                return self._cached[1]
            generation = self._generation
            calls = await self.twin.get_all("calls")
            bookings = await self.twin.get_all("bookings")
            snapshot = build_snapshot(calls, bookings, now, live_booking=self.live_booking)
            if generation == self._generation:  # no rep action landed while it was read
                self._cached = (now + CACHE, snapshot)
            return snapshot

    def forget(self) -> None:
        """Drop the cached snapshot, so a rep sees their own action at once."""
        self._generation += 1
        self._cached = None


def build_snapshot(
    calls: dict[str, Row], bookings: dict[str, Row], now: datetime, *, live_booking: bool = False
) -> Reply:
    held = handoffs(bookings)
    shown = [_call(key, row, held.get(key), now) for key, row in calls.items()]
    shown.sort(key=lambda call: call["started_at"] or "", reverse=True)
    queue = [_booking(key, row, calls) for key, row in bookings.items()]
    return {
        "status": "ok",
        "live_booking": live_booking,
        "generated_at": now.isoformat(),
        "kpis": kpis(shown),
        "turned_away": turned_away(shown),
        "bookings": [booking for booking in queue if booking["state"] != HOLDS_NOTHING],
        "calls": shown,
    }


def handoffs(bookings: dict[str, Row]) -> dict[str, Data]:
    """Each call's reservation, as the booking rows' events tell it.

    A freed load can be reserved again by another call, so a row's current state belongs
    to its latest reservation, and an earlier one ends where its events left it. Every
    booking event that changes the state records the new state.
    """
    found: dict[str, Data] = {}
    for load_id, row in bookings.items():
        current: Data | None = None
        for event in row.data.get("events", []):
            if event.get("action") == "reserved":
                current = {"load_id": load_id, "state": "RESERVED", "submitted": False}
                found[str(event.get("call_id"))] = current
            elif current is not None and "state" in event:
                current["state"] = event["state"]
                current["submitted"] |= event["state"] == "SUBMITTING"
        if current is not None:  # the row itself is the authority on its latest reservation
            current["state"] = row.data.get("state")
    return found


def outcome(data: Data, booking: Data | None, now: datetime) -> str:
    """The call's outcome, by the first rule that applies (architecture section 7)."""
    if booking is not None:
        return "agreed_pending_rep"
    if data.get("outcome"):
        return str(data["outcome"])
    if data.get("closed_at"):
        return "ended_without_agreement"
    if data.get("ended_at"):  # the call ended before the agent closed it
        return "ended_without_close"
    last = _time(data.get("last_activity"))
    if last is not None and now - last >= IDLE:
        return "end_not_recorded"  # no end arrived: inferred from 30 quiet minutes
    return "in_progress"


def code_passed(data: Data) -> bool:
    """Whether the call ever passed its code. A later MC change clears verified_at but
    not the milestone, which its events keep, so the northstar's denominator holds.
    """
    events = data.get("events") or []
    passed = any((e.get("action"), e.get("status")) == ("verify_code", "verified") for e in events)
    return passed or bool(data.get("verified_at"))


def kpis(calls: list[Data]) -> Data:
    """Section 14's measures over real calls. PENDING is never counted as confirmed."""
    real = [call for call in calls if call["cohort"] == "real"]
    handed = [call["booking"] for call in real if call["booking"] is not None]
    waits = [wait for call in real if (wait := _first_offer_seconds(call)) is not None]
    return {
        "calls": len(real),
        "code_passed": _count(real, "code_passed"),
        **_handoff_kpis(handed, _count(real, "code_passed")),
        "outcomes": dict(Counter(call["outcome"] for call in real)),
        "median_seconds_to_first_offer": statistics.median(waits) if waits else None,
        "closed_with_summary": sum(_has_closing_notes(call) for call in real),
        "ends_reported": _count(real, "ended_at"),
        "synthetic_calls": len(calls) - len(real),
    }


def _has_closing_notes(call: Data) -> bool:
    return bool(call["closed_at"] and str(call.get("summary") or "").strip())


def _handoff_kpis(handed: list[Data], passed: int) -> Data:
    """The northstar, reserved handoffs per code-passed call (D-15), and what followed."""
    states = Counter(booking["state"] for booking in handed)
    return {
        "handoffs": len(handed),
        "northstar": round(len(handed) / passed, 3) if passed else None,
        "rep_confirmed": _count(handed, "submitted"),
        "tms_acknowledged": states["ACK_PENDING"],
        "tms_confirmed": states["CONFIRMED"],
        "unknown": states["UNKNOWN"],
    }


def turned_away(calls: list[Data]) -> list[Data]:
    """Lanes real carriers asked for when nothing matched (D-13), most asked first."""
    asked = Counter(
        tuple((call["search"] or {}).get(term) for term in LANE)
        for call in calls
        if call["cohort"] == "real" and call["outcome"] == "no_match"
    )
    return [dict(zip(LANE, lane, strict=True)) | {"calls": n} for lane, n in asked.most_common()]


def _call(key: str, row: Row, booking: Data | None, now: datetime) -> Data:
    data = row.data
    cohort = "synthetic" if key in SYNTHETIC_ROWS else data.get("cohort")
    fields = {name: data.get(name) for name in CALL_FIELDS}
    derived = {
        "cohort": cohort,
        "code_passed": code_passed(data),
        "outcome": outcome(data, booking, now),
        "booking": booking,
    }
    return {"id": key, "version": row.version, **fields, **derived}


def _booking(key: str, row: Row, calls: dict[str, Row]) -> Data:
    call = calls.get(str(row.data.get("call_id")))
    matched = call is not None and call.data.get("mc") == row.data.get("mc")
    carrier = call.data.get("carrier_name") if matched and call is not None else None
    return {"load_id": key, "version": row.version, "carrier_name": carrier} | {
        name: row.data.get(name) for name in BOOKING_FIELDS
    }


def _first_offer_seconds(call: Data) -> float | None:
    """Seconds from first recorded service activity to the first matched search, not speech."""
    found = [
        event.get("at")
        for event in call["events"] or []
        if (event.get("action"), event.get("status")) == ("find_loads", "found")
    ]
    started, first = _time(call["started_at"]), _time(found[0] if found else None)
    return None if started is None or first is None else (first - started).total_seconds()


def _count(rows: list[Data], name: str) -> int:
    return sum(1 for row in rows if row[name])


def _time(text: object) -> datetime | None:
    return datetime.fromisoformat(text) if isinstance(text, str) and text else None
