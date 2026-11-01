"""Validate the existing Twin entity tables without DDL or control-row creation."""

import asyncio

from service.config import settings
from service.adapters.twin.client import Platform
from service.adapters.twin.repository import GROUPS, TwinRepository


async def main():
    values = settings()
    repository = TwinRepository(Platform(values), values.get("TWIN_TABLE_PREFIX", "proto_"))
    for table in GROUPS:
        await repository.rows(table, limit=1)
    print("Existing entity tables are accessible. No schema or control row changed.")


if __name__ == "__main__":
    asyncio.run(main())
