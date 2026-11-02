"""The TMS client against a real local TCP server, including every documented fault."""

import asyncio
import socket
import time

import pytest

from service.adapters.tms.client import TmsClient, TmsSettings, TmsUnavailable
from service.tests import fake_tms as fake
from service.tests.conftest import NetworkBlocked
from service.tests.fake_tms import FakeTMS, make_load, run


def test_tests_cannot_reach_anything_but_this_machine() -> None:
    with socket.socket() as connection, pytest.raises(NetworkBlocked):
        connection.connect(("192.0.2.1", 80))
    client = TmsClient(TmsSettings(host="192.0.2.1", port=80, token="t"))
    with pytest.raises(NetworkBlocked):
        asyncio.run(client.get("LD1"))


def test_get_returns_a_load_in_pdf_fields() -> None:
    tms = FakeTMS([make_load("LD1", RATE="2709", MAX_BUY="2922")])
    load = run(tms, lambda client: client.get("LD1"))
    assert load is not None
    assert (load.load_id, load.loadboard_rate, load.max_rate) == ("LD1", 2709, 2922)
    assert load.dimensions == "636 x 96 x 108 in"


def test_an_unknown_load_is_none_after_one_request() -> None:
    tms = FakeTMS()
    assert run(tms, lambda client: client.get("LD404")) is None
    assert len(tms.requests) == 1


def test_search_sends_only_established_filters_in_tms_format() -> None:
    tms = FakeTMS([make_load("LD1"), make_load("LD2", EQTYPE="REEFER")])
    found = run(
        tms,
        lambda client: client.query(
            equipment=" dry_van ", origin_state="tx", dest_state="ga", limit=5
        ),
    )
    assert [load.load_id for load in found] == ["LD1"]
    assert tms.requests == [
        "CMD:LOAD_QUERY|AUTH:<token>|EQTYPE:DRY_VAN|ORIG_STATE:TX|DEST_STATE:GA|MAX_RESULTS:5"
    ]


@pytest.mark.parametrize(
    "criteria",
    [
        {},
        {"equipment": "TANKER"},
        {"origin_state": "Texas"},
        {"equipment": "DRY_VAN", "limit": 0},
        {"equipment": "DRY_VAN", "limit": "3"},
        {"equipment": "DRY_VAN", "limit": True},
    ],
)
def test_bad_search_input_is_refused_before_connecting(criteria: dict[str, object]) -> None:
    tms = FakeTMS()
    with pytest.raises(ValueError):
        run(tms, lambda client: client.query(**criteria))  # type: ignore[arg-type]
    assert tms.requests == []


def test_search_results_keep_their_real_status() -> None:
    tms = FakeTMS([make_load("LD1"), make_load("LD2", STATUS="PENDING")])
    found = run(tms, lambda client: client.query(equipment="DRY_VAN"))
    assert {load.load_id: load.status for load in found} == {"LD1": "OPEN", "LD2": "PENDING"}


def test_a_reply_larger_than_one_frame_is_read_whole() -> None:
    loads = [make_load(f"LD{i}", NOTES="x" * 400, ORIG_CITY="C" * 300) for i in range(20)]
    found = run(FakeTMS(loads), lambda client: client.query(equipment="DRY_VAN", limit=20))
    assert len(found) == 20


def test_echo_skips_injected_faults() -> None:
    tms = FakeTMS(faults=[fake.SILENT])
    run(tms, lambda client: client.echo())
    assert list(tms.faults) == [fake.SILENT]


def test_a_wrong_token_is_not_retried_and_never_shown() -> None:
    tms = FakeTMS([make_load("LD1")])
    with pytest.raises(TmsUnavailable) as caught:
        run(tms, lambda client: client.get("LD1"), token="wrong-token")
    assert len(tms.requests) == 1
    assert "wrong-token" not in str(caught.value)
    assert "secret" not in repr(TmsSettings(host="h", port=1, token="secret"))


@pytest.mark.parametrize(
    "fault",
    [
        fake.SILENT,
        fake.LOST,
        fake.PARTIAL,
        fake.CUT_AT_LINE,
        fake.MALFORMED,
        fake.TRAILING,
        fake.SERVER_ERROR,
    ],
)
def test_each_fault_is_recovered_on_the_next_attempt(fault: str) -> None:
    tms = FakeTMS([make_load("LD1")], faults=[fault])
    load = run(tms, lambda client: client.get("LD1"))
    assert load is not None
    assert len(tms.requests) == 2


def test_a_read_gives_up_after_three_attempts() -> None:
    tms = FakeTMS([make_load("LD1")], faults=[fake.PARTIAL, fake.MALFORMED, fake.CUT_AT_LINE])
    with pytest.raises(TmsUnavailable):
        run(tms, lambda client: client.get("LD1"))
    assert len(tms.requests) == 3


def test_a_read_never_outlasts_its_budget() -> None:
    tms = FakeTMS([make_load("LD1")], faults=[fake.SILENT] * 3)
    started = time.monotonic()
    with pytest.raises(TmsUnavailable):
        run(tms, lambda client: client.get("LD1"), budget=0.3, attempt=0.2)
    assert time.monotonic() - started < 0.8


def test_reading_stops_at_end_without_waiting_for_the_server_to_close() -> None:
    tms = FakeTMS([make_load("LD1")], faults=[fake.DELAYED_CLOSE])
    started = time.monotonic()
    run(tms, lambda client: client.get("LD1"))
    assert time.monotonic() - started < 0.2
    assert len(tms.requests) == 1


def test_a_reply_split_across_many_chunks_is_reassembled() -> None:
    tms = FakeTMS([make_load("LD1")], faults=[fake.SPLIT])
    load = run(tms, lambda client: client.get("LD1"))
    assert load is not None
    assert len(tms.requests) == 1


def test_an_oversized_line_is_a_failed_read() -> None:
    tms = FakeTMS([make_load("LD1", NOTES="x" * 5000)])
    with pytest.raises(TmsUnavailable):
        run(tms, lambda client: client.get("LD1"))
    assert len(tms.requests) == 3


def test_a_closed_port_is_unavailable() -> None:
    tms = FakeTMS()
    port = run(tms, lambda client: asyncio.sleep(0, client.settings.port))
    settings = TmsSettings(
        host="127.0.0.1", port=port, token="t", read_budget_seconds=0.5, attempt_seconds=0.1
    )
    with pytest.raises(TmsUnavailable):
        asyncio.run(TmsClient(settings).get("LD1"))


def test_tms_errors_on_echo_and_search_mean_unavailable() -> None:
    for action in (lambda client: client.echo(), lambda client: client.query(equipment="REEFER")):
        with pytest.raises(TmsUnavailable):
            run(FakeTMS(), action, token="wrong-token")


def test_a_search_record_without_a_load_id_means_unavailable() -> None:
    with pytest.raises(TmsUnavailable):
        run(FakeTMS([make_load("")]), lambda client: client.query(equipment="DRY_VAN"))


def test_a_reply_for_a_different_load_is_refused() -> None:
    tms = FakeTMS()
    tms.board["LD1"] = make_load("LD2")
    with pytest.raises(TmsUnavailable):
        run(tms, lambda client: client.get("LD1"))
