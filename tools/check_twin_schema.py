"""Read-only check of the selected Twin schema. Never creates tables or prints row data."""

import argparse
from collections.abc import Mapping
from typing import Any

import httpx

from service.adapters.twin import TABLES, URL, TwinUnavailable, _rows
from tools.launch import settings

COLUMNS = """
SELECT table_name, column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = current_schema()
AND table_name IN ('calls', 'bookings', 'negotiations')
ORDER BY table_name, ordinal_position
"""
KEYS = """
SELECT tc.table_name, kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
AND tc.table_name = kcu.table_name
WHERE tc.table_schema = current_schema() AND tc.constraint_type = 'PRIMARY KEY'
AND tc.table_name IN ('calls', 'bookings', 'negotiations')
"""


def problems(columns: list[dict[str, Any]], keys: list[dict[str, Any]]) -> list[str]:
    found = []
    expected = {"id": "text", "version": "bigint", "data": "jsonb"}
    for table in sorted(TABLES):
        actual = {r["column_name"]: r for r in columns if r["table_name"] == table}
        for column, kind in expected.items():
            if actual.get(column, {}).get("data_type") != kind:
                found.append(f"{table}.{column}: expected {kind}")
        if actual.get("id", {}).get("is_nullable") != "NO":
            found.append(f"{table}.id: must be NOT NULL")
        if [r["column_name"] for r in keys if r["table_name"] == table] != ["id"]:
            found.append(f"{table}: primary key must be id alone")
        for column, row in actual.items():
            if column not in expected and row["is_nullable"] == "NO" and not row["column_default"]:
                found.append(f"{table}.{column}: extra required column blocks service inserts")
    return found


def check(environment: str, values: Mapping[str, str], client: httpx.Client) -> list[str]:
    """The environment header also selects current_schema(); never assume public."""
    if environment not in {"production", "staging"}:
        raise ValueError("Choose production or staging explicitly.")
    required = ("HAPPYROBOT_API_KEY", "HAPPYROBOT_ORG_ID")
    if any(not values.get(key) for key in required):
        return ["Set HAPPYROBOT_API_KEY and HAPPYROBOT_ORG_ID in .env or the environment."]
    headers = {
        "Authorization": f"Bearer {values['HAPPYROBOT_API_KEY']}",
        "x-organization-id": values["HAPPYROBOT_ORG_ID"],
        "x-twin-environment": environment,
    }
    try:
        columns = _rows(client.post(URL, headers=headers, json={"sql": COLUMNS}))
        keys = _rows(client.post(URL, headers=headers, json={"sql": KEYS}))
        return problems(columns, keys)
    except (httpx.HTTPError, TwinUnavailable, KeyError, TypeError):
        return ["Twin schema read failed or was incomplete; no changes made."]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", choices=("production", "staging"), required=True)
    args = parser.parse_args()
    with httpx.Client(timeout=20) as client:
        found = check(args.environment, settings(), client)
    for problem in found:
        print(problem)
    if not found:
        print(f"Twin {args.environment}: calls, bookings and negotiations schema compatible.")
    return int(bool(found))


if __name__ == "__main__":
    raise SystemExit(main())
