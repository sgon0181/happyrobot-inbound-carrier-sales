"""The FMCSA lookup: an error is unavailable, never a result, and the webKey never leaks."""

import asyncio
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from service.adapters.fmcsa import Fmcsa, FmcsaSettings, FmcsaUnavailable

KEY = "fmcsa-web-key"
CARRIER = {"legalName": "WERNER ENTERPRISES INC", "statusCode": "A"}


def lookup(reply: Callable[[httpx.Request], httpx.Response], mc: str = "138328") -> Any:
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return reply(request)

    async def scenario() -> Any:
        client = Fmcsa(FmcsaSettings(api_key=KEY), httpx.MockTransport(handle))
        try:
            return await client.carriers(mc)
        finally:
            await client.close()

    return asyncio.run(scenario()), seen


def test_the_docket_lookup_sends_the_mc_and_key() -> None:
    found, seen = lookup(lambda _: httpx.Response(200, json={"content": [{"carrier": CARRIER}]}))
    assert found == [CARRIER]
    assert seen[0].url.path == "/qc/services/carriers/docket-number/138328/"
    assert seen[0].url.params["webKey"] == KEY


@pytest.mark.parametrize(
    "reply",
    [
        httpx.Response(200, json={"content": []}),
        httpx.Response(200, json={"content": None}),
        httpx.Response(404),
    ],
)
def test_no_record_is_an_empty_list(reply: httpx.Response) -> None:
    assert lookup(lambda _: reply)[0] == []


def test_a_single_record_may_come_without_a_list() -> None:
    found, _ = lookup(lambda _: httpx.Response(200, json={"content": {"carrier": CARRIER}}))
    assert found == [CARRIER]


@pytest.mark.parametrize(
    "reply",
    [
        httpx.Response(403),  # what this machine gets
        httpx.Response(500),
        httpx.Response(200, text="<html>"),
        httpx.Response(200, json={"content": [], "errorMessage": "bad key"}),
        httpx.Response(200, json={"content": ["not a carrier"]}),
        httpx.Response(200, json=[]),
        httpx.Response(200, content=b"x" * (2 * 1024 * 1024 + 1)),
    ],
)
def test_anything_unclear_is_unavailable_and_hides_the_key(reply: httpx.Response) -> None:
    with pytest.raises(FmcsaUnavailable) as caught:
        lookup(lambda _: reply)
    assert KEY not in str(caught.value)


def test_a_network_failure_is_unavailable_and_hides_the_key() -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"cannot reach {request.url}", request=request)

    with pytest.raises(FmcsaUnavailable) as caught:
        lookup(fail)
    assert KEY not in str(caught.value)
    assert KEY not in repr(FmcsaSettings(api_key=KEY))


def test_an_mc_that_is_not_normalized_is_refused_before_any_request() -> None:
    with pytest.raises(ValueError):
        lookup(lambda _: httpx.Response(200, json={"content": []}), mc="MC-138328")
