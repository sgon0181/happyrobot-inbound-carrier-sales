"""Twin rows over HappyRobot's SQL API, with a version check on every write (D-23).

Twin runs one statement per request and has no multi-table transactions, but one
UPDATE ... WHERE version = n is atomic. So everything that changes together lives in
one row, and every write is compare-and-set. Statements are paced to about 4 a second.
"""

import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import httpx

URL = "https://platform.happyrobot.ai/api/v2/twin/sql"
TABLES = frozenset({"calls", "bookings"})
MAX_ATTEMPTS = 5  # tries at one change before a busy row counts as unavailable
RATE_LIMIT_RETRIES = 5

Data = dict[str, Any]


class TwinUnavailable(Exception):
    """Twin failed. A failed write may still have landed, so the next read decides."""


@dataclass(frozen=True, kw_only=True)
class TwinSettings:
    api_key: str = field(repr=False)
    org_id: str
    url: str = URL
    seconds_between_statements: float = 0.25
    timeout_seconds: float = 5.0


@dataclass(frozen=True)
class Row:
    version: int
    data: Data


class Twin:
    def __init__(
        self, settings: TwinSettings, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self.settings = settings
        headers = {
            "Authorization": f"Bearer {settings.api_key}",
            "x-organization-id": settings.org_id,
            "x-twin-environment": "production",
        }
        self._http = httpx.AsyncClient(
            transport=transport, headers=headers, timeout=settings.timeout_seconds
        )
        self._pacer = asyncio.Lock()
        self._next_start = 0.0

    async def close(self) -> None:
        await self._http.aclose()

    async def get(self, table: str, key: str) -> Row | None:
        sql = f"SELECT version, data FROM {_table(table)} WHERE id = {quote(key)}"  # noqa: S608
        rows = await self._sql(sql)
        if not rows:
            return None
        if len(rows) != 1 or not isinstance(rows[0].get("data"), dict):
            raise TwinUnavailable("Twin returned an invalid row.")
        return Row(int(rows[0]["version"]), rows[0]["data"])

    async def insert(self, table: str, key: str, data: Data) -> bool:
        """Create the row at version 1. False if the key already exists."""
        sql = (
            f"INSERT INTO {_table(table)} (id, version, data) "  # noqa: S608
            f"VALUES ({quote(key)}, 1, {_jsonb(data)}) ON CONFLICT (id) DO NOTHING RETURNING id"
        )
        return bool(await self._sql(sql))

    async def update(self, table: str, key: str, version: int, data: Data) -> bool:
        """Write only if the row is still at this version. False if another write got there."""
        sql = (
            f"UPDATE {_table(table)} SET version = version + 1, data = {_jsonb(data)} "  # noqa: S608
            f"WHERE id = {quote(key)} AND version = {int(version)} RETURNING id"
        )
        return bool(await self._sql(sql))

    async def change[T](
        self, table: str, key: str, edit: Callable[[Data | None], tuple[Data | None, T]]
    ) -> T:
        """Read, edit, then write back only if nothing changed meanwhile, retrying a busy row.

        edit gets the current data, or None if there is no row, and returns the data to
        write (None to write nothing) and a result. It may run more than once, so it must
        not do anything except compute.
        """
        for _ in range(MAX_ATTEMPTS):
            row = await self.get(table, key)
            data, result = edit(None if row is None else row.data)
            if data is None:
                return result
            if row is None:
                written = await self.insert(table, key, data)
            else:
                written = await self.update(table, key, row.version, data)
            if written:
                return result
        raise TwinUnavailable("The row kept changing, so the write was abandoned.")

    async def _sql(self, sql: str) -> list[Data]:
        """One statement. Only rate-limit refusals are retried; nothing else is."""
        for attempt in range(RATE_LIMIT_RETRIES + 1):
            await self._pace()
            try:
                response = await self._http.post(self.settings.url, json={"sql": sql})
            except httpx.HTTPError:
                raise TwinUnavailable("Twin did not answer.") from None
            if response.status_code == 429 and attempt < RATE_LIMIT_RETRIES:
                await asyncio.sleep(min(2.0, 0.2 * 2**attempt))
                continue
            return _rows(response)
        raise TwinUnavailable("Twin kept refusing for rate limit.")  # pragma: no cover

    async def _pace(self) -> None:
        """Start statements at least seconds_between_statements apart."""
        async with self._pacer:
            loop = asyncio.get_running_loop()
            await asyncio.sleep(max(0.0, self._next_start - loop.time()))
            self._next_start = loop.time() + self.settings.seconds_between_statements


def quote(value: str) -> str:
    """A SQL string literal. Every value reaches SQL through here, and only through here."""
    if "\x00" in value:
        raise ValueError("A SQL value cannot contain a NUL character.")
    return "'" + value.replace("'", "''") + "'"


def _table(name: str) -> str:
    if name not in TABLES:
        raise ValueError(f"Unknown table {name!r}.")
    return name


def _jsonb(data: Data) -> str:
    return quote(json.dumps(data, separators=(",", ":"))) + "::jsonb"


def _rows(response: httpx.Response) -> list[Data]:
    if response.status_code != 200:
        raise TwinUnavailable(f"Twin returned HTTP {response.status_code}.")
    try:
        rows = response.json()["rows"]
    except (ValueError, KeyError, TypeError):
        raise TwinUnavailable("Twin returned an unreadable reply.") from None
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise TwinUnavailable("Twin returned an unreadable reply.")
    return rows
