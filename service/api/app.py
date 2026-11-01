"""Single instance API. All business state is in Production Twin."""

import asyncio
from contextlib import asynccontextmanager, suppress
import hmac
import json
import re
import time
import uuid
from types import SimpleNamespace
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from service.config import settings
from service.adapters.tms.client import TmsClient, TmsSettings
from service.adapters.tms.evidence import ReceiptJournal
from service.adapters.fmcsa.client import FMCSAClient
from service.adapters.notify.email import EmailNotifier
from service.adapters.twin.client import Platform
from service.adapters.twin.repository import TwinRepository
from service.core.calls import Runtime
from service.core.booking import agent_view
from service.adapters.confirmation import NativeConfirmation


def redact_transcript(messages):
    """Redact literal and spoken six-digit codes, including failed attempts."""
    lines = []
    tools = []
    submitted = []
    # Coalesce adjacent speaker fragments before redaction. ASR may split one
    # six-digit attempt into two messages containing three digits each.
    joined = []
    for message in messages:
        if isinstance(message.get("content"), str) and message["content"].startswith("<Thoughts>"):
            continue
        if (
            joined
            and message.get("role") in ("user", "assistant")
            and joined[-1].get("role") == message.get("role")
            and isinstance(message.get("content"), str)
            and isinstance(joined[-1].get("content"), str)
        ):
            joined[-1]["content"] += " " + message["content"]
            joined[-1]["tool_calls"] = (joined[-1].get("tool_calls") or []) + (
                message.get("tool_calls") or []
            )
        else:
            joined.append(dict(message))
    for message in joined:
        for tool in message.get("tool_calls") or []:
            function = tool.get("function") or {}
            name = tool.get("name") or function.get("name")
            if name != "verify_code":
                continue
            arguments = tool.get("arguments", function.get("arguments", tool.get("args", {})))
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except ValueError:
                    continue
            code = arguments.get("code") if isinstance(arguments, dict) else None
            if isinstance(code, (str, int)) and re.fullmatch(r"[0-9]{6}", str(code)):
                submitted.append(str(code))
    words = r"(?:zero|oh|one|two|three|four|five|six|seven|eight|nine)"
    for message in joined:
        for tool in message.get("tool_calls") or []:
            name = tool.get("name") or (tool.get("function") or {}).get("name")
            if name:
                tools.append(name)
        if message.get("role") not in ("user", "assistant"):
            continue
        text = message.get("content")
        if not isinstance(text, str) or not text or text.startswith("<Thoughts>"):
            continue
        for code in submitted:
            text = re.sub(r"(?<!\d)" + r"[\s,.-]*".join(code) + r"(?!\d)", "[code redacted]", text)
        text = re.sub(r"\b[0-9]{6}\b", "[code redacted]", text)
        text = re.sub(
            r"\b" + words + r"(?:[\s,-]+" + words + r"){5}\b",
            "[spoken code redacted]",
            text,
            flags=re.I,
        )
        text = re.sub(r"(?<!\d)(?:\d[ ,.-]){5}\d(?!\d)", "[code redacted]", text)
        lines.append(message["role"] + ": " + text)
    return "\n".join(lines), tools


