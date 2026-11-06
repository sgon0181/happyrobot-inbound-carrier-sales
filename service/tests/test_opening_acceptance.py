"""Opening acceptance avoids a redundant write without bypassing shared-state reads."""

import asyncio
from typing import Any
from unittest.mock import patch

import httpx
import pytest

from service import negotiation_memory as memory
from service.core.negotiation import Action
from service.core.pricing import Terms
from service.tests.fake_tms import make_load
from service.tests.rig import AGENT, RUN, START
from service.tests.test_reciprocal_memory import reconnect
from service.tests.test_selling import LANE, counter, offered

TERMS = Terms(
    load_id="LD09001", policy_version="fixture", opening=1900, targets=(2000, 2075, 2200), cap=2200
)
KEY = "138328:LD09001"


def test_exact_opening_acceptance_still_reads_memory_and_finalizes_booking() -> None:
    r = offered()
    before = len(r.twin.statements)
    assert counter(r, 1900)["status"] == "agreed"
    statements = r.twin.statements[before:]
    assert any("FROM negotiations" in sql for sql in statements)
    assert not any(
        sql.startswith(("INSERT INTO negotiations", "UPDATE negotiations")) for sql in statements
    )
    assert not r.twin.tables["negotiations"]
    assert r.row()["agreement"]["rate"] == 1900
    assert r.row()["accepting"] is None
    assert r.twin.data("bookings", "LD09001")["rate"] == 1900


def test_lower_acceptance_persists_the_lower_price() -> None:
    r = offered()
    assert counter(r, 1850)["status"] == "agreed"
    assert r.twin.data("negotiations", KEY)["offer"] == 1850


def test_existing_memory_keeps_its_cas_even_when_acceptance_changes_nothing() -> None:
    r = offered()
    counter(r, 9000)
    before = r.twin.tables["negotiations"][KEY][0]
    assert counter(r, 1900)["status"] == "agreed"
    assert r.twin.tables["negotiations"][KEY][0] == before + 1
    assert r.twin.data("negotiations", KEY)["rounds"] == 1


def test_repriced_opening_is_not_an_empty_negotiation() -> None:
    r = offered()
    r.board.records = [make_load(RATE="2200", MAX_BUY="2400")]
    assert counter(r, 1900)["status"] == "agreed"
    assert r.twin.data("negotiations", KEY)["offer"] == 1900


def test_rounds_spent_on_other_load_are_not_forgotten() -> None:
    r = offered(make_load("LD09001"), make_load("LD09002"))
    counter(r, 9000, "LD09002")
    assert counter(r, 1900)["status"] == "agreed"
    assert r.twin.data("negotiations", KEY)["rounds"] == 1


def test_material_change_replaces_existing_memory_through_cas() -> None:
    r = offered()
    counter(r, 9000)
    before = r.twin.tables["negotiations"][KEY][0]
    r.board.records = [make_load(WEIGHT="30000")]
    run = reconnect(r)
    r.post("/loads/search", run_id=run, **LANE)
    result = r.post("/negotiate", run_id=run, load_id="LD09001", rate="1900")
    assert result["status"] == "agreed"
    assert r.twin.tables["negotiations"][KEY][0] == before + 1
    shipment: Any = r.twin.data("negotiations", KEY)["shipment"]
    assert shipment["weight"] == 30000


@pytest.mark.parametrize(
    ("other_ask", "other_action", "remembered"),
    [
        ("2050", Action.COUNTER, 1950),
        ("1850", Action.ACCEPT, 1850),
    ],
)
def test_concurrent_decision_is_not_overwritten_by_opening_acceptance(
    other_ask: str,
    other_action: Action,
    remembered: int,
) -> None:
    r = offered()
    load = asyncio.run(r.board.get("LD09001"))
    assert load is not None

    async def scenario() -> None:
        twin = r.twin.twin()
        original_get = twin.get

        async def interleave(table: str, key: str) -> Any:
            row = await original_get(table, key)
            if table == "negotiations" and row is None:
                other = await memory.decide(
                    r.twin.twin(),
                    "138328",
                    "other-call",
                    load,
                    TERMS,
                    r.row(),
                    other_ask,
                    False,
                    START,
                )
                assert other.action is other_action
            return row

        with patch.object(twin, "get", interleave):
            accepted = await memory.decide(
                twin, "138328", RUN, load, TERMS, r.row(), "1900", False, START
            )
        assert accepted.action is Action.ACCEPT and accepted.rate == 1900
        assert r.twin.data("negotiations", KEY)["offer"] == remembered

    asyncio.run(scenario())


def test_competing_opening_acceptances_still_reserve_exactly_once() -> None:
    r = offered()
    runs = [RUN, reconnect(r), reconnect(r)]
    for run in runs[1:]:
        r.post("/loads/search", run_id=run, **LANE)

    async def scenario() -> list[str]:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=r.client.app),
            base_url="http://fixture",
            headers={"Authorization": "Bearer " + AGENT},
        ) as client:
            replies = await asyncio.gather(
                *(
                    client.post(
                        "/negotiate", json={"run_id": run, "load_id": "LD09001", "rate": "1900"}
                    )
                    for run in runs
                )
            )
        return [reply.json()["status"] for reply in replies]

    statuses = asyncio.run(scenario())
    assert statuses.count("agreed") == 1
    assert len(r.twin.tables["bookings"]) == 1
    assert not r.twin.tables["negotiations"]
    assert not r.board.sends


def test_lower_shared_acceptance_present_at_read_is_never_skipped() -> None:
    r = offered()
    load = asyncio.run(r.board.get("LD09001"))
    assert load is not None
    first = asyncio.run(
        memory.decide(
            r.twin.twin(), "138328", "other-call", load, TERMS, r.row(), "1850", False, START
        )
    )
    assert first.action is Action.ACCEPT
    version = r.twin.tables["negotiations"][KEY][0]
    reply = counter(r, 1900)
    assert reply["status"] == "counter" and reply["offer"] < 1900
    assert r.twin.tables["negotiations"][KEY][0] == version + 1
    assert not r.twin.tables["bookings"]
