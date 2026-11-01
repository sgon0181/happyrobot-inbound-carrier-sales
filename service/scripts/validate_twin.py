"""LIVE entity contention on labelled synthetic rows, without TMS or email calls."""

import asyncio
import json
import statistics
import time
import uuid

from service.config import settings
from service.adapters.twin.client import Platform
from service.adapters.twin.repository import TwinRepository
from service.adapters.twin.bookings import TwinBookingStore
from service.core.booking import Booking, BookingConflict, State


def timings(samples):
    ordered = sorted(samples)
    return {
        "median_ms": round(statistics.median(ordered) * 1000, 1),
        "p95_ms": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))] * 1000, 1),
    }


async def main():
    repository = TwinRepository(Platform(settings()))
    store = TwinBookingStore(repository, live=False)
    probe = uuid.uuid4().hex
    calls = [str(uuid.uuid4()) for _ in range(16)]

    async def seed(cid):
        row = {
            "id": cid,
            "cohort": "synthetic",
            "mc": "000001",
            "started_at": time.time(),
            "last_activity": time.time(),
            "closed_at": time.time(),
            "rounds": 0,
            "outcome": "entity_contention_probe",
            "verified_until": 0,
        }
        assert await repository.cas("calls", cid, None, row)

    await asyncio.gather(*(seed(cid) for cid in calls))
    claim_times, update_times, parallel_times = [], [], []

    async def claim(index):
        started = time.monotonic()
        booking = Booking(
            uuid.uuid4().hex, calls[index], "SYNTHETIC-" + probe, "000001", 1000, "synthetic"
        )
        try:
            result, created = await store.create(booking, "contention", "identical")
            return result if created else None
        except BookingConflict:
            return None
        finally:
            claim_times.append(time.monotonic() - started)

    candidates = await asyncio.gather(*(claim(i) for i in range(8)))
    winners = [b for b in candidates if b]
    assert len(winners) == 1

    async def conditional():
        started = time.monotonic()
        result = await store.update(
            winners[0].id,
            {State.AGREED},
            state=State.UNKNOWN,
            reason="synthetic_entity_probe",
            review_required=True,
        )
        update_times.append(time.monotonic() - started)
        return result

    updates = await asyncio.gather(*(conditional() for _ in range(8)))
    assert sum(b is not None for b in updates) == 1

    async def independent(cid):
        started = time.monotonic()
        for value in range(1, 5):

            def change(state, call):
                call["probe_save"] = value

            await repository.update_call(cid, change, {})
        _, row = await repository.get("calls", cid)
        assert row["probe_save"] == 4
        parallel_times.append(time.monotonic() - started)

    wall_start = time.monotonic()
    await asyncio.gather(*(independent(cid) for cid in calls[8:]))
    parallel_wall = time.monotonic() - wall_start
    await repository.drain()
    result = {
        "label": "LIVE_INFRASTRUCTURE_SIMULATED_BUSINESS",
        "host": "FLY_MACHINE",
        "mode": "Authoritative entity rows and primary-key claims",
        "probe_id": probe,
        "claim_contenders": 8,
        "claim_winners": 1,
        "claim_latency": timings(claim_times),
        "conditional_contenders": 8,
        "conditional_winners": 1,
        "conditional_latency": timings(update_times),
        "parallel_calls": 8,
        "conditional_saves_per_independent_call": 4,
        "parallel_calls_completed": 8,
        "parallel_call_latency": timings(parallel_times),
        "parallel_wall_ms": round(parallel_wall * 1000, 1),
        "sum_individual_call_ms": round(sum(parallel_times) * 1000, 1),
        "live_tms_sends": 0,
        "emails": 0,
        "limit": (
            "Eight independent call-state sequences, not eight voice or integration calls. "
            "No multi-table transactions."
        ),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    from service.adapters.twin.client import PlatformError

    try:
        asyncio.run(main())
    except PlatformError as error:
        print(json.dumps({"status": "platform_error", "code": error.code, "detail": error.detail}))
        raise
