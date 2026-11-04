"""One app over HTTP with every outside system faked: Twin, FMCSA, email and the TMS."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from fastapi.testclient import TestClient

from service.adapters.email import EmailFailed
from service.adapters.fmcsa import Fmcsa, FmcsaSettings
from service.adapters.tms.client import Sent, TmsClient, TmsSettings, TmsUnavailable
from service.adapters.tms.mapping import to_load, to_summary
from service.adapters.tms.protocol import parse_reply
from service.api import Reachable, create_app
from service.bookings import Bookings
from service.calls import CallRows, Calls
from service.config import POLICY_DIR
from service.core.models import Load, LoadSummary
from service.core.pricing import PricingPolicy
from service.dashboard import Dashboard
from service.rep_actions import RepActions
from service.selling import Sales
from service.tests.fake_twin import FakeTwin
from service.tests.test_carrier_policy import ACTIVE

RUN = "3f2b8c1e-0d4a-4c1b-9a6e-2f1d5e7c9b10"
AGENT, OPS = "agent-key-" + "a" * 20, "ops-key-" + "o" * 20
START = datetime(2026, 11, 2, 12, tzinfo=UTC)
PRICING = PricingPolicy.from_json((POLICY_DIR / "pricing-v1.json").read_text())
BLOCKED = frozenset({"LD01086"})


class FakeMailer:
    def __init__(self, *, fail: bool = False) -> None:
        self.codes: list[str] = []
        self.fail = fail

    async def send(self, code: str, mc: str) -> None:
        if self.fail:
            raise EmailFailed("down")
        self.codes.append(code)


@dataclass
class Clock:
    now: datetime = START

    def __call__(self) -> datetime:
        return self.now


@dataclass
class FakeFmcsa:
    carriers: list[dict[str, Any]]
    status: int = 200
    delay: float = 0.0
    during: Callable[[], None] = lambda: None  # runs while a lookup is in flight
    seen: list[str] = field(default_factory=list)

    async def reply(self, request: httpx.Request) -> httpx.Response:
        self.seen.append(request.url.path)
        await asyncio.sleep(self.delay)
        self.during()
        content = [{"carrier": c} for c in self.carriers]
        return httpx.Response(self.status, json={"content": content})


PENDING_RECEIPT = (
    b"LOAD_ID:LD09001     |BOOKING_REF:FIXTURE01|STATUS:PENDING |TIMESTAMP:20261103010203\r\n"
    b"END\r\n"
)


def sent(raw: bytes, step: str = "received", error: str | None = None) -> Sent:
    """A LOAD_BOOK outcome, parsed as the client would parse it."""
    return Sent(step, error, raw, parse_reply(raw) if error is None else None)


@dataclass
class FakeBoard:
    """The TMS reads that selling needs, from TMS-shaped records, without a socket."""

    records: list[dict[str, str]] = field(default_factory=list)
    down: bool = False
    unreadable: set[str] = field(default_factory=set)  # load IDs whose details fail to read
    queries: list[dict[str, Any]] = field(default_factory=list)
    during: Callable[[], None] = lambda: None  # runs while a search is in flight
    reading: Callable[[str], None] = lambda load_id: None  # runs while details are read
    details: dict[str, dict[str, str]] = field(default_factory=dict)  # differ from the search
    sends: list[tuple[str, str, int]] = field(default_factory=list)  # every LOAD_BOOK asked for
    receipt: Sent = field(default_factory=lambda: sent(PENDING_RECEIPT))
    sending: Callable[[], Awaitable[None]] | None = None  # runs while a booking is in flight

    async def query(
        self,
        *,
        equipment: str | None = None,
        origin_state: str | None = None,
        dest_state: str | None = None,
        limit: int = 20,
    ) -> list[LoadSummary]:
        if self.down:
            raise TmsUnavailable("down")
        self.queries.append({"equipment": equipment, "origin": origin_state, "dest": dest_state})
        self.during()
        return [to_summary(record) for record in self.records][:limit]

    async def get(self, load_id: str) -> Load | None:
        self.reading(load_id)
        if self.down or load_id in self.unreadable:
            raise TmsUnavailable("down")
        listed = next((r for r in self.records if r["LOAD_ID"] == load_id), None)
        record = self.details.get(load_id, listed)
        return None if record is None else to_load(record)

    async def book(self, load_id: str, mc: str, rate: int) -> Sent:
        self.sends.append((load_id, mc, rate))
        if self.sending is not None:
            await self.sending()
        return self.receipt


@dataclass
class Rig:
    client: TestClient
    twin: FakeTwin
    mailer: FakeMailer
    clock: Clock
    fmcsa: FakeFmcsa
    board: FakeBoard
    dashboard: Dashboard
    desk: RepActions

    def post(self, path: str, key: str = AGENT, **body: Any) -> Any:
        response = self.client.post(
            path, json={"run_id": RUN, **body}, headers={"Authorization": f"Bearer {key}"}
        )
        return response.json() | {"http": response.status_code}

    def get(self, path: str, key: str = OPS) -> Any:
        response = self.client.get(path, headers={"Authorization": f"Bearer {key}"})
        return response.json() | {"http": response.status_code}

    def row(self) -> dict[str, Any]:
        return self.twin.data("calls", RUN)

    def verified_with_code(self) -> str:
        assert self.post("/carriers/verify", mc="MC-138328")["status"] == "eligible"
        assert self.post("/otp/send")["status"] == "sent"
        return self.mailer.codes[-1]

    def verified(self) -> None:
        assert self.post("/otp/verify", code=self.verified_with_code())["status"] == "verified"

    def booking(self, load_id: str, state: str, call_id: str = "another-call") -> None:
        self.twin.tables["bookings"][load_id] = (1, {"state": state, "call_id": call_id})


def rig(
    carriers: list[dict[str, Any]] | None = None,
    *,
    fmcsa_status: int = 200,
    fmcsa_delay: float = 0.0,
    mail_fails: bool = False,
    deadline: float = 12.0,
    tms: Reachable | None = None,
    live_booking: bool = True,
) -> Rig:
    found = [ACTIVE] if carriers is None else carriers
    fake = FakeFmcsa(found, status=fmcsa_status, delay=fmcsa_delay)
    twin, mailer, clock, board = FakeTwin(), FakeMailer(fail=mail_fails), Clock(), FakeBoard()
    rows = CallRows(twin=twin.twin(), cohort="real", now=clock)
    fmcsa = Fmcsa(FmcsaSettings(api_key="k"), httpx.MockTransport(fake.reply))
    calls = Calls(
        rows=rows, fmcsa=fmcsa, mailer=mailer, code_secret=b"s" * 24, trusted_contacts=True
    )
    sales = Sales(
        rows=rows,
        board=board,
        bookings=Bookings(rows.twin),
        pricing=PRICING,
        pricing_secret=b"p" * 24,
        blocked=BLOCKED,
        display_timezone=ZoneInfo("America/Chicago"),
    )
    dashboard = Dashboard(rows.twin, live_booking=live_booking, now=clock)
    desk = RepActions(
        twin=rows.twin,
        tms=board,
        live=live_booking,
        blocked=BLOCKED,
        now=clock,
        save_pause=0.0,
    )
    closed_port = TmsSettings(
        host="127.0.0.1", port=9, token="t", read_budget_seconds=0.2, attempt_seconds=0.1
    )
    app = create_app(
        calls=calls,
        sales=sales,
        dashboard=dashboard,
        desk=desk,
        tms=tms or TmsClient(closed_port),
        agent_key=AGENT,
        ops_key=OPS,
        deadline_seconds=deadline,
    )
    return Rig(TestClient(app), twin, mailer, clock, fake, board, dashboard, desk)