def make_app(runtime, values, platform=None):
    async def collect():
        if platform is None:
            return {"status": "unavailable", "collected": 0}
        collected = {}
        calls = await runtime.repository.rows("calls", filters={"cohort": "real"}, limit=40)
        for cid, _, call in calls:
            _, previous = await runtime.repository.get("call_transcripts", cid)
            if (
                not call.get("closed_at")
                or call["cohort"] != "real"
                or (previous or {}).get("redaction_version") == 2
            ):
                continue
            try:
                run = await asyncio.to_thread(platform.request, "/runs/" + cid)
                if run.get("workflow_id") != values.get("PROTOTYPE_WORKFLOW_ID"):
                    continue
                sessions = await asyncio.to_thread(platform.request, "/runs/" + cid + "/sessions")
                all_messages = []
                complete = True
                for session in sessions.get("data", []):
                    cursor = None
                    page = 1
                    for _ in range(30):
                        suffix = ("?cursor=" + cursor) if cursor else ("?page=" + str(page))
                        response = await asyncio.to_thread(
                            platform.request, "/sessions/" + session["id"] + "/messages" + suffix
                        )
                        all_messages.extend(response.get("data", []))
                        cursor = response.get("next_cursor") or (
                            response.get("pagination") or {}
                        ).get("next_cursor")
                        if not cursor and not (response.get("pagination") or {}).get(
                            "has_next_page"
                        ):
                            break
                        page += 1
                    else:
                        complete = False
                text, tools = redact_transcript(all_messages)
                if text:
                    collected[cid] = {
                        "call_id": cid,
                        "transcript": text,
                        "tools": tools,
                        "complete": complete,
                        "summary": "Recorded outcome: " + str(call.get("outcome")),
                        "summary_source": "DETERMINISTIC_PROTOTYPE",
                        "notes": "Live platform transcript, codes redacted.",
                        "sentiment": "not_assessed",
                        "source": "LIVE_PLATFORM_TRANSCRIPT",
                        "redaction_version": 2,
                    }
            except Exception:
                continue

        for cid, row in collected.items():
            await runtime.repository.upsert("call_transcripts", cid, row)
        return {"status": "ok", "collected": len(collected)}

    @asynccontextmanager
    async def lifespan(app):
        # Provisioning is an explicit setup command. Runtime never attempts DDL.
        await runtime.repository.rows("calls", limit=1)
        await runtime.bookings.recover()

        async def sweep():
            while True:
                await asyncio.sleep(45)
                try:
                    for cid, _, call in await runtime.repository.rows("calls"):
                        if (
                            not call.get("closed_at")
                            and time.time() - call["last_activity"] >= 1800
                        ):
                            await runtime.close(cid)
                    await collect()
                except Exception:
                    pass

        task = asyncio.create_task(sweep())
        yield
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        if runtime.bookings.pending:
            await asyncio.gather(*runtime.bookings.pending, return_exceptions=True)

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)

    @app.middleware("http")
    async def protect(request, call_next):
        started = time.monotonic()
        ops = request.url.path.startswith("/ops/") or (
            request.url.path.startswith("/bookings")
            and (
                request.method == "GET"
                or re.fullmatch(r"/bookings/[^/]+/(confirm|decline|reconcile)", request.url.path)
            )
        )
        expected = values["OPS_API_KEY" if ops else "AGENT_API_KEY"]
        if not hmac.compare_digest(
            request.headers.get("authorization", "").encode(), ("Bearer " + expected).encode()
        ):
            return JSONResponse({"status": "unauthorized"}, 401)
        try:
            if int(request.headers.get("content-length", "0")) > 16384:
                return JSONResponse({"status": "request_too_large"}, 413)
        except ValueError:
            return JSONResponse({"status": "invalid_request"}, 400)
        request.state.deadline = asyncio.get_running_loop().time() + 12
        try:
            async with asyncio.timeout(12):
                response = await call_next(request)
        except TimeoutError:
            response = JSONResponse(
                {
                    "status": (
                        "in_progress"
                        if request.url.path == "/bookings"
                        else "temporarily_unavailable"
                    )
                }
            )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Service-Duration-Ms"] = str(
            round((time.monotonic() - started) * 1000, 1)
        )
        return response

    @app.exception_handler(ValueError)
    @app.exception_handler(KeyError)
    async def invalid(request, error):
        return JSONResponse({"status": "invalid_request"}, 400)

    async def body(request):
        raw = await request.body()
        if len(raw) > 16384:
            raise ValueError("Request too large")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("JSON object required")
        return data

    def identity(data):
        cid = data["run_id"]
        if not isinstance(cid, str) or str(uuid.UUID(cid)) != cid.lower():
            raise ValueError("Runtime run ID required")
        if any(
            key in data
            for key in ("call_id", "call_token", "operation_id", "verified", "eligible", "max_rate")
        ):
            raise ValueError("Untrusted state field")
        return cid

    async def execute(request, action):
        data = await body(request)
        cid = identity(data)
        lock = runtime.locks.setdefault(cid, asyncio.Lock())
        async with lock:
            try:
                result = await action(cid, data)
                if result.get("status") in {
                    "no_match",
                    "carrier_ineligible",
                    "code_failed",
                    "negotiation_failed",
                    "pricing_review_required",
                    "tms_unavailable",
                    "confirmation_unavailable",
                    "not_booked",
                    "booking_failed",
                    "senior_review",
                    "consent_verified",
                }:
                    result = {**result, "end_call_required": True}
                return result
            except (KeyError, ValueError):
                raise
            except Exception:
                return {"status": "temporarily_unavailable"}

    @app.get("/health")
    async def health():
        try:
            await runtime.tms.echo()
            return {
                "status": "ok",
                "store": runtime.repository.label,
                "booking_mode": runtime.booking_mode,
            }
        except Exception:
            return {"status": "tms_unavailable"}

    @app.post("/carriers/verify")
    async def carrier(request: Request):
        return await execute(request, lambda cid, b: runtime.verify_carrier(cid, b["mc"]))

    @app.post("/otp/send")
    async def send(request: Request):
        return await execute(request, lambda cid, b: runtime.send_code(cid))

    @app.post("/otp/verify")
    async def verify(request: Request):
        return await execute(request, lambda cid, b: runtime.verify_code(cid, b["code"]))

    @app.post("/loads/search")
    async def search(request: Request):
        return await execute(
            request,
            lambda cid, b: runtime.search(
                cid,
                {
                    k: b[k]
                    for k in (
                        "equipment",
                        "origin_state",
                        "dest_state",
                        "origin_city",
                        "pickup_date",
                    )
                    if b.get(k)
                },
            ),
        )

    @app.post("/negotiate")
    async def negotiate(request: Request):
        return await execute(
            request, lambda cid, b: runtime.negotiate(cid, b["load_id"], b["rate"])
        )

    @app.post("/bookings")
    async def book(request: Request):
        data = await body(request)
        if any(k in data for k in ("rate", "mc", "load_id")):
            raise ValueError("Booking uses stored agreement")
        return await execute(request, lambda cid, b: runtime.book(cid, request.state.deadline))

    @app.post("/calls/{cid}/close")
    async def close(cid: str, request: Request):
        data = await body(request)
        if identity(data) != cid:
            raise ValueError("Run ID mismatch")
        return await runtime.close(cid)

    @app.get("/bookings")
    async def bookings():
        return {"status": "ok", "bookings": (await runtime.snapshot())["queue"]}

    @app.get("/ops/snapshot")
    async def snapshot():
        return await runtime.snapshot()

    @app.post("/bookings/{bid}/{action}")
    async def rep(bid: str, action: str, request: Request):
        if action not in ("confirm", "decline", "reconcile"):
            raise ValueError("Unknown action")
        data = await body(request)
        actor = data.get("actor")
        if not isinstance(actor, str) or not actor.strip() or len(actor) > 200:
            raise ValueError("Signed-in rep required")
        booking = await (
            runtime.bookings.reconcile(bid)
            if action == "reconcile"
            else getattr(runtime.bookings, action)(bid, actor)
        )

        def audit(state):
            runtime.event(
                state,
                booking.call_id,
                "rep_" + action,
                booking.state.value,
                actor=actor,
                booking_id=bid,
            )

        from service.adapters.twin.repository import empty

        state = empty()
        audit(state)
        for key, row in state["call_events"].items():
            runtime.repository.defer_aux("call_events", key, row)
        return {
            "status": "ok",
            "state": booking.state.value,
            "rep_decision": booking.rep_decision.value,
        }

    @app.post("/ops/collect-transcripts")
    async def transcripts():
        return await collect()

    @app.post("/ops/fmcsa-probe")
    async def authority(request: Request):
        data = await body(request)
        mc = data["mc"]
        try:
            return await runtime.authority(str(mc))
        except Exception:
            return {"status": "fmcsa_unavailable"}

    @app.post("/ops/calls/{cid}/qa")
    async def mark_qa(cid: str):
        if str(uuid.UUID(cid)) != cid.lower():
            raise ValueError("Run ID required")

        def change(data):
            if data["calls"].get(cid, {}).get("booking_id"):
                raise ValueError("A reserved call cannot be relabelled as QA.")
            if any(
                b["call_id"] == cid and (b.get("write_intent_id") or b.get("reference"))
                for b in data["bookings"].values()
            ):
                raise ValueError("A spent or acknowledged call cannot be relabelled as QA.")
            call = data["calls"].setdefault(cid, runtime.new_call(cid))
            call.update(cohort="synthetic", qa_source="HYBRID_INTEGRATION_CHECK")
            return {"status": "ok"}

        return await runtime.repository.update_call(
            cid, lambda data, call: change(data), runtime.new_call(cid)
        )

    app.state.runtime = runtime
    return app


