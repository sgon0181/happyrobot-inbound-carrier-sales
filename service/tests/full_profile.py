"""Optional offline full-flow saturation probe with actual Twin pacing and voice deadlines.

Run: python -m service.tests.full_profile --arrivals 12 --spacing 1.5 --think 3
All dependencies are fixtures. A caller stops at its first error without a final webhook,
so outstanding claims remain visible. No TMS booking command is issued.
"""

import argparse
import asyncio
import json
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
from service.tests.rig import FakeFmcsa
from service.tests.test_carrier_policy import ACTIVE
from service.tests.test_config import ENV
from service.tests.test_peak_shift import ORIGINS, SESSION, Inboxes, auth


async def profile(arrivals: int, spacing: float, think: float) -> dict[str, Any]:
    twin, inbox = FakeTwin(), Inboxes()
    carrier = FakeFmcsa([ACTIVE], delay=0.01)
    authority = Fmcsa(FmcsaSettings(api_key="fixture"), httpx.MockTransport(carrier.reply))
    outcomes: Counter[str] = Counter()
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
            await asyncio.gather(
                *(_caller(api, inbox, outcomes, i, spacing, think) for i in range(arrivals))
            )
        writes = sum(line.startswith("CMD:LOAD_BOOK|") for line in wire.requests)
    calls = [row for _, row in twin.tables["calls"].values()]
    return {
        "arrivals": arrivals,
        "spacing_seconds": spacing,
        "think_seconds": think,
        "outcomes": dict(outcomes),
        "sql_statements": len(twin.statements),
        "durable_holds": len(twin.tables["bookings"]),
        "outstanding_claims": sum(bool(call.get("accepting")) for call in calls),
        "finalized_agreements": sum(bool(call.get("agreement")) for call in calls),
        "tms_booking_writes": writes,
    }


async def _caller(
    api: httpx.AsyncClient,
    inbox: Inboxes,
    outcomes: Counter[str],
    i: int,
    spacing: float,
    think: float,
) -> None:
    await asyncio.sleep(i * spacing)
    session = str(UUID(int=i + 1, version=4))
    SESSION.set(session)

    async def post(path: str, **body: Any) -> dict[str, Any]:
        response = await api.post(path, json={"run_id": session, **body})
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arrivals", type=int, choices=range(1, 13), default=12)
    parser.add_argument("--spacing", type=float, default=0)
    parser.add_argument("--think", type=float, default=0)
    args = parser.parse_args()
    if min(args.spacing, args.think) < 0:
        parser.error("Spacing and think time must be nonnegative.")
    print(json.dumps(asyncio.run(profile(args.arrivals, args.spacing, args.think)), indent=2))
