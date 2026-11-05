"""Optional offline full-flow saturation probe with actual Twin pacing and voice deadlines.

Run: python -m service.tests.full_profile --arrivals 12 --spacing 1.5 --think 3
All dependencies are fixtures. A caller stops at its first error without a final webhook,
so outstanding claims remain visible. No TMS booking command is issued.
"""

import argparse
import asyncio
import json
import math
import time
from collections import Counter
from typing import Any
from unittest.mock import patch
from uuid import UUID

import httpx

from service import main
from service.adapters.fmcsa import Fmcsa, FmcsaSettings
from service.config import load_settings
from service.core.approved_freight import MARKETS
from service.tests.fake_tms import FakeTMS, client_for, make_load
from service.tests.fake_twin import FakeTwin
from service.tests.profile_history import poll, seed
from service.tests.rig import FakeFmcsa
from service.tests.test_carrier_policy import ACTIVE
from service.tests.test_config import ENV
from service.tests.test_peak_shift import ORIGINS, SESSION, Inboxes, auth


async def profile(
    arrivals: int,
    spacing: float,
    think: float,
    *,
    historical_calls: int = 0,
    historical_bookings: int = 0,
    dashboard: bool = False,
) -> dict[str, Any]:
    twin, inbox = FakeTwin(), Inboxes()
    seed(twin, historical_calls, historical_bookings)
    snapshots: list[dict[str, Any]] = []
    carrier = FakeFmcsa([ACTIVE], delay=0.01)
    authority = Fmcsa(FmcsaSettings(api_key="fixture"), httpx.MockTransport(carrier.reply))
    outcomes: Counter[str] = Counter()
    timings: list[tuple[str, float]] = []
    records = [
        make_load(f"LD9{i:04}", ORIG_STATE=state, ORIG_CITY=MARKETS[state][0])
        for i, state in enumerate(ORIGINS[:arrivals])
    ]
    async with FakeTMS(records) as wire:
        with (
            patch.object(main, "Twin", lambda _: twin.twin(pace=0.25)),
            patch.object(main, "Fmcsa", lambda _: authority),
            patch.object(main, "CodeMailer", lambda _: inbox),
            patch.object(main, "TmsClient", lambda _: client_for(wire)),
        ):
            app = main.build(load_settings(ENV | {"CALL_COHORT": "real"}))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://fixture",
            headers=auth(ENV["AGENT_API_KEY"]),
        ) as api:

            async def arrive(i: int) -> float:
                await asyncio.sleep(i * spacing)
                start = time.monotonic()
                await _caller(api, inbox, outcomes, timings, i, think)
                return time.monotonic() - start

            refresh = asyncio.create_task(poll(api, snapshots)) if dashboard else None
            try:
                journeys = await asyncio.gather(*(arrive(i) for i in range(arrivals)))
            finally:
                if refresh:
                    refresh.cancel()
                    await asyncio.gather(refresh, return_exceptions=True)
        writes = sum(line.startswith("CMD:LOAD_BOOK|") for line in wire.requests)
    calls = [row for _, row in twin.tables["calls"].values()]
    return {
        "arrivals": arrivals,
        "spacing_seconds": spacing,
        "think_seconds": think,
        "outcomes": dict(outcomes),
        "sql_statements": len(twin.statements),
        "sql_kinds": dict(Counter(" ".join(sql.split()[:3]) for sql in twin.statements)),
        "journey_p95_seconds": _p95(journeys),
        "tool_p95_seconds": {
            path: _p95([elapsed for name, elapsed in timings if name == path])
            for path in dict(timings)
        },
        "booking_rows": len(twin.tables["bookings"]),
        "durable_holds": sum(
            row.get("state") == "RESERVED" for _, row in twin.tables["bookings"].values()
        ),
        "historical_calls": historical_calls,
        "historical_bookings": historical_bookings,
        "snapshot_reads": snapshots,
        "outstanding_claims": sum(bool(call.get("accepting")) for call in calls),
        "finalized_agreements": sum(bool(call.get("agreement")) for call in calls),
        "tms_booking_writes": writes,
    }


async def _caller(
    api: httpx.AsyncClient,
    inbox: Inboxes,
    outcomes: Counter[str],
    timings: list[tuple[str, float]],
    i: int,
    think: float,
) -> None:
    session = str(UUID(int=i + 1, version=4))
    SESSION.set(session)

    async def post(path: str, **body: Any) -> dict[str, Any]:
        start = time.monotonic()
        response = await api.post(path, json={"run_id": session, **body})
        timings.append((path, time.monotonic() - start))
        response.raise_for_status()
        data = dict(response.json())
        outcomes[f"{path}:{data.get('status')}"] += 1
        await asyncio.sleep(think)
        return data

    if (await post("/carriers/verify", mc=str(170000 + i)))["status"] != "eligible":
        return
    if (await post("/otp/send"))["status"] != "sent":
        return
    if (await post("/otp/verify", code=inbox.messages[session]))["status"] != "verified":
        return
    found = await post(
        "/loads/search", equipment="dry van", origin_state=ORIGINS[i], dest_state="GA"
    )
    if found["status"] != "found":
        return
    load = found["loads"][0]
    if (await post("/negotiate", load_id=load["load_id"], rate=load["offer"]))[
        "status"
    ] == "agreed":
        await post("/calls/close", summary="Offline capacity fixture.")
        await post("/calls/ended", ended_by="caller", duration_seconds=60)


def _p95(samples: list[float]) -> float:
    return round(sorted(samples)[math.ceil(len(samples) * 0.95) - 1], 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arrivals", type=int, choices=range(1, 13), default=12)
    parser.add_argument("--spacing", type=float, default=0)
    parser.add_argument("--think", type=float, default=0)
    parser.add_argument("--historical-calls", type=int, choices=range(0, 2001), default=0)
    parser.add_argument("--historical-bookings", type=int, choices=range(0, 2001), default=0)
    parser.add_argument("--dashboard", action="store_true")
    args = parser.parse_args()
    if min(args.spacing, args.think) < 0:
        parser.error("Spacing and think time must be nonnegative.")
    print(
        json.dumps(
            asyncio.run(
                profile(
                    args.arrivals,
                    args.spacing,
                    args.think,
                    historical_calls=args.historical_calls,
                    historical_bookings=args.historical_bookings,
                    dashboard=args.dashboard,
                )
            ),
            indent=2,
        )
    )
