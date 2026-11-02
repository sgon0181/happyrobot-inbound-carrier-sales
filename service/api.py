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

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from service.adapters.tms.client import TmsUnavailable
from service.adapters.twin import TwinUnavailable
from service.calls import Calls, Reply

VOICE_DEADLINE_SECONDS = 12.0
MAX_BODY_BYTES = 16_384
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


def create_app(
    *,
    calls: Calls,
    tms: Reachable,
    agent_key: str,
    ops_key: str,
    deadline_seconds: float = VOICE_DEADLINE_SECONDS,
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None,
) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.add_exception_handler(RequestValidationError, _invalid)
    app.middleware("http")(_limit_size)
    agent = Depends(_bearer(agent_key))
    either = Depends(_bearer(agent_key, ops_key))

    def voice(work: Awaitable[Reply]) -> Awaitable[Reply]:
        return _within_deadline(work, deadline_seconds)

    @app.post("/carriers/verify", dependencies=[agent])
    async def verify_carrier(body: VerifyCarrier) -> Reply:
        return await voice(calls.verify_carrier(body.run_id, body.mc))

    @app.post("/otp/send", dependencies=[agent])
    async def send_code(body: Voice) -> Reply:
        return await voice(calls.send_code(body.run_id))

    @app.post("/otp/verify", dependencies=[agent])
    async def verify_code(body: VerifyCode) -> Reply:
        return await voice(calls.verify_code(body.run_id, body.code))

    @app.get("/health", dependencies=[either])
    async def health() -> Reply:
        try:
            await tms.echo()
        except TmsUnavailable:
            return {"status": "ok", "tms": "unreachable"}
        return {"status": "ok", "tms": "reachable"}

    return app


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


async def _limit_size(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    length = request.headers.get("content-length", "0")
    if not length.isdigit() or int(length) > MAX_BODY_BYTES:
        return JSONResponse({"status": "request_too_large"}, 413)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


def _bearer(*keys: str) -> Callable[[str], None]:
    """Accept any one of these keys, compared in constant time."""
    expected = [f"Bearer {key}".encode() for key in keys]

    def check(authorization: Annotated[str, Header()] = "") -> None:
        given = authorization.encode()
        if not any([hmac.compare_digest(given, key) for key in expected]):
            raise HTTPException(401, "unauthorized")

    return check
