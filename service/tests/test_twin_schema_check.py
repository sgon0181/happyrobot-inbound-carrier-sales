"""Provisioning checks select the right schema, fail closed and never mutate Twin."""

import json
from typing import Any

import httpx
import pytest

from tools.check_twin_schema import COLUMNS, KEYS, check, problems


def shape() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    columns = [
        {
            "table_name": table,
            "column_name": name,
            "data_type": kind,
            "is_nullable": "NO" if name == "id" else "YES",
            "column_default": None,
        }
        for table in ("calls", "bookings", "negotiations")
        for name, kind in (("id", "text"), ("version", "bigint"), ("data", "jsonb"))
    ]
    return columns, [
        {"table_name": t, "column_name": "id"} for t in ("calls", "bookings", "negotiations")
    ]


def test_observed_schema_and_additive_optional_columns_are_compatible() -> None:
    columns, keys = shape()
    assert problems(columns, keys) == []
    columns.append(dict(columns[0], column_name="optional", is_nullable="YES"))
    assert problems(columns, keys) == []
    columns[-1]["is_nullable"] = "NO"
    assert problems(columns, keys) == [
        "calls.optional: extra required column blocks service inserts"
    ]
    columns[-1]["column_default"] = "'safe'::text"
    assert problems(columns, keys) == []


def test_missing_memory_table_wrong_type_and_composite_key_fail() -> None:
    columns, keys = shape()
    columns = [c for c in columns if c["table_name"] != "negotiations"]
    columns[1]["data_type"] = "text"
    keys.append({"table_name": "calls", "column_name": "version"})
    found = problems(columns, keys)
    assert "negotiations.data: expected jsonb" in found
    assert "calls.version: expected bigint" in found
    assert "calls: primary key must be id alone" in found


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_check_sends_only_metadata_reads_with_an_explicit_environment(environment: str) -> None:
    columns, keys = shape()
    seen = []

    def reply(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-twin-environment"] == environment
        sql = json.loads(request.content)["sql"]
        assert "current_schema()" in sql and sql.lstrip().startswith("SELECT")
        seen.append(sql)
        rows = columns if sql == COLUMNS else keys
        return httpx.Response(200, json={"rows": rows, "rowCount": len(rows), "truncated": False})

    with httpx.Client(transport=httpx.MockTransport(reply)) as client:
        assert (
            check(
                environment, {"HAPPYROBOT_API_KEY": "fixture", "HAPPYROBOT_ORG_ID": "org"}, client
            )
            == []
        )
    assert seen == [COLUMNS, KEYS]


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(403, text="private server details"),
        httpx.Response(200, json={"rows": [], "truncated": True}),
        httpx.Response(200, json={"rows": [], "rowCount": 9}),
        httpx.Response(200, text="not JSON"),
        httpx.Response(200, json={"rows": [{"unexpected": "shape"}]}),
    ],
)
def test_bad_or_partial_response_does_not_print_private_payload(response: httpx.Response) -> None:
    with httpx.Client(transport=httpx.MockTransport(lambda _: response)) as client:
        found = check(
            "staging", {"HAPPYROBOT_API_KEY": "fixture", "HAPPYROBOT_ORG_ID": "org"}, client
        )
    assert found == ["Twin schema read failed or was incomplete; no changes made."]


def test_missing_credentials_or_unknown_environment_make_no_requests() -> None:
    def refuse(_: httpx.Request) -> httpx.Response:
        raise AssertionError("No request allowed")

    with httpx.Client(transport=httpx.MockTransport(refuse)) as client:
        assert check("staging", {}, client)
        with pytest.raises(ValueError, match="explicitly"):
            check("development", {}, client)
