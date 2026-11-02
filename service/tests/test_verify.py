"""The verify flow over HTTP: MC check, code sent, code checked, against a fake Twin and FMCSA."""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from service.adapters.email import EmailFailed
from service.adapters.fmcsa import Fmcsa, FmcsaSettings
from service.adapters.tms.client import TmsClient, TmsSettings
from service.api import Reachable, create_app
from service.calls import Calls, is_verified
from service.tests.fake_twin import FakeTwin
from service.tests.test_carrier_policy import ACTIVE, INACTIVE

RUN = "3f2b8c1e-0d4a-4c1b-9a6e-2f1d5e7c9b10"
AGENT, OPS = "agent-key-" + "a" * 20, "ops-key-" + "o" * 20
START = datetime(2026, 11, 2, 12, tzinfo=UTC)


class FakeMailer:
    def __init__(self, *, fail: bool = False) -> None:
        self.codes: list[str] = []
        self.fail = fail

    async def send(self, code: str) -> None:
        if self.fail:
            raise EmailFailed("down")
        self.codes.append(code)


@dataclass
class Clock:
    now: datetime = START

    def __call__(self) -> datetime:
        return self.now


@dataclass
class Rig:
    client: TestClient
    twin: FakeTwin
    mailer: FakeMailer
    clock: Clock
    fmcsa_calls: list[str] = field(default_factory=list)

    def post(self, path: str, key: str = AGENT, **body: Any) -> Any:
        response = self.client.post(
            path, json={"run_id": RUN, **body}, headers={"Authorization": f"Bearer {key}"}
        )
        return response.json() | {"http": response.status_code}

    def row(self) -> dict[str, Any]:
        return self.twin.data("calls", RUN)

    def verified_with_code(self) -> str:
        assert self.post("/carriers/verify", mc="MC-138328")["status"] == "eligible"
        assert self.post("/otp/send")["status"] == "sent"
        return self.mailer.codes[-1]


def rig(
    carriers: list[dict[str, Any]] | None = None,
    *,
    fmcsa_status: int = 200,
    fmcsa_delay: float = 0.0,
    mail_fails: bool = False,
    deadline: float = 12.0,
    tms: Reachable | None = None,
) -> Rig:
    found = [ACTIVE] if carriers is None else carriers
    seen: list[str] = []

    async def fmcsa_reply(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        await asyncio.sleep(fmcsa_delay)
        return httpx.Response(fmcsa_status, json={"content": [{"carrier": c} for c in found]})

    twin, mailer, clock = FakeTwin(), FakeMailer(fail=mail_fails), Clock()
    fmcsa = Fmcsa(FmcsaSettings(api_key="k"), httpx.MockTransport(fmcsa_reply))
    calls = Calls(
        twin=twin.twin(),
        fmcsa=fmcsa,
        mailer=mailer,
        code_secret=b"s" * 24,
        cohort="real",
        now=clock,
    )
    closed_port = TmsSettings(
        host="127.0.0.1", port=9, token="t", read_budget_seconds=0.2, attempt_seconds=0.1
    )
    tms = tms or TmsClient(closed_port)
    app = create_app(calls=calls, tms=tms, agent_key=AGENT, ops_key=OPS, deadline_seconds=deadline)
    return Rig(TestClient(app), twin, mailer, clock, seen)


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
    assert row["events"] == [
        {"seq": 1, "at": START.isoformat(), "action": "verify_carrier", "status": "eligible"}
    ]
    assert r.fmcsa_calls == ["/qc/services/carriers/docket-number/138328/"]


def test_a_malformed_mc_is_refused_without_asking_fmcsa() -> None:
    r = rig()
    assert r.post("/carriers/verify", mc="one two three")["status"] == "invalid_mc"
    assert r.fmcsa_calls == []


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
    assert [e["status"] for e in r.row()["events"]] == ["eligible", "code_issued", "send_failed"]


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
