"""Optional history and dashboard pressure for the offline paced full-journey probe."""

import asyncio
import time
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx

from service.call_state import new_call
from service.tests.fake_twin import FakeTwin
from service.tests.test_config import ENV


def seed(twin: FakeTwin, calls: int, bookings: int) -> None:
    now = datetime.now(UTC) - timedelta(days=1)
    for i in range(calls):
        row = new_call("synthetic", now)
        row.update(closed_at=now.isoformat(), ended_at=now.isoformat(), read_only=True)
        twin.tables["calls"][str(UUID(int=i + 10000, version=4))] = (1, row)
    for i in range(bookings):
        twin.tables["bookings"][f"LD7{i:04}"] = (
            1,
            {"state": "RELEASED", "events": [], "call_id": "historical", "read_only": True},
        )


async def poll(api: httpx.AsyncClient, snapshots: list[dict[str, Any]]) -> None:
    while True:
        start = time.monotonic()
        response = await api.get(
            "/ops/snapshot", headers={"Authorization": f"Bearer {ENV['OPS_API_KEY']}"}
        )
        body = response.json()
        snapshots.append(
            {
                "http": response.status_code,
                "status": body.get("status"),
                "calls": len(body.get("calls", [])),
                "seconds": round(time.monotonic() - start, 2),
            }
        )
        await asyncio.sleep(15)
