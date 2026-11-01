"""Validate pre-provisioned native Twin tables and initialize the control row.

Create tables once in Twin's UI: text primary id, integer version default0,
JSONB data default{}. Bookings also need nullable text active_load/active_call.
The runtime API role cannot create tables. No grant or role change is attempted.
"""

import asyncio
from service.config import settings
from service.adapters.twin.client import Platform, literal
from service.adapters.twin.repository import TwinRepository, GROUPS, CONTROL


async def main():
    p = Platform(settings())
    repo = TwinRepository(p)
    for group in GROUPS:
        name = repo.table(group)
        rows = (await p.sql("SELECT to_regclass(" + literal("public." + name) + ") AS name"))[
            "rows"
        ]
        if not rows[0]["name"]:
            raise RuntimeError("Provision " + name + " in the native Twin UI first")
        print(name, "present")
    await p.sql(
        f'INSERT INTO {repo.table("calls")}(id,version,data) '
        f"VALUES ({literal(CONTROL)},0,'{{}}'::jsonb) ON CONFLICT DO NOTHING"
    )
    print("Prototype schema checked; existing evidence preserved")


if __name__ == "__main__":
    asyncio.run(main())