def configured_app():
    values = settings()
    for key in ("AGENT_API_KEY", "OPS_API_KEY", "OTP_HASH_SECRET", "PRICING_SECRET"):
        if len(values.get(key, "")) < 24:
            raise RuntimeError("Private service configuration required")
    for key in ("HAPPYROBOT_ORG_ID", "FMCSA_API_KEY", "OTP_EMAIL_CREDENTIAL", "DEMO_OTP_EMAIL"):
        if not values.get(key):
            raise RuntimeError("Private configuration required: " + key)
    platform = Platform(values)
    repository = TwinRepository(platform, values.get("TWIN_TABLE_PREFIX", "proto_"))
    tms = TmsClient(
        TmsSettings(
            values["TMS_HOST"],
            int(values["TMS_PORT"]),
            values["TMS_TOKEN"],
            booking_enabled=values.get("BOOKING_MODE", "off") == "live",
        ),
        ReceiptJournal(values.get("RECEIPT_JOURNAL_DIR", "/tmp/carrier-receipts")),
    )
    fmcsa = FMCSAClient(SimpleNamespace(fmcsa_api_key=values["FMCSA_API_KEY"], timeout=5))

    async def authority(mc):
        record = await asyncio.to_thread(fmcsa.lookup, mc)
        record["source"] = "LIVE_FMCSA"
        return record

    runtime = Runtime(
        repository,
        tms,
        authority,
        EmailNotifier(values, platform),
        values,
        confirmation=NativeConfirmation(platform, values.get("PROTOTYPE_WORKFLOW_ID")),
    )
    return make_app(runtime, values, platform)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(configured_app(), host="0.0.0.0", port=8767, access_log=False)
