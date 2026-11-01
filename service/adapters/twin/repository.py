"""Approved last-resort Twin CAS state with separate physical read models.

Twin wraps SQL and rejects data-modifying CTEs. Therefore the versioned control
row is authoritative. Eight business tables and the claims table are projected
read models. This is an explicit prototype deviation, not normalized atomic SQL.
"""

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


class Conflict(RuntimeError):
    pass


def empty():
    return {name: {} for name in GROUPS}


class MemoryRepository:
    label = "SIMULATED"

    def __init__(self):
        self.data = empty()
        self.lock = asyncio.Lock()

    async def initialize(self):
        pass

    async def read(self):
        return 0, copy.deepcopy(self.data)

    async def update(self, fn):
        async with self.lock:
            data = copy.deepcopy(self.data)
            result = fn(data)
            self.data = data
            return result


class TwinRepository:
    label = "LIVE"

    def __init__(self, client, prefix="proto_"):
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,30}_", prefix):
            raise ValueError("Invalid table prefix")
        self.client, self.prefix = client, prefix
        self.pending = set()
        self.projection_errors = 0

    def table(self, name):
        if name not in GROUPS:
            raise ValueError("Unknown table")
        return self.prefix + name

    async def initialize(self):
        for name in GROUPS:
            extra = (
                ", active_load text UNIQUE, active_call text UNIQUE" if name == "bookings" else ""
            )
            await self.client.sql(
                f"CREATE TABLE IF NOT EXISTS {self.table(name)} "
                f"(id text PRIMARY KEY, version bigint NOT NULL DEFAULT 0, data jsonb NOT NULL{extra})"
            )
        await self.client.sql(
            f'INSERT INTO {self.table("calls")}(id,data) '
            f"VALUES ({literal(CONTROL)},'{{}}'::jsonb) ON CONFLICT DO NOTHING"
        )

    async def read(self):
        rows = (
            await self.client.sql(
                f'SELECT version,data FROM {self.table("calls")} WHERE id={literal(CONTROL)}'
            )
        )["rows"]
        if len(rows) != 1:
            raise RuntimeError("Prototype schema not initialized")
        row = rows[0]
        data = row["data"]
        if data == {}:
            return int(row["version"]), empty()
        if not isinstance(data, dict) or any(
            k not in data or not isinstance(data[k], dict) for k in GROUPS
        ):
            raise RuntimeError("Canonical Twin state is incomplete; writes blocked")
        return int(row["version"]), data

    async def update(self, fn):
        for _ in range(30):
            version, before = await self.read()
            data = copy.deepcopy(before)
            result = fn(data)
            for key, row in data["bookings"].items():
                if before["bookings"].get(key) == row:
                    continue
                for kind, value in [("load", row["load_id"]), ("call", row["call_id"])]:
                    claim = kind + ":" + value
                    active = row["state"] != "FAILED"
                    previous = data["booking_claims"].get(claim)
                    if previous and previous["booking_id"] != key:
                        if not active:
                            continue
                        if previous["active"]:
                            raise Conflict("Physical claim already held")
                    data["booking_claims"][claim] = {
                        "booking_id": key,
                        "active": active,
                        "load_id": row["load_id"],
                        "call_id": row["call_id"],
                    }
            rows = (
                await self.client.sql(
                    f'UPDATE {self.table("calls")} SET version=version+1, '
                    f"data={literal(json.dumps(data))}::jsonb WHERE id={literal(CONTROL)} "
                    f"AND version={version} RETURNING version"
                )
            )["rows"]
            if rows:
                task = asyncio.create_task(self.project(before, data, version + 1))
                self.pending.add(task)
                task.add_done_callback(self.pending.discard)
                return result
            await asyncio.sleep(0.01)
        raise Conflict("Prototype concurrent update did not settle")

    async def project(self, before, data, version):
        # These are monotonic read models, not the source of coordination.
        # The canonical row commits first. Projection failure cannot lose an ACK.
        for name in GROUPS:
            changed = [
                (key, row) for key, row in data[name].items() if before[name].get(key) != row
            ]
            if not changed:
                continue
            table = self.table(name)
            fields = "id,version,data"
            values = []
            updates = "version=EXCLUDED.version,data=EXCLUDED.data"
            if name == "bookings":
                fields += ",active_load,active_call"
                updates += ",active_load=EXCLUDED.active_load,active_call=EXCLUDED.active_call"
            for key, row in changed:
                value = f"({literal(key)},{version},{literal(json.dumps(row))}::jsonb"
                if name == "bookings":
                    active = row["state"] != "FAILED"
                    value += f',{literal(row["load_id"] if active else None)},{literal(row["call_id"] if active else None)}'
                values.append(value + ")")
            try:
                await self.client.sql(
                    f"INSERT INTO {table}({fields}) VALUES "
                    + ",".join(values)
                    + f" ON CONFLICT(id) DO UPDATE SET {updates} WHERE {table}.version<EXCLUDED.version"
                )
            except Exception:
                self.projection_errors += 1
