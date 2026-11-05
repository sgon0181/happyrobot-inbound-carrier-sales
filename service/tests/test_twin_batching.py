"""Fresh read batching preserves isolation, cancellation, fairness and optimistic conflicts."""

import asyncio
import json
from collections.abc import Callable, Coroutine

import httpx
import pytest

from service.adapters.twin import Twin, TwinSettings, TwinUnavailable
from service.adapters.twin_reads import MAX_KEYS, MAX_WAITERS
from service.tests.fake_twin import FakeTwin

Handle = (
    Callable[[httpx.Request], httpx.Response]
    | Callable[[httpx.Request], Coroutine[None, None, httpx.Response]]
)


def client(fake: FakeTwin, handle: Handle | None = None, pace: float = 0) -> Twin:
    settings = TwinSettings(api_key="fixture", org_id="org", seconds_between_statements=pace)
    return Twin(settings, httpx.MockTransport(handle or fake._handle))


def test_concurrent_reads_merge_keys_and_return_independent_copies() -> None:
    async def run() -> None:
        fake = FakeTwin()
        fake.tables["calls"]["a"] = (1, {"notes": []})
        twin = client(fake)
        a, b, missing = await asyncio.gather(
            twin.get("calls", "a"), twin.get("calls", "a"), twin.get("calls", "absent")
        )
        assert a and b and missing is None
        a.data["notes"].append("mine")
        assert b.data == {"notes": []}
        assert len(fake.statements) == 1
        assert fake.statements[0].count("'a'") == 1
        await twin.close()

    asyncio.run(run())


def test_waiting_read_collects_keys_only_after_its_paced_slot() -> None:
    async def run() -> None:
        fake = FakeTwin()
        twin = client(fake, pace=0.05)
        await twin.insert("calls", "a", {})
        first = asyncio.create_task(twin.get("calls", "a"))
        await asyncio.sleep(0.01)
        second = asyncio.create_task(twin.get("calls", "b"))
        await asyncio.gather(first, second)
        assert len(fake.statements) == 2
        assert "'a', 'b'" in fake.statements[-1]
        await twin.close()

    asyncio.run(run())


def test_one_cancellation_does_not_cancel_another_waiter_or_shared_read() -> None:
    async def run() -> None:
        fake, entered, release = FakeTwin(), asyncio.Event(), asyncio.Event()

        async def handle(request: httpx.Request) -> httpx.Response:
            entered.set()
            await release.wait()
            return fake._handle(request)

        twin = client(fake, handle)
        a, b = (asyncio.create_task(twin.get("calls", key)) for key in ("a", "b"))
        await entered.wait()
        a.cancel()
        with pytest.raises(asyncio.CancelledError):
            await a
        release.set()
        assert await b is None
        assert len(fake.statements) == 1
        await twin.close()

    asyncio.run(run())


def test_later_read_after_interleaving_write_has_a_new_snapshot() -> None:
    async def run() -> None:
        fake, entered, release = FakeTwin(), asyncio.Event(), asyncio.Event()
        fake.tables["calls"]["a"] = (1, {"value": "old"})

        async def handle(request: httpx.Request) -> httpx.Response:
            sql = json.loads(request.content)["sql"]
            response = fake._handle(request)
            if sql.startswith("SELECT") and not entered.is_set():
                entered.set()
                await release.wait()
            return response

        twin = client(fake, handle)
        first = asyncio.create_task(twin.get("calls", "a"))
        await entered.wait()
        assert await twin.update("calls", "a", 1, {"value": "new"})
        later = await twin.get("calls", "a")
        assert later and later.data["value"] == "new"
        release.set()
        earlier = await first
        assert earlier and earlier.data["value"] == "old"
        assert len(fake.statements) == 3
        await twin.close()

    asyncio.run(run())


def test_shared_failure_reaches_every_waiter_and_the_next_read_recovers() -> None:
    async def run() -> None:
        fake = FakeTwin()
        fake.statuses.append(500)
        twin = client(fake)
        results = await asyncio.gather(
            twin.get("calls", "a"), twin.get("calls", "b"), return_exceptions=True
        )
        assert all(isinstance(result, TwinUnavailable) for result in results)
        assert await twin.get("calls", "c") is None
        assert len(fake.statements) == 2
        await twin.close()

    asyncio.run(run())


def test_large_key_sets_are_bounded_and_dashboard_scans_remain_separate() -> None:
    async def run() -> None:
        fake = FakeTwin()
        twin = client(fake)
        await asyncio.gather(
            twin.get_many("calls", map(str, range(MAX_KEYS + 1))), twin.get_all("calls")
        )
        assert len(fake.statements) == 3
        assert max(sql.count("'") // 2 for sql in fake.statements) == MAX_KEYS
        with pytest.raises(ValueError, match="512 bytes"):
            await twin.get("calls", "x" * 513)
        await twin.close()

    asyncio.run(run())


def test_read_admission_is_bounded_and_shutdown_detaches_all_waiters() -> None:
    async def run() -> None:
        fake, entered, release = FakeTwin(), asyncio.Event(), asyncio.Event()

        async def handle(request: httpx.Request) -> httpx.Response:
            entered.set()
            await release.wait()
            return fake._handle(request)

        twin = client(fake, handle)
        tasks = [asyncio.create_task(twin.get("calls", str(i))) for i in range(MAX_WAITERS + 1)]
        await entered.wait()
        while not any(task.done() for task in tasks):
            await asyncio.sleep(0)
        await twin.close()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        assert sum(isinstance(result, TwinUnavailable) for result in results) == 1
        assert all(
            isinstance(result, (TwinUnavailable, asyncio.CancelledError)) for result in results
        )
        with pytest.raises(TwinUnavailable):
            await twin.get("calls", "after-close")

    asyncio.run(run())


@pytest.mark.parametrize("version", ["bad", None, float("inf")])
def test_malformed_shared_row_fails_every_waiter_without_hanging(version: object) -> None:
    async def run() -> None:
        fake = FakeTwin()

        def handle(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, text=json.dumps({"rows": [{"id": "a", "version": version, "data": {}}]})
            )

        twin = client(fake, handle)
        results = await asyncio.wait_for(
            asyncio.gather(twin.get("calls", "a"), twin.get("calls", "a"), return_exceptions=True),
            timeout=1,
        )
        assert all(isinstance(result, TwinUnavailable) for result in results)
        await twin.close()

    asyncio.run(run())
