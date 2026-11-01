"""Authoritative entity rows in Twin, with compare-and-set per mutable row."""

import asyncio
import copy
import json
import re

from .client import literal

GROUPS = (
    "carriers",
    "calls",
    "call_transcripts",
    "call_events",
    "otp_challenges",
    "negotiation_rounds",
    "bookings",
    "unmet_demand",
    "booking_claims",
)
CONTROL = "__prototype_commit_version__"
CRITICAL = {"calls", "bookings", "otp_challenges", "booking_claims"}


class Conflict(RuntimeError):
    pass


def empty():
    return {name: {} for name in GROUPS}


class Repository:
    """Shared row contract. Bulk reads exist only for operators and migration."""

    def __init__(self):
        self.pending = set()
        self.projection_errors = 0

    async def mutate(self, table, key, change, initial=None):
        for _ in range(20):
            version, before = await self.get(table, key)
            row = copy.deepcopy(before if before is not None else initial)
            if row is None:
                raise KeyError(key)
            result = change(row)
            if row == before:
                return result
            if await self.cas(table, key, version, row):
                return result
            await asyncio.sleep(0)
        raise Conflict("Entity update did not settle")

    async def read_call(self, cid):
        version, call = await self.get("calls", cid)
        state = empty()
        if call is not None:
            state["calls"][cid] = call
            challenge = call.get("challenge")
            if challenge:
                _, row = await self.get("otp_challenges", challenge)
                if row is not None:
                    state["otp_challenges"][challenge] = row
        state["bookings"] = {key: row for key, _, row in await self.rows("bookings", call_id=cid)}
        return version, state

    async def update_call(self, cid, change, initial):
        for _ in range(20):
            version, state = await self.read_call(cid)
            call = state["calls"].setdefault(cid, copy.deepcopy(initial))
            before = copy.deepcopy(state)
            result = change(state, call)
            if state["otp_challenges"] != before["otp_challenges"]:
                raise ValueError("OTP changes require their own conditional row update")
            if state["bookings"] != before["bookings"]:
                raise ValueError("Booking changes require the booking store")
            if call != before["calls"].get(cid) or version is None:
                if not await self.cas("calls", cid, version, call):
                    await asyncio.sleep(0)
                    continue
            for group in GROUPS:
                if group in CRITICAL:
                    continue
                for key, row in state[group].items():
                    if before[group].get(key) != row:
                        self.defer_aux(group, key, row)
            return result
        raise Conflict("Call update did not settle")

    def defer_aux(self, table, key, row):
        async def save():
            try:
                await self.upsert(table, key, row)
            except Exception:
                self.projection_errors += 1

        task = asyncio.create_task(save())
        self.pending.add(task)
        task.add_done_callback(self.pending.discard)

    async def acquire_claim(self, key, row):
        version, current = await self.get("booking_claims", key)
        if current and (current.get("active") or current.get("write_intent_id")):
            return False
        return await self.cas("booking_claims", key, version, row)

    async def read(self):
        state = empty()
        for group, rows in zip(GROUPS, await asyncio.gather(*(self.rows(g) for g in GROUPS))):
            state[group] = {key: row for key, _, row in rows}
        return 0, state

    async def drain(self):
        if self.pending:
            await asyncio.gather(*tuple(self.pending))


class MemoryRepository(Repository):
    label = "SIMULATED"

    def __init__(self):
        super().__init__()
        self.data = empty()
        self.versions = {}
        self.lock = asyncio.Lock()

    async def initialize(self):
        pass

    async def get(self, table, key):
        row = self.data[table].get(key)
        return (
            (self.versions.get((table, key), 0), copy.deepcopy(row))
            if row is not None
            else (None, None)
        )

    async def cas(self, table, key, version, row):
        async with self.lock:
            actual = self.versions.get((table, key), 0) if key in self.data[table] else None
            if actual != version:
                return False
            self.data[table][key] = copy.deepcopy(row)
            self.versions[table, key] = (version or 0) + 1
            return True

    async def rows(self, table, *, call_id=None, ids=None, filters=None, limit=None):
        result = []
        for key, row in self.data[table].items():
            if key == CONTROL or (ids is not None and key not in ids):
                continue
            if call_id is not None and row.get("call_id") != call_id:
                continue
            if filters and any(str(row.get(k)) != str(v) for k, v in filters.items()):
                continue
            result.append((key, self.versions.get((table, key), 0), copy.deepcopy(row)))
        return result[:limit] if limit else result

    async def upsert(self, table, key, row):
        async with self.lock:
            if self.data[table].get(key) != row:
                self.data[table][key] = copy.deepcopy(row)
                self.versions[table, key] = self.versions.get((table, key), 0) + 1

    async def update(self, fn):
        """Fixture setup compatibility, never used by production hot paths."""
        async with self.lock:
            state = copy.deepcopy(self.data)
            result = fn(state)
            self.data = state
            return result

    def defer_aux(self, table, key, row):
        self.data[table][key] = copy.deepcopy(row)


