"""A paged dashboard scan must be complete before any metrics are presented."""

import asyncio

import httpx
import pytest

from service.adapters import twin as storage
from service.adapters.twin import Twin, TwinSettings, TwinUnavailable
from service.tests.fake_twin import FakeTwin


def test_keyset_scan_reads_all_pages_with_stable_order_and_quoted_cursor() -> None:
    fake = FakeTwin()
    fake.tables["calls"] = {f"run'{i:04}": (1, {"i": i}) for i in range(251)}
    rows = asyncio.run(fake.twin().get_all("calls"))
    assert len(rows) == 251 and [row.data["i"] for row in rows.values()] == list(range(251))
    assert len(fake.statements) == 3
    assert "WHERE id > 'run''0099'" in fake.statements[1]


def test_scan_limit_refuses_a_partial_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(storage, "MAX_SCAN_PAGES", 2)
    fake = FakeTwin()
    fake.tables["calls"] = {f"run-{i:04}": (1, {}) for i in range(201)}
    with pytest.raises(TwinUnavailable, match="scan limit"):
        asyncio.run(fake.twin().get_all("calls"))
    assert len(fake.statements) == 2


@pytest.mark.parametrize(
    "metadata",
    [
        {"rowCount": 501, "returnedRows": 500, "truncated": True, "truncationReason": "row_cap"},
        {
            "rowCount": 101,
            "returnedRows": 99,
            "truncated": True,
            "truncationReason": "response_size_cap",
        },
        {"rowCount": 2, "returnedRows": 1, "truncated": False},
        {"rowCount": 1, "returnedRows": 2, "truncated": False},
    ],
)
def test_incomplete_reply_metadata_fails_both_point_reads_and_scans(
    metadata: dict[str, object],
) -> None:
    async def run() -> None:
        reply = {"rows": [{"id": "a", "version": 1, "data": {}}]} | metadata
        settings = TwinSettings(api_key="fixture", org_id="org", seconds_between_statements=0)
        twin = Twin(settings, httpx.MockTransport(lambda _: httpx.Response(200, json=reply)))
        for read in (twin.get("calls", "a"), twin.get_all("calls")):
            with pytest.raises(TwinUnavailable, match="truncated or incomplete"):
                await read
        await twin.close()

    asyncio.run(run())


@pytest.mark.parametrize("ids", [["b", "a"], ["a", "a"]])
def test_out_of_order_or_duplicate_page_identifiers_are_rejected(ids: list[str]) -> None:
    reply = {"rows": [{"id": key, "version": 1, "data": {}} for key in ids]}
    settings = TwinSettings(api_key="fixture", org_id="org", seconds_between_statements=0)
    twin = Twin(settings, httpx.MockTransport(lambda _: httpx.Response(200, json=reply)))
    with pytest.raises(TwinUnavailable, match="unordered or duplicate"):
        asyncio.run(twin.get_all("calls"))
