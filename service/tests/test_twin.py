"""Twin storage: every value is quoted, every write is version-checked, and statements are paced."""

import asyncio
import time
from typing import Any

import httpx
import pytest

from service.adapters.twin import Data, Twin, TwinSettings, TwinUnavailable, quote
from service.tests.fake_twin import API_KEY, FakeTwin


def test_values_are_quoted_so_they_cannot_end_the_string() -> None:
    assert quote("LD1") == "'LD1'"
    assert quote("x' OR '1'='1") == "'x'' OR ''1''=''1'"
    with pytest.raises(ValueError):
        quote("bad\x00value")


def test_an_unknown_table_is_refused_before_any_request() -> None:
    fake = FakeTwin()
    with pytest.raises(ValueError):
        asyncio.run(fake.twin().get("users; DROP TABLE calls", "x"))
    assert fake.statements == []


def test_rows_are_created_once_and_updated_only_at_their_version() -> None:
    fake = FakeTwin()

    async def scenario() -> list[Any]:
        twin = fake.twin()
        return [
            await twin.get("calls", "run-1"),
            await twin.insert("calls", "run-1", {"mc": "138328"}),
            await twin.insert("calls", "run-1", {"mc": "999"}),  # the key exists
            await twin.update("calls", "run-1", 1, {"mc": "1515"}),
            await twin.update("calls", "run-1", 1, {"mc": "2"}),  # stale version
            await twin.get("calls", "run-1"),
        ]

    missing, created, duplicate, updated, stale, row = asyncio.run(scenario())
    assert (missing, created, duplicate, updated, stale) == (None, True, False, True, False)
    assert (row.version, row.data) == (2, {"mc": "1515"})


def test_many_rows_are_read_in_one_statement() -> None:
    fake = FakeTwin()

    async def scenario() -> tuple[dict[str, Any], dict[str, Any]]:
        twin = fake.twin()
        await twin.insert("bookings", "LD1", {"state": "RESERVED"})
        await twin.insert("bookings", "o'k", {"state": "RELEASED"})
        found = await twin.get_many("bookings", ["LD1", "o'k", "LD9", "LD1"])
        return {key: row.data for key, row in found.items()}, await twin.get_many("bookings", [])

    found, nothing = asyncio.run(scenario())
    assert found == {"LD1": {"state": "RESERVED"}, "o'k": {"state": "RELEASED"}}
    assert nothing == {}
    assert len(fake.statements) == 3  # two inserts and one read; no keys means no statement


def test_a_quote_in_a_value_is_stored_exactly() -> None:
    fake = FakeTwin()
    asyncio.run(fake.twin().insert("calls", "o'brien", {"note": "it's here"}))
    assert fake.data("calls", "o'brien") == {"note": "it's here"}


def count_up(data: Data | None) -> tuple[Data | None, int]:
    count = (data or {}).get("count", 0) + 1
    return {"count": count}, count


def test_concurrent_changes_to_one_row_all_land() -> None:
    fake = FakeTwin()

    async def scenario() -> list[int]:
        twin = fake.twin()
        return await asyncio.gather(*(twin.change("calls", "run-1", count_up) for _ in range(5)))

    results = asyncio.run(scenario())
    assert sorted(results) == [1, 2, 3, 4, 5]
    assert fake.data("calls", "run-1") == {"count": 5}


def test_a_change_that_edits_nothing_writes_nothing() -> None:
    fake = FakeTwin()
    result = asyncio.run(fake.twin().change("calls", "run-1", lambda data: (None, "unchanged")))
    assert result == "unchanged"
    assert len(fake.statements) == 1  # the read only


def test_a_row_that_keeps_changing_is_abandoned_after_five_tries() -> None:
    fake = FakeTwin()
    asyncio.run(fake.twin().insert("calls", "run-1", {"count": 0}))
    fake.interfere = True
    with pytest.raises(TwinUnavailable, match="kept changing"):
        asyncio.run(fake.twin().change("calls", "run-1", count_up))
    assert fake.data("calls", "run-1") == {"count": 0}


def test_rate_limit_refusals_are_retried_and_nothing_else_is() -> None:
    fake = FakeTwin()
    fake.statuses.extend([429, 429])
    assert asyncio.run(fake.twin().get("calls", "run-1")) is None
    assert len(fake.statements) == 3
    fake.statuses.append(500)
    with pytest.raises(TwinUnavailable, match="HTTP 500") as caught:
        asyncio.run(fake.twin().get("calls", "run-1"))
    assert API_KEY not in str(caught.value)


@pytest.mark.parametrize(
    "reply",
    [
        httpx.Response(200, text="not json"),
        httpx.Response(200, json={"rows": "nope"}),
        httpx.Response(200, json={"rows": [{"version": 1, "data": "not an object"}]}),
        httpx.Response(200, json={"rows": [{"version": 1, "data": {}}] * 2}),  # one key, two rows
    ],
)
def test_an_unreadable_reply_means_unavailable(reply: httpx.Response) -> None:
    settings = TwinSettings(api_key=API_KEY, org_id="org", seconds_between_statements=0)
    twin = Twin(settings, httpx.MockTransport(lambda _: reply))
    with pytest.raises(TwinUnavailable):
        asyncio.run(twin.get("calls", "run-1"))


def test_a_network_failure_means_unavailable() -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    twin = Twin(TwinSettings(api_key=API_KEY, org_id="org"), httpx.MockTransport(fail))
    with pytest.raises(TwinUnavailable):
        asyncio.run(twin.get("calls", "run-1"))


def test_every_request_carries_the_key_organization_and_environment() -> None:
    fake = FakeTwin()
    asyncio.run(fake.twin().get("calls", "run-1"))
    headers = fake.headers[0]
    assert headers["authorization"] == f"Bearer {API_KEY}"
    assert (headers["x-organization-id"], headers["x-twin-environment"]) == ("org", "production")
    assert API_KEY not in repr(TwinSettings(api_key=API_KEY, org_id="org"))


def test_statements_start_no_closer_than_the_pace() -> None:
    fake = FakeTwin()

    async def scenario() -> None:
        twin = fake.twin(pace=0.05)
        await asyncio.gather(*(twin.get("calls", f"run-{i}") for i in range(5)))
        await twin.close()

    started = time.monotonic()
    asyncio.run(scenario())
    assert time.monotonic() - started >= 4 * 0.05


def test_every_row_of_a_table_is_read_in_one_statement() -> None:
    fake = FakeTwin()

    async def scenario() -> tuple[dict[str, Any], dict[str, Any]]:
        twin = fake.twin()
        await twin.insert("bookings", "LD1", {"state": "RESERVED"})
        await twin.insert("bookings", "o'k", {"state": "RELEASED"})
        found = await twin.get_all("bookings")
        return {key: (row.version, row.data) for key, row in found.items()}, await twin.get_all(
            "calls"
        )

    found, empty = asyncio.run(scenario())
    assert found == {"LD1": (1, {"state": "RESERVED"}), "o'k": (1, {"state": "RELEASED"})}
    assert empty == {}
    assert fake.statements[-2:] == [
        "SELECT id, version, data FROM bookings",
        "SELECT id, version, data FROM calls",
    ]
