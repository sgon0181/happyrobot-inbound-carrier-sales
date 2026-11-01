"""LIVE Twin contention, with explicitly synthetic business records and no TMS."""

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


async def main():
    client = Platform(settings())
    repo = TwinRepository(client)
    store = TwinBookingStore(repo, live=False)
    identity = uuid.uuid4().hex
    calls = [str(uuid.uuid4()) for _ in range(8)]

    def seed(data):
        for cid in calls:
            data["calls"][cid] = {
                "id": cid,
                "cohort": "synthetic",
                "mc": "138328",
                "started_at": time.time(),
                "last_activity": time.time(),
                "closed_at": time.time(),
                "rounds": 0,
                "outcome": "twin_contention_probe",
                "verified_until": 0,
            }

    await repo.update(seed)

    async def claim(index):
        b = Booking(
            uuid.uuid4().hex, calls[index], "SYNTHETIC-" + identity, "138328", 1000, "synthetic"
        )
        try:
            result, created = await store.create(b, "contention", "identical")
            return result if created else None
        except BookingConflict:
            return None

    candidates = await asyncio.gather(*(claim(i) for i in range(8)))
    winners = [b for b in candidates if b]
    assert len(winners) == 1

    async def conditional():
        return await store.update(
            winners[0].id,
            frozenset({State.AGREED}),
            state=State.UNKNOWN,
            reason="synthetic_contention_probe",
            review_required=True,
        )

    updates = await asyncio.gather(*(conditional() for _ in range(8)))
    assert sum(b is not None for b in updates) == 1
    if repo.pending:
        await asyncio.gather(*repo.pending)
    print(
        json.dumps(
            {
                "label": "LIVE",
                "business_records": "SIMULATED",
                "mode": "Twin canonical CAS fallback",
                "unique_claim_contenders": 8,
                "unique_claim_winners": len(winners),
                "conditional_update_contenders": 8,
                "conditional_update_winners": sum(b is not None for b in updates),
                "projection_errors": repo.projection_errors,
                "median_ms": round(statistics.median(client.latencies) * 1000, 1),
                "p95_ms": round(
                    sorted(client.latencies)[int(len(client.latencies) * 0.95)] * 1000, 1
                ),
                "live_tms_sends": 0,
                "probe_id": identity,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
