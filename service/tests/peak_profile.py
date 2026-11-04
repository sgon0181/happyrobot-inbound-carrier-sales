"""Manual paced arrival experiment: python -m service.tests.peak_profile (about 40 seconds)."""

import asyncio
import json
import math
import time
from collections import Counter
from typing import Any
from unittest.mock import patch
from uuid import UUID

import httpx

from service.tests.fake_twin import FakeTwin
from service.tests.rig import AGENT, rig


async def profile(arrivals: int, gap: float) -> dict[str, Any]:
    twin = FakeTwin.twin
    with patch.object(FakeTwin, "twin", lambda fake: twin(fake, pace=0.25)):
        fixture = rig(fmcsa_delay=0.01)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=fixture.client.app), base_url="http://fixture"
    ) as api:

        async def verify(i: int) -> tuple[str, float]:
            await asyncio.sleep(i * gap)
            start = time.monotonic()
            response = await api.post(
                "/carriers/verify",
                headers={"Authorization": f"Bearer {AGENT}"},
                json={"mc": str(170000 + i), "run_id": str(UUID(int=i + 1, version=4))},
            )
            return response.json()["status"], time.monotonic() - start

        async def read_desk() -> None:
            await asyncio.sleep(0.1)
            await fixture.dashboard.snapshot()

        callers = asyncio.gather(*(verify(i) for i in range(arrivals)))
        results, _ = await asyncio.gather(callers, read_desk())
        timings = sorted(seconds for _, seconds in results)
        return {
            "arrivals": arrivals,
            "spacing_seconds": gap,
            "outcomes": dict(Counter(status for status, _ in results)),
            "p95_seconds": round(timings[math.ceil(arrivals * 0.95) - 1], 2),
            "statements": len(fixture.twin.statements),
        }


async def main() -> None:
    for count, gap in [(8, 0.0), (15, 0.0), (15, 1.5), (30, 0.0)]:
        print(json.dumps(await profile(count, gap)), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
