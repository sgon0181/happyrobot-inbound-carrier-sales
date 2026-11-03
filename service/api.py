"""HTTP routes. Each caller has its own key, and the routes hold no business rules.

Voice routes always answer HTTP 200 with a status the agent can act on, and stop at a
12 second deadline. HTTP errors are kept for a wrong key or a malformed request. Every
route needs a key, health included, and the API docs routes are off (INV-8).
"""

import asyncio
import hmac
import logging
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from typing import Annotated, Protocol

from fastapi import Depends, FastAPI, Header, HTTPException, Path, Request
from fastapi.exceptions import RequestValidationError
from fastapi.params import Depends as Dependency
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from service.adapters.tms.client import TmsUnavailable
from service.adapters.twin import TwinUnavailable
from service.calls import Calls, Reply
from service.dashboard import Dashboard
from service.rep_actions import RepActions
from service.selling import Sales

VOICE_DEADLINE_SECONDS = 12.0
MAX_BODY_BYTES = 16_384
LOAD_ID = r"^[A-Za-z0-9_-]{1,32}$"
RUN_ID = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
log = logging.getLogger("service")


class Reachable(Protocol):
    """What health needs from the TMS client: a round trip that raises TmsUnavailable."""

    async def echo(self) -> None: ...


class Voice(BaseModel):
    """Every voice request names its call. Unknown fields, such as 'verified', are refused.

    The agent may send an MC or code as a JSON number, so numbers are read as text.
    """

    model_config = ConfigDict(extra="forbid", coerce_numbers_to_str=True)
    run_id: str = Field(pattern=RUN_ID)


class VerifyCarrier(Voice):
    mc: str = Field(max_length=32)


class VerifyCode(Voice):
    code: str = Field(max_length=32)


class FindLoads(Voice):
    """Any term may be left out or blank, but at least one is needed."""

    equipment: str | None = Field(default=None, max_length=32)
    origin_state: str | None = Field(default=None, max_length=32)
    dest_state: str | None = Field(default=None, max_length=32)


class Close(Voice):
    summary: str | None = Field(default=None, max_length=4000)


class Negotiate(Voice):
    load_id: str = Field(max_length=32)
    rate: str = Field(max_length=32)  # the carrier's ask, as the agent heard it


class RepAction(BaseModel):
    """A rep's action names the booking version on their screen (D-31) and who they are."""

    model_config = ConfigDict(extra="forbid")
    version: int = Field(ge=1, strict=True)  # the number from the snapshot, never text
    rep: str = Field(min_length=1, max_length=200, pattern=r"\S")


LoadId = Annotated[str, Path(pattern=LOAD_ID)]


def create_app(
    *,
    calls: Calls,
    sales: Sales,
    dashboard: Dashboard,
    desk: RepActions,
    tms: Reachable,
    agent_key: str,
    ops_key: str,
    deadline_seconds: float = VOICE_DEADLINE_SECONDS,
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None,
) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.add_exception_handler(RequestValidationError, _invalid)
    app.add_exception_handler(TwinUnavailable, _unavailable)
    app.middleware("http")(_no_store)
    app.add_middleware(_limit_body)  # added last, so it runs first
    either = Depends(_bearer(agent_key, ops_key))
    _voice_routes(app, calls, sales, Depends(_bearer(agent_key)), deadline_seconds)
    _ops_routes(app, dashboard, desk, Depends(_bearer(ops_key)))

    @app.get("/health", dependencies=[either])
    async def health() -> Reply:
        try:
            await tms.echo()
        except TmsUnavailable:
            return {"status": "ok", "tms": "unreachable"}
        return {"status": "ok", "tms": "reachable"}

    return app


