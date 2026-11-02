"""The verify flow over HTTP: MC check, code sent, code checked, against a fake Twin and FMCSA."""

import asyncio
import json
from collections.abc import Iterator
from datetime import timedelta
from typing import Any

import pytest
from starlette.types import Message, Receive, Scope, Send

from service.api import _limit_body
from service.calls import is_verified
from service.core.carrier_policy import assess
from service.tests.rig import AGENT, OPS, RUN, START, rig
from service.tests.test_carrier_policy import INACTIVE


def test_every_route_needs_its_key_and_the_docs_are_off() -> None:
    r = rig()
    for key in ("", "wrong", OPS):
        assert r.post("/carriers/verify", key=key, mc="138328")["http"] == 401
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert r.client.get(path).status_code == 404
    assert r.client.get("/health").status_code == 401


def test_health_takes_either_key_and_reports_the_tms_honestly() -> None:
    r = rig()
    for key in (AGENT, OPS):
        response = r.client.get("/health", headers={"Authorization": f"Bearer {key}"})
        assert response.json() == {"status": "ok", "tms": "unreachable"}


def test_an_eligible_carrier_is_saved_on_a_new_call_row() -> None:
    r = rig()
    reply = r.post("/carriers/verify", mc="MC-138328")
    assert reply == {"status": "eligible", "carrier_name": "WERNER ENTERPRISES INC", "http": 200}
    row = r.row()
    assert (row["cohort"], row["mc"], row["eligible"], row["outcome"]) == (
        "real",
        "138328",
        True,
        None,
    )
    event = {"at": START.isoformat(), "action": "verify_carrier", "mc": "138328"}
    assert row["events"] == [
        {"seq": 1, **event, "status": "checking", "lookup": 1},
        {"seq": 2, **event, "status": "eligible", "carrier_name": "WERNER ENTERPRISES INC"},
    ]
    assert r.fmcsa.seen == ["/qc/services/carriers/docket-number/138328/"]


def test_a_malformed_mc_is_refused_without_asking_fmcsa() -> None:
    r = rig()
    assert r.post("/carriers/verify", mc="one two three")["status"] == "invalid_mc"
    assert r.fmcsa.seen == []


def test_an_inactive_carrier_cannot_get_a_code() -> None:
    r = rig([INACTIVE])
    assert r.post("/carriers/verify", mc="134652")["status"] == "ineligible"
    assert r.row()["outcome"] == "carrier_ineligible"
    assert r.post("/otp/send")["status"] == "not_eligible"
    assert r.mailer.codes == []


def test_an_unknown_mc_is_not_found() -> None:
    assert rig([]).post("/carriers/verify", mc="99999999")["status"] == "not_found"


def test_fmcsa_failure_is_reported_as_unavailable_not_as_a_result() -> None:
    r = rig(fmcsa_status=403)
    assert r.post("/carriers/verify", mc="138328")["status"] == "fmcsa_unavailable"
    assert (r.row()["outcome"], r.row()["eligible"]) == ("fmcsa_unavailable", False)


def test_the_right_code_verifies_the_call_and_only_its_hash_is_stored() -> None:
    r = rig()
    code = r.verified_with_code()
    assert len(code) == 6
    assert code not in json.dumps(r.row())
    assert r.post("/otp/verify", code=f"{code[:3]} {code[3:]}")["status"] == "verified"
    assert is_verified(r.row())
    assert code not in json.dumps(r.row())  # events hold step results, never a code
    assert r.post("/otp/verify", code=code)["status"] == "verified"  # a repeat is safe


def test_three_wrong_codes_lock_the_call_even_for_the_right_code() -> None:
    r = rig()
    code = r.verified_with_code()
    wrong = "000000" if code != "000000" else "111111"
    replies = [r.post("/otp/verify", code=wrong) for _ in range(3)]
    assert [(x["status"], x.get("tries_left")) for x in replies] == [
        ("wrong_code", 2),
        ("wrong_code", 1),
        ("locked", None),
    ]
    assert r.post("/otp/verify", code=code)["status"] == "locked"
    assert r.row()["outcome"] == "code_failed"


