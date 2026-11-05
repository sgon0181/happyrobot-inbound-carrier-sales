"""Disposable local review fixture. Never imports real credentials or contacts external services."""

import base64
import json
import secrets
import shutil
import subprocess
import threading
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request

from service.tests.fake_tms import FakeTMS, client_for, make_load
from service.tests.rig import RUN, rig
from service.tests.test_carrier_policy import ACTIVE

TLS = Path("/fixture-tls")
APP_ORIGIN = "http://127.0.0.1:3080"
IDENTITIES = {"rep": "local-review-rep", "viewer": "local-review-viewer"}


def make_token() -> str:
    payload = json.dumps({"exp": int(time.time()) + 86400, "twin_environment": "staging"})
    encoded = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    return f"fixture.{encoded}.{secrets.token_urlsafe(24)}"


TOKENS = {role: make_token() for role in IDENTITIES}
READY = threading.Event()
fixture = rig([ACTIVE | {"legalName": "LOCAL REVIEW FIXTURE CARRIER"}])
fixture.clock.now = datetime.now(UTC)
pickup = fixture.clock.now + timedelta(days=3)
delivery = pickup + timedelta(days=1)
load = make_load(
    PICKUP_DT=pickup.strftime("%Y%m%d%H%M%S"), DELIVERY_DT=delivery.strftime("%Y%m%d%H%M%S")
)
fixture.board.records = [load]
fixture.verified()
if (
    fixture.post("/loads/search", equipment="dry van", origin_state="TX", dest_state="GA")["status"]
    != "found"
):
    raise RuntimeError("Local fixture could not find its load.")
if fixture.post("/negotiate", load_id="LD09001", rate="1850")["status"] != "agreed":
    raise RuntimeError("Local fixture could not reserve its load.")
fixture.post("/calls/close", summary="Disposable local fixture. No real carrier was contacted.")
fixture.post("/calls/ended", ended_by="assistant", duration_seconds=60)
wire = FakeTMS([load])


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    async with wire:
        fixture.desk.tms = client_for(wire)
        READY.set()
        try:
            yield
        finally:
            READY.clear()


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)


@app.get("/api/apps/me")
async def current_user(request: Request) -> dict[str, str]:
    received = request.headers.get("authorization", "")
    for role, token in TOKENS.items():
        if secrets.compare_digest(received, "Bearer " + token):
            return {
                "id": IDENTITIES[role],
                "email": role + "@example.invalid",
                "first_name": "Local fixture",
                "last_name": role,
            }
    raise HTTPException(401)


app.mount("/fixture", fixture.client.app)


class Entry(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.headers.get("Host") not in {"127.0.0.1:3081", "localhost:3081", "127.0.0.1:8081"}:
            self.send_error(400)
            return
        if self.path == "/ready":
            if not READY.is_set():
                self.send_error(503)
                return
            self.respond({"status": "ready", "fixture": True})
            return
        if self.path == "/counts":
            self.respond(
                {
                    "tcp_booking_commands": sum(
                        r.startswith("CMD:LOAD_BOOK|") for r in wire.requests
                    ),
                    "state": fixture.twin.data("bookings", "LD09001")["state"],
                }
            )
            return
        role = self.path.removeprefix("/enter/")
        if self.path != "/enter/" + role or role not in TOKENS:
            self.send_error(404)
            return
        target = f"{APP_ORIGIN}/?view=reservations&load=LD09001&run={RUN}"
        self.send_response(302)
        self.send_header("Location", target)
        self.send_header(
            "Set-Cookie", f"hr_token={TOKENS[role]}; HttpOnly; SameSite=Lax; Path=/; Max-Age=86400"
        )
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def respond(self, data: dict[str, object]) -> None:
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass


def main() -> None:
    TLS.mkdir(parents=True, exist_ok=True)
    # Each forced recreation refreshes the local certificate before the desk starts.
    openssl = shutil.which("openssl")
    if openssl is None:
        raise RuntimeError("The fixture image requires openssl.")
    subprocess.run(  # noqa: S603, resolved executable and fixed arguments
        [
            openssl,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "7",
            "-keyout",
            str(TLS / "key.pem"),
            "-out",
            str(TLS / "ca.pem"),
            "-subj",
            "/CN=fixture",
            "-addext",
            "subjectAltName=DNS:fixture,DNS:localhost,IP:127.0.0.1",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    (TLS / "key.pem").chmod(0o600)
    entry = ThreadingHTTPServer(("0.0.0.0", 8081), Entry)  # noqa: S104, Docker publishes loopback only
    threading.Thread(target=entry.serve_forever, daemon=True).start()
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",  # noqa: S104, container-only TLS provider
            port=8443,
            ssl_keyfile=str(TLS / "key.pem"),
            ssl_certfile=str(TLS / "ca.pem"),
            access_log=False,
        )
    finally:
        entry.shutdown()
        entry.server_close()


if __name__ == "__main__":
    main()