class TwinRepository(Repository):
    label = "LIVE"

    def __init__(self, client, prefix="proto_"):
        super().__init__()
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,30}_", prefix):
            raise ValueError("Invalid table prefix")
        self.client, self.prefix = client, prefix

    def table(self, name):
        if name not in GROUPS:
            raise ValueError("Unknown table")
        return self.prefix + name

    async def get(self, table, key):
        if key == CONTROL:
            raise ValueError("The frozen control row is not an entity")
        result = await self.client.sql(
            f"SELECT version,data FROM {self.table(table)} WHERE id={literal(key)}"
        )
        rows = result["rows"]
        if not rows:
            return None, None
        if len(rows) != 1 or not isinstance(rows[0].get("data"), dict):
            raise RuntimeError("Invalid entity row")
        return int(rows[0]["version"]), rows[0]["data"]

    async def read_call(self, cid):
        calls, challenges, bookings = (
            self.table(name) for name in ("calls", "otp_challenges", "bookings")
        )
        key = literal(cid)
        sql = (
            f"SELECT 'calls' AS entity,id,version,data FROM {calls} WHERE id={key} "
            f"UNION ALL SELECT 'otp_challenges' AS entity,id,version,data FROM {challenges} "
            f"WHERE id=(SELECT data->>'challenge' FROM {calls} WHERE id={key}) "
            f"UNION ALL SELECT 'bookings' AS entity,id,version,data FROM {bookings} "
            f"WHERE data->>'call_id'={key}"
        )
        state, version = empty(), None
        for row in (await self.client.sql(sql))["rows"]:
            if row["entity"] not in {"calls", "otp_challenges", "bookings"} or not isinstance(
                row["data"], dict
            ):
                raise RuntimeError("Invalid scoped entity result")
            state[row["entity"]][row["id"]] = row["data"]
            if row["entity"] == "calls":
                version = int(row["version"])
        return version, state

    def booking_columns(self, table, row):
        if table != "bookings":
            return "", "", ""
        active = row.get("state") != "FAILED" or bool(row.get("write_intent_id"))
        load = literal(row.get("load_id") if active else None)
        call = literal(row.get("call_id") if active else None)
        return (
            ",active_load,active_call",
            f",{load},{call}",
            f",active_load={load},active_call={call}",
        )

    async def cas(self, table, key, version, row):
        name = self.table(table)
        value = literal(json.dumps(row)) + "::jsonb"
        columns, values, assignments = self.booking_columns(table, row)
        if version is None:
            sql = (
                f"INSERT INTO {name}(id,version,data{columns}) "
                f"VALUES ({literal(key)},1,{value}{values}) ON CONFLICT DO NOTHING RETURNING id"
            )
        else:
            sql = (
                f"UPDATE {name} SET version=version+1,data={value}{assignments} "
                f"WHERE id={literal(key)} AND version={int(version)} RETURNING id"
            )
        return bool((await self.client.sql(sql))["rows"])

    async def rows(self, table, *, call_id=None, ids=None, filters=None, limit=None):
        where = [f"id<>{literal(CONTROL)}"]
        if call_id is not None:
            where.append(f"data->>'call_id'={literal(call_id)}")
        if ids is not None:
            if not ids:
                return []
            where.append("id IN (" + ",".join(literal(key) for key in ids) + ")")
        for key, value in (filters or {}).items():
            if not re.fullmatch(r"[a-z_]+", key):
                raise ValueError("Invalid filter")
            where.append(f"data->>{literal(key)}={literal(value)}")
        suffix = f" LIMIT {int(limit)}" if limit else ""
        result = await self.client.sql(
            f"SELECT id,version,data FROM {self.table(table)} WHERE " + " AND ".join(where) + suffix
        )
        return [(r["id"], int(r["version"]), r["data"]) for r in result["rows"]]

    async def acquire_claim(self, key, row):
        name = self.table("booking_claims")
        result = await self.client.sql(
            f"INSERT INTO {name}(id,version,data) "
            f"VALUES ({literal(key)},1,{literal(json.dumps(row))}::jsonb) "
            f"ON CONFLICT(id) DO UPDATE SET version={name}.version+1,data=EXCLUDED.data "
            f"WHERE {name}.data->>'active'='false' "
            f"AND COALESCE({name}.data->>'write_intent_id','')='' RETURNING id"
        )
        return bool(result["rows"])

    async def upsert(self, table, key, row):
        if table in CRITICAL:
            raise ValueError("Critical entities require compare-and-set")
        name = self.table(table)
        await self.client.sql(
            f"INSERT INTO {name}(id,version,data) "
            f"VALUES ({literal(key)},1,{literal(json.dumps(row))}::jsonb) "
            f"ON CONFLICT(id) DO UPDATE SET version={name}.version+1,data=EXCLUDED.data "
            f"WHERE {name}.data IS DISTINCT FROM EXCLUDED.data RETURNING id"
        )
