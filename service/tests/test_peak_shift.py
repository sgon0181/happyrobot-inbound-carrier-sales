"""Twelve concurrent HTTP call journeys against a real TCP listener with fixture dependencies."""

import asyncio
from collections import Counter
from contextvars import ContextVar
from typing import Any
from uuid import UUID

import httpx
import pytest

from service import main
from service.adapters.fmcsa import Fmcsa, FmcsaSettings
from service.config import load_settings
from service.tests import rig
from service.tests.fake_tms import MALFORMED, FakeTMS, client_for, make_load
from service.tests.fake_twin import FakeTwin
from service.tests.test_carrier_policy import ACTIVE
from service.tests.test_config import ENV

ORIGINS = ("TX", "CA", "AZ", "KY", "UT", "OR", "WA", "LA", "MD", "AL", "IA", "IL")
SESSION: ContextVar[str] = ContextVar("inbox_session")


class Inboxes:
    """Out-of-band fixture mail. Each caller can read only its own delivery."""

    def __init__(self) -> None:
        self.messages: dict[str, str] = {}

    async def send(self, code: str, mc: str) -> None:
        self.messages[SESSION.get()] = code


async def journey(
    client: httpx.AsyncClient, inbox: Inboxes, start: asyncio.Barrier, i: int
) -> None:
    session = str(UUID(int=i + 1, version=4))
    SESSION.set(session)

    async def post(path: str, **body: Any) -> dict[str, Any]:
        res = await client.post(path, json={"run_id": session, **body})
        res.raise_for_status()
        return dict(res.json())

    assert (await post("/carriers/verify", mc=str(170000 + i)))["status"] == "eligible"
    assert (await post("/otp/send"))["status"] == "sent"
    assert (await post("/otp/verify", code=inbox.messages[session]))["status"] == "verified"
    await start.wait()
    match = await post(
        "/loads/search", equipment="dry van", origin_state=ORIGINS[i], dest_state="GA"
    )
    [load] = match["loads"]
    load_id = f"LD9{i:04}"
    assert load["load_id"] == load_id
    assert (await post("/negotiate", load_id=load_id, rate=load["offer"]))["status"] == "agreed"
    await post("/calls/close", summary="Controlled parallel call.")
    await post("/calls/ended", ended_by="assistant", duration_seconds=60)
    path = f"/bookings/{load_id}/confirm"
    requests = (
        client.post(path, json={"version": 1, "rep": rep}, headers=auth(ENV["OPS_API_KEY"]))
        for rep in ("rep-a", "rep-b")
    )
    responses = await asyncio.gather(*requests)
    assert sorted(r.json()["status"] for r in responses) == ["sent", "stale"]


def auth(key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {key}"}


def test_parallel_journeys_recover_a_bad_read_and_submit_each_load_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def run() -> None:
        twin, inbox = FakeTwin(), Inboxes()
        carrier = rig.FakeFmcsa([ACTIVE], delay=0.01)
        authority = Fmcsa(FmcsaSettings(api_key="fixture"), httpx.MockTransport(carrier.reply))
        records = [make_load(f"LD9{i:04}", ORIG_STATE=s) for i, s in enumerate(ORIGINS)]
        async with FakeTMS(records, faults=[MALFORMED]) as wire:
            monkeypatch.setattr(main, "Twin", lambda _: twin.twin())
            monkeypatch.setattr(main, "Fmcsa", lambda _: authority)
            monkeypatch.setattr(main, "CodeMailer", lambda _: inbox)
            monkeypatch.setattr(main, "TmsClient", lambda _: client_for(wire))
            app = main.build(load_settings(ENV | {"LIVE_BOOKING": "true", "CALL_COHORT": "real"}))
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://fixture", headers=auth(ENV["AGENT_API_KEY"])
            ) as client:
                barrier = asyncio.Barrier(len(records))
                tasks = (journey(client, inbox, barrier, i) for i in range(len(records)))
                await asyncio.wait_for(asyncio.gather(*tasks), 30)
            commands = Counter(line.split("|", 1)[0] for line in wire.requests)
            assert commands["CMD:LOAD_QUERY"] == len(records) + 1
            assert commands["CMD:LOAD_BOOK"] == len(records)
            bookings = twin.tables["bookings"]
            assert len(bookings) == len(twin.tables["calls"]) == len(records)
            assert all(row["state"] == "ACK_PENDING" for _, row in bookings.values())

    asyncio.run(run())
