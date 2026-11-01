"""HYBRID native active chat with synthetic code proof and ZERO live bookings.

Real FMCSA, email and load reads. QA classification and the atomic BookingStore
both prevent a live send. This does not stand in for the owner's live call.
"""

import asyncio
import hashlib
import hmac
import json
import time
from pathlib import Path
import httpx
from service.config import settings, ROOT
from service.adapters.twin.repository import TwinRepository

WORKFLOW = "01a19476-5384-704b-9c5e-569fd96f9adf"
HOST = "https://codex-e2e-lab-sg-20261031.fly.dev"


async def main():
    v = settings()
    api_headers = {
        "Authorization": "Bearer " + v["HAPPYROBOT_API_KEY"],
        "x-organization-id": v.get("HAPPYROBOT_ORG_ID", "01a17a99-0856-7f88-b09f-4b787e20413c"),
        "x-twin-environment": "production",
    }
    async with httpx.AsyncClient(
        base_url="https://platform.happyrobot.ai/api/v2", headers=api_headers, timeout=20
    ) as platform, httpx.AsyncClient(base_url=HOST, timeout=20) as service:

        class P:
            async def sql(self, sql):
                r = await platform.post("/twin/sql", json={"sql": sql})
                r.raise_for_status()
                return r.json()

        repository = TwinRepository(P())
        _, before = await repository.read()
        baseline = set(before["calls"])
        old_intents = {
            b.get("write_intent_id")
            for b in before["bookings"].values()
            if b.get("write_intent_id")
        }
        ops = {"Authorization": "Bearer " + v["OPS_API_KEY"]}
        r = await platform.post(
            "/chat/tokens/",
            json={"workflow_id": WORKFLOW, "env": "development", "ttl_seconds": 900, "data": {}},
        )
        r.raise_for_status()
        token = r.json()["token"]
        headers = {"Authorization": "Bearer " + token}
        r = await platform.post("/chat/sessions/", headers=headers)
        r.raise_for_status()
        sid = r.json()["session_id"]
        private = ROOT / "secrets/active-consent-session.json"
        private.write_text(json.dumps({"session_id": sid, "token": token}))
        private.chmod(0o600)
        print("Native QA session created", sid, flush=True)

        async def send(text):
            r = await platform.post(
                "/chat/sessions/" + sid + "/messages", headers=headers, json={"content": text}
            )
            r.raise_for_status()

        async def wait_for(predicate, label, seconds=50):
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                _, d = await repository.read()
                answer = predicate(d)
                if answer:
                    return d, answer
                await asyncio.sleep(1)
            raise RuntimeError("Timed out at " + label)

        async def history():
            r = await platform.get("/chat/sessions/" + sid + "/history", headers=headers)
            r.raise_for_status()
            return r.json()

        cid = None
        try:
            await send("My MC is 138328.")
            _, call = await wait_for(
                lambda d: next(
                    (
                        c
                        for key, c in d["calls"].items()
                        if key not in baseline and c.get("mc") == "138328"
                    ),
                    None,
                ),
                "authority",
            )
            cid = call["id"]
            r = await service.post("/ops/calls/" + cid + "/qa", headers=ops, json={})
            r.raise_for_status()
            print("Call classified synthetic before verification or booking", cid, flush=True)
            _, call = await wait_for(
                lambda d: (d["calls"][cid] if d["calls"][cid].get("challenge") else None),
                "code issuance",
            )
            code = "000001"

            def fixture(d):
                call = d["calls"][cid]
                assert call["cohort"] == "synthetic"
                challenge = d["otp_challenges"][call["challenge"]]
                challenge.update(
                    hash=hmac.new(
                        v["OTP_HASH_SECRET"].encode(),
                        (cid + "|138328|" + code).encode(),
                        hashlib.sha256,
                    ).hexdigest(),
                    delivery_status="sent",
                    proof_source="SIMULATED_QA_CODE",
                )

            await repository.update(fixture)
            await send("My code is " + code + ". I need a dry van from Arkansas to New York.")
            _, call = await wait_for(
                lambda d: d["calls"][cid] if d["calls"][cid].get("offers") else None, "load search"
            )
            load_id, offer = next(iter(call["offers"].items()))
            await send("I need 25 dollars more than your opening offer, please.")
            await asyncio.sleep(3)
            _, d = await repository.read()
            call = d["calls"][cid]
            if not call.get("agreement"):
                offered = call["offers"][load_id]["current_offer"]
                await send("I accept the returned total of " + str(offered) + " dollars.")
            _, agreement = await wait_for(lambda d: d["calls"][cid].get("agreement"), "agreement")
            await wait_for(
                lambda d: (d["calls"][cid].get("agreement") or {}).get("confirmation_anchor"),
                "confirmation question",
            )
            print("Native first consent check reached service, no booking submitted", flush=True)
            await send(
                "I am clarifying the total, not authorizing a booking. Is that your opening offer plus 25 dollars?"
            )
            await asyncio.sleep(4)
            _, d = await repository.read()
            assert not (d["calls"][cid].get("agreement") or {}).get("booking_consent")
            assert not any(
                b.get("write_intent_id") for b in d["bookings"].values() if b["call_id"] == cid
            )
            await send(
                "Please ask the exact booking permission question by itself, with the load ID and total."
            )
            await asyncio.sleep(3)
            await send("Yes please book it.")
            _, agreement = await wait_for(
                lambda d: (
                    (d["calls"][cid].get("agreement") or {})
                    if (d["calls"][cid].get("agreement") or {}).get("booking_consent")
                    else None
                ),
                "positive consent",
            )
            _, after = await repository.read()
            assert old_intents == {
                b.get("write_intent_id")
                for b in after["bookings"].values()
                if b.get("write_intent_id")
            }
            result = {
                "label": "HYBRID",
                "run_id": cid,
                "session_id": sid,
                "authority": "LIVE_FMCSA",
                "email": "LIVE_SMTP",
                "code_proof": "SIMULATED_QA_CODE",
                "load_reads": "LIVE_TMS",
                "consent": "LIVE_ACTIVE_NATIVE_TRANSCRIPT",
                "price_clarification_approved": False,
                "explicit_yes_approved": True,
                "proof": agreement["consent_proof"],
                "new_live_sends": 0,
                "limit": "Text session with synthetic identity proof, not a real carrier voice call.",
            }
            (ROOT / "docs/prototype-evidence/active-consent-check.json").write_text(
                json.dumps(result, indent=2) + "\n"
            )
            print(json.dumps(result), flush=True)
        finally:
            try:
                data = await history()
                path = ROOT / "secrets/active-consent-history.json"
                path.write_text(json.dumps(data, indent=2))
                path.chmod(0o600)
                await platform.post("/chat/sessions/" + sid + "/close", headers=headers)
            except Exception:
                pass
            if repository.pending:
                await asyncio.gather(*repository.pending, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
