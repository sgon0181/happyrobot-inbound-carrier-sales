"""Builds the settings, adapters and app: the only place that connects the parts.

Run with `uvicorn --factory service.main:create`, so settings load at startup, not at import.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from service.adapters.email import CodeMailer, EmailSettings
from service.adapters.fmcsa import Fmcsa, FmcsaSettings
from service.adapters.tms.client import TmsClient, TmsSettings
from service.adapters.twin import Twin, TwinSettings
from service.api import create_app
from service.bookings import Bookings
from service.calls import CallRows, Calls
from service.config import Settings, load_settings
from service.dashboard import Dashboard
from service.rep_actions import RepActions
from service.selling import Sales

# httpx logs each request URL at INFO level, and FMCSA's URL carries the webKey.
logging.getLogger("httpx").setLevel(logging.WARNING)


def build(settings: Settings) -> FastAPI:
    twin = Twin(TwinSettings(api_key=settings.twin_api_key, org_id=settings.twin_org_id))
    fmcsa = Fmcsa(FmcsaSettings(api_key=settings.fmcsa_api_key))
    email = EmailSettings(
        user=settings.email_user, credential=settings.email_credential, inbox=settings.demo_inbox
    )
    tms = TmsClient(
        TmsSettings(host=settings.tms_host, port=settings.tms_port, token=settings.tms_token)
    )
    rows = CallRows(twin=twin, cohort=settings.cohort)
    calls = Calls(
        rows=rows, fmcsa=fmcsa, mailer=CodeMailer(email), code_secret=settings.otp_hash_secret
    )
    sales = Sales(
        rows=rows,
        board=tms,
        bookings=Bookings(twin),
        pricing=settings.pricing,
        pricing_secret=settings.pricing_secret,
        blocked=settings.blocked_loads,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        await twin.close()
        await fmcsa.close()

    return create_app(
        calls=calls,
        sales=sales,
        dashboard=Dashboard(twin),
        desk=RepActions(
            twin=twin, tms=tms, live=settings.live_booking, blocked=settings.blocked_loads
        ),
        tms=tms,
        agent_key=settings.agent_api_key,
        ops_key=settings.ops_api_key,
        lifespan=lifespan,
    )


def create() -> FastAPI:
    return build(load_settings())