def _voice_routes(
    app: FastAPI, calls: Calls, sales: Sales, agent: Dependency, deadline: float
) -> None:
    def voice(work: Awaitable[Reply]) -> Awaitable[Reply]:
        return _within_deadline(work, deadline)

    @app.post("/carriers/verify", dependencies=[agent])
    async def verify_carrier(body: VerifyCarrier) -> Reply:
        return await voice(calls.verify_carrier(body.run_id, body.mc))

    @app.post("/otp/send", dependencies=[agent])
    async def send_code(body: Voice) -> Reply:
        return await voice(calls.send_code(body.run_id))

    @app.post("/otp/verify", dependencies=[agent])
    async def verify_code(body: VerifyCode) -> Reply:
        return await voice(calls.verify_code(body.run_id, body.code))

    @app.post("/loads/search", dependencies=[agent])
    async def find_loads(body: FindLoads) -> Reply:
        terms = (body.equipment, body.origin_state, body.dest_state)
        return await voice(sales.find_loads(body.run_id, *terms))

    @app.post("/negotiate", dependencies=[agent])
    async def negotiate(body: Negotiate) -> Reply:
        return await voice(sales.negotiate(body.run_id, body.load_id, body.rate))

    @app.post("/calls/close", dependencies=[agent])
    async def close(body: Close) -> Reply:
        return await voice(sales.close(body.run_id, body.summary))


def _ops_routes(app: FastAPI, dashboard: Dashboard, desk: RepActions, ops: Dependency) -> None:
    """The operations app's routes. Rep actions have no voice deadline: they run to the end."""

    async def acted(work: Awaitable[Reply]) -> Reply:
        try:
            return await work
        finally:
            dashboard.forget()  # the rep's next snapshot shows what they did

    @app.get("/ops/snapshot", dependencies=[ops])
    async def snapshot() -> Reply:
        return await dashboard.snapshot()

    @app.post("/bookings/{load_id}/confirm", dependencies=[ops])
    async def confirm(load_id: LoadId, body: RepAction) -> Reply:
        return await acted(desk.confirm(load_id, body.version, body.rep))

    @app.post("/bookings/{load_id}/decline", dependencies=[ops])
    async def decline(load_id: LoadId, body: RepAction) -> Reply:
        return await acted(desk.decline(load_id, body.version, body.rep))

    @app.post("/bookings/{load_id}/reconcile", dependencies=[ops])
    async def reconcile(load_id: LoadId, body: RepAction) -> Reply:
        return await acted(desk.reconcile(load_id, body.version, body.rep))


async def _within_deadline(work: Awaitable[Reply], seconds: float) -> Reply:
    """A voice request answers in time or says it could not. It never hangs the call."""
    try:
        async with asyncio.timeout(seconds):
            return await work
    except (TimeoutError, TwinUnavailable) as error:
        log.warning("Voice request failed: %s", type(error).__name__)
        return {"status": "temporarily_unavailable"}


async def _invalid(request: Request, error: Exception) -> JSONResponse:
    return JSONResponse({"status": "invalid_request"}, 400)  # never echoes the input back


async def _unavailable(request: Request, error: Exception) -> JSONResponse:
    """An operations request that Twin failed. Voice requests answer within their deadline."""
    log.warning("Operations request failed: %s", type(error).__name__)
    return JSONResponse({"status": "temporarily_unavailable"}, 503)


async def _no_store(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


def _limit_body(app: ASGIApp) -> ASGIApp:
    """Read the body before anything else, and refuse it past MAX_BODY_BYTES.

    The bytes received are counted, so a chunked request without a Content-Length is
    limited too, and an oversized body is never held whole in memory.
    """

    async def limited(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await app(scope, receive, send)
            return
        try:
            body = await _read_body(receive)
        except _Disconnected:
            return  # the caller left mid-upload, so the request never happened
        if body is None:
            await JSONResponse({"status": "request_too_large"}, 413)(scope, receive, send)
            return
        pending: list[Message] = [{"type": "http.request", "body": body, "more_body": False}]

        async def replay() -> Message:
            return pending.pop() if pending else await receive()

        await app(scope, replay, send)

    return limited


class _Disconnected(Exception):
    pass


async def _read_body(receive: Receive) -> bytes | None:
    """The whole body, or None as soon as it passes MAX_BODY_BYTES."""
    body, more = b"", True
    while more:
        message = await receive()
        if message["type"] == "http.disconnect":
            raise _Disconnected
        body += message.get("body", b"")
        if len(body) > MAX_BODY_BYTES:
            return None
        more = message.get("more_body", False)
    return body


def _bearer(*keys: str) -> Callable[[str], None]:
    """Accept any one of these keys, compared in constant time."""
    expected = [f"Bearer {key}".encode() for key in keys]

    def check(authorization: Annotated[str, Header()] = "") -> None:
        given = authorization.encode()
        if not any([hmac.compare_digest(given, key) for key in expected]):
            raise HTTPException(401, "unauthorized")

    return check