def test_a_code_expires_after_five_minutes() -> None:
    r = rig()
    code = r.verified_with_code()
    r.clock.now = START + timedelta(minutes=5)
    assert r.post("/otp/verify", code=code)["status"] == "expired"


def test_a_third_send_is_refused() -> None:
    r = rig()
    r.verified_with_code()
    assert r.post("/otp/send")["status"] == "sent"
    assert r.post("/otp/send")["status"] == "send_limit"
    assert len(r.mailer.codes) == 2


def test_a_failed_email_still_counts_as_a_send() -> None:
    r = rig(mail_fails=True)
    r.post("/carriers/verify", mc="138328")
    assert r.post("/otp/send")["status"] == "send_failed"
    assert r.row()["otp"]["sends"] == 1
    statuses = [e["status"] for e in r.row()["events"]]
    assert statuses == ["checking", "eligible", "code_issued", "send_failed"]


def test_a_new_mc_needs_a_new_code_but_keeps_the_budgets() -> None:
    r = rig()
    code = r.verified_with_code()
    r.post("/otp/verify", code=code)
    assert r.post("/carriers/verify", mc="1515")["status"] == "eligible"
    assert not is_verified(r.row())
    assert r.post("/otp/verify", code=code)["status"] == "no_code"
    assert r.row()["otp"]["sends"] == 1


@pytest.mark.parametrize(
    "body",
    [
        {"run_id": "not-a-uuid", "mc": "138328"},
        {"run_id": RUN, "mc": "138328", "verified": True},  # the model cannot set state
        {"run_id": RUN},
        {"run_id": RUN, "mc": "1" * 40},
    ],
)
def test_a_malformed_request_is_refused_without_echoing_it(body: dict[str, Any]) -> None:
    response = rig().client.post(
        "/carriers/verify", json=body, headers={"Authorization": f"Bearer {AGENT}"}
    )
    assert (response.status_code, response.json()) == (400, {"status": "invalid_request"})


def test_an_oversized_body_is_refused() -> None:
    response = rig().client.post(
        "/otp/send",
        content=b"x" * 20_000,
        headers={"Authorization": f"Bearer {AGENT}", "Content-Type": "application/json"},
    )
    assert response.status_code == 413


def test_twin_failure_is_temporarily_unavailable() -> None:
    r = rig()
    r.twin.statuses.extend([503])
    assert r.post("/carriers/verify", mc="138328") == {
        "status": "temporarily_unavailable",
        "http": 200,
    }


def test_a_request_past_the_deadline_stops_and_says_so() -> None:
    r = rig(fmcsa_delay=0.5, deadline=0.1)
    assert r.post("/carriers/verify", mc="138328")["status"] == "temporarily_unavailable"
    events = r.row()["events"]  # the call and its MC were saved before FMCSA was asked
    assert [(e["mc"], e["status"]) for e in events] == [("138328", "checking")]


def test_rechecking_the_same_mc_keeps_the_code_already_sent() -> None:
    r = rig()
    code = r.verified_with_code()
    assert r.post("/carriers/verify", mc="138328")["status"] == "eligible"
    assert r.post("/otp/verify", code=code)["status"] == "verified"


def test_a_code_cannot_be_checked_before_the_carrier_is_eligible() -> None:
    r = rig([INACTIVE])
    r.post("/carriers/verify", mc="134652")
    assert r.post("/otp/verify", code="123456")["status"] == "not_eligible"
    assert r.post("/otp/verify", code="12")["status"] == "invalid_code"


class ReachableTms:
    async def echo(self) -> None:
        return None


def test_health_reports_a_reachable_tms() -> None:
    response = rig(tms=ReachableTms()).client.get(
        "/health", headers={"Authorization": f"Bearer {OPS}"}
    )
    assert response.json() == {"status": "ok", "tms": "reachable"}


def test_an_mc_or_code_sent_as_a_json_number_is_read_as_text() -> None:
    r = rig()
    assert r.post("/carriers/verify", mc=138328)["status"] == "eligible"
    assert r.post("/otp/send")["status"] == "sent"
    code = r.mailer.codes[-1]
    expected = "verified" if not code.startswith("0") else "invalid_code"  # a number loses zeros
    assert r.post("/otp/verify", code=int(code))["status"] == expected


