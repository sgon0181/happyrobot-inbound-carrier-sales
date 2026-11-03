"""A fake Twin for tests: it runs the adapter's exact SQL against in-memory tables.

Any statement the adapter did not build itself is refused, so a change to the SQL
shows up here as a failing test, not as a surprise on the live Twin.
"""

import json
import re
from collections import deque

import httpx

from service.adapters.twin import Twin, TwinSettings

API_KEY = "fake-twin-key"
_LITERAL = r"'((?:[^']|'')*)'"
_SELECT = re.compile(rf"SELECT version, data FROM (\w+) WHERE id = {_LITERAL}")
_SELECT_MANY = re.compile(
    rf"SELECT id, version, data FROM (\w+) WHERE id IN \(({_LITERAL}(?:, {_LITERAL})*)\)"
)
_SELECT_ALL = re.compile(r"SELECT id, version, data FROM (\w+)")
_INSERT = re.compile(
    rf"INSERT INTO (\w+) \(id, version, data\) VALUES \({_LITERAL}, 1, {_LITERAL}::jsonb\) "
    r"ON CONFLICT \(id\) DO NOTHING RETURNING id"
)
_UPDATE = re.compile(
    rf"UPDATE (\w+) SET version = version \+ 1, data = {_LITERAL}::jsonb "
    rf"WHERE id = {_LITERAL} AND version = (\d+) RETURNING id"
)


class FakeTwin:
    def __init__(self) -> None:
        self.tables: dict[str, dict[str, tuple[int, dict[str, object]]]] = {
            "calls": {},
            "bookings": {},
        }
        self.statements: list[str] = []
        self.headers: list[httpx.Headers] = []
        self.statuses: deque[int] = deque()  # HTTP statuses to answer with before working again
        self.interfere = False  # another writer bumps every row right after each read

    def twin(self, *, pace: float = 0.0) -> Twin:
        settings = TwinSettings(
            api_key=API_KEY,
            org_id="org",
            url="https://twin.test/sql",
            seconds_between_statements=pace,
        )
        return Twin(settings, httpx.MockTransport(self._handle))

    def data(self, table: str, key: str) -> dict[str, object]:
        return self.tables[table][key][1]

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.headers.append(request.headers)
        sql = json.loads(request.content)["sql"]
        self.statements.append(sql)
        if self.statuses:
            return httpx.Response(self.statuses.popleft())
        rows = self._run(sql)
        if rows is None:
            return httpx.Response(400, json={"message": "statement not recognised"})
        return httpx.Response(200, json={"rows": rows})

    def _run(self, sql: str) -> list[dict[str, object]] | None:
        if match := _SELECT.fullmatch(sql):
            table, key = match[1], _text(match[2])
            row = self.tables[table].get(key)
            if row and self.interfere:
                self.tables[table][key] = (row[0] + 1, row[1])
            return [{"version": row[0], "data": row[1]}] if row else []
        if match := _SELECT_MANY.fullmatch(sql):
            table = self.tables[match[1]]
            keys = [_text(key) for key in re.findall(_LITERAL, match[2])]
            return [
                {"id": k, "version": table[k][0], "data": table[k][1]} for k in keys if k in table
            ]
        if match := _SELECT_ALL.fullmatch(sql):
            rows = self.tables[match[1]].items()
            return [{"id": key, "version": row[0], "data": row[1]} for key, row in rows]
        if match := _INSERT.fullmatch(sql):
            table, key, data = match[1], _text(match[2]), json.loads(_text(match[3]))
            if key in self.tables[table]:
                return []
            self.tables[table][key] = (1, data)
            return [{"id": key}]
        if match := _UPDATE.fullmatch(sql):
            table, data, key, version = (
                match[1],
                json.loads(_text(match[2])),
                _text(match[3]),
                match[4],
            )
            row = self.tables[table].get(key)
            if row is None or row[0] != int(version):
                return []
            self.tables[table][key] = (row[0] + 1, data)
            return [{"id": key}]
        return None


def _text(literal: str) -> str:
    return literal.replace("''", "'")