def test_a_failed_lookup_for_a_new_mc_drops_the_earlier_verification() -> None:
    r = rig()
    r.post("/otp/verify", code=r.verified_with_code())
    r.fmcsa.status = 403
    assert r.post("/carriers/verify", mc="1515")["status"] == "fmcsa_unavailable"
    row = r.row()
    assert (row["mc"], row["carrier_name"], is_verified(row)) == ("1515", None, False)
    assert row["otp"]["sends"] == 1


def test_each_lookup_records_its_mc_and_result() -> None:
    r = rig()
    r.post("/carriers/verify", mc="138328")
    r.fmcsa.carriers = [INACTIVE]
    r.post("/carriers/verify", mc="134652")
    assert [(e["mc"], e["status"], e.get("reason")) for e in r.row()["events"]] == [
        ("138328", "checking", None),
        ("138328", "eligible", None),
        ("134652", "checking", None),
        ("134652", "ineligible", assess([INACTIVE]).reason),
    ]


def test_a_late_lookup_never_overwrites_a_newer_one() -> None:
    r = rig()

    def caller_gives_another_mc() -> None:  # a newer lookup started, as in A, then B, then A
        version, data = r.twin.tables["calls"][RUN]
        r.twin.tables["calls"][RUN] = (version + 1, {**data, "mc": "1515", "lookup": 2})

    r.fmcsa.during = caller_gives_another_mc
    assert r.post("/carriers/verify", mc="138328")["status"] == "superseded"
    row = r.row()
    assert (row["mc"], row["carrier_name"], row["eligible"]) == ("1515", None, False)


def chunks(*sizes: int) -> Iterator[bytes]:
    yield b'{"run_id": "' + RUN.encode() + b'"}'
    for size in sizes:
        yield b" " * size  # whitespace keeps the JSON valid


def test_a_chunked_body_is_limited_by_the_bytes_received() -> None:
    r = rig()
    headers = {"Authorization": f"Bearer {AGENT}", "Content-Type": "application/json"}
    small = r.client.post("/otp/send", content=chunks(10), headers=headers)
    assert (small.status_code, small.json()["status"]) == (200, "not_eligible")
    large = r.client.post("/otp/send", content=chunks(10_000, 10_000), headers=headers)
    assert (large.status_code, large.json()) == (413, {"status": "request_too_large"})


def test_the_body_is_handed_on_once_then_later_messages_pass_through() -> None:
    arriving: list[Message] = [
        {"type": "http.request", "body": b"ab", "more_body": True},
        {"type": "http.request", "body": b"c", "more_body": False},
        {"type": "http.disconnect"},
    ]
    seen: list[Message] = []

    async def inner(scope: Scope, receive: Receive, send: Send) -> None:
        seen.extend([await receive(), await receive()])

    async def receive() -> Message:
        return arriving.pop(0)

    async def send(message: Message) -> None:
        raise AssertionError("nothing is sent")

    async def request() -> None:
        await _limit_body(inner)({"type": "http"}, receive, send)

    asyncio.run(request())
    body = {"type": "http.request", "body": b"abc", "more_body": False}
    assert seen == [body, {"type": "http.disconnect"}]


def test_a_corrected_mc_does_not_inherit_the_earlier_outcome() -> None:
    r = rig([INACTIVE], deadline=0.2)
    assert r.post("/carriers/verify", mc="134652")["status"] == "ineligible"
    r.fmcsa.delay = 0.5  # the correction's lookup is cut off by the deadline
    assert r.post("/carriers/verify", mc="1515")["status"] == "temporarily_unavailable"
    assert (r.row()["mc"], r.row()["authority"], r.row()["outcome"]) == ("1515", None, None)


def test_a_disconnect_mid_upload_never_reaches_the_app() -> None:
    arriving: list[Message] = [
        {"type": "http.request", "body": b"{}", "more_body": True},
        {"type": "http.disconnect"},
    ]
    called: list[bool] = []

    async def inner(scope: Scope, receive: Receive, send: Send) -> None:
        called.append(True)

    async def receive() -> Message:
        return arriving.pop(0)

    async def send(message: Message) -> None:
        raise AssertionError("nothing is sent")

    async def request() -> None:
        await _limit_body(inner)({"type": "http"}, receive, send)

    asyncio.run(request())
    assert called == []
