"""Service-owned call rules. The model supplies requests, never verification facts."""

import asyncio
import hashlib
import hmac
import json
import re
import secrets
import time
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from service.core.booking import BookingService, State, agent_view, BookingConflict
from service.core.loads import select_offers
from service.core.negotiation import respond, Action
from service.core.pricing import PricingPolicy, price_load
from service.core.ports import TmsUnavailable
from service.adapters.twin.bookings import TwinBookingStore, PROTECTED, decode
from service.core.campaign import permission


class Runtime:
    def __init__(
        self, repository, tms, authority, notifier, values, clock=time.time, confirmation=None
    ):
        self.repository, self.tms, self.authority, self.notifier = (
            repository,
            tms,
            authority,
            notifier,
        )
        self.values, self.clock = values, clock
        self.confirmation = confirmation
        self.policy = PricingPolicy.load()
        self.locks = {}
        self.booking_store = TwinBookingStore(
            repository, live=repository.label == "LIVE", clock=self.clock
        )
        self.bookings = BookingService(self.booking_store, tms)

    def digest(self, text):
        return hmac.new(
            self.values["OTP_HASH_SECRET"].encode(), text.encode(), hashlib.sha256
        ).hexdigest()

    def event(self, data, cid, action, status, **fields):
        data["call_events"][uuid.uuid4().hex] = {
            "call_id": cid,
            "action": action,
            "status": status,
            "at": self.clock(),
            **fields,
        }

    def new_call(self, cid):
        return {
            "id": cid,
            "cohort": "real" if self.repository.label == "LIVE" else "synthetic",
            "started_at": self.clock(),
            "last_activity": self.clock(),
            "mc": None,
            "eligible": False,
            "verified_until": 0,
            "sends": 0,
            "failed_codes": 0,
            "rounds": 0,
            "operations": {},
            "offers": {},
            "agreement": None,
            "outcome": None,
            "closed_at": None,
            "policy_version": self.policy.version,
        }

    async def operation(self, cid, action, args, fn):
        fingerprint = self.digest(
            action + "|" + json.dumps(args, sort_keys=True, separators=(",", ":"))
        )

        def change(data):
            call = data["calls"].setdefault(cid, self.new_call(cid))
            if call.get("booking_id") and action != "close":
                reserved = data["bookings"].get(call["booking_id"])
                return agent_view(decode(reserved)) if reserved else {"status": "in_progress"}
            previous = call["operations"].get(fingerprint)
            if previous and self.clock() - previous["finished_at"] <= 5:
                cached = previous["result"]
                agreement = call.get("agreement")
                stale_agreement = (
                    action == "negotiate"
                    and cached.get("status") == "agreed"
                    and (
                        not agreement
                        or any(agreement.get(k) != cached.get(k) for k in ("load_id", "rate"))
                    )
                )
                if not stale_agreement:
                    return cached
            result = fn(data, call)
            call["last_activity"] = self.clock()
            call["operations"][fingerprint] = {"finished_at": self.clock(), "result": result}
            self.event(data, cid, action, result.get("status", "ok"), fingerprint=fingerprint)
            return result

        return await self.repository.update_call(
            cid, lambda data, call: change(data), self.new_call(cid)
        )

    def gate(self, call):
        if call.get("closed_at"):
            return {"status": "call_closed"}
        if call.get("booking_id"):
            return {"status": "in_progress"}
        if not call.get("eligible"):
            return {"status": "carrier_ineligible"}
        if call["verified_until"] <= self.clock():
            return {"status": "otp_required"}

    async def verify_carrier(self, cid, mc):
        from service.adapters.fmcsa.client import FMCSAClient

        mc = FMCSAClient.normalize_mc(mc)
        _, data = await self.repository.read_call(cid)
        call = data["calls"].get(cid)
        if call and call.get("closed_at"):
            return {"status": "call_closed"}
        if call and call.get("booking_id"):
            reserved = data["bookings"].get(call["booking_id"])
            return agent_view(decode(reserved)) if reserved else {"status": "in_progress"}
        if call and call.get("mc") == mc and self.clock() - call.get("authority_at", 0) <= 5:
            return {
                "status": "ok" if call["eligible"] else call["outcome"],
                "carrier_name": call.get("carrier_name"),
            }
        try:
            authority = await self.authority(mc)
        except Exception:
            authority = {"eligible": False, "reason": "fmcsa_unavailable", "source": "unavailable"}

        def apply(data, call):
            reserved = data["bookings"].get(call.get("booking_id"))
            if call.get("booking_id"):
                return agent_view(decode(reserved)) if reserved else {"status": "in_progress"}
            if any(b["state"] != "FAILED" for b in data["bookings"].values()):
                return {"status": "in_progress"}
            if call.get("mc") != mc:
                call["operations"] = {}
            name = (authority.get("carrier") or {}).get("legalName")
            status = (
                "ok"
                if authority["eligible"]
                else (
                    "fmcsa_unavailable"
                    if authority["reason"] == "fmcsa_unavailable"
                    else "carrier_ineligible"
                )
            )
            call.update(
                mc=mc,
                eligible=bool(authority["eligible"]),
                verified_until=0,
                authority_at=self.clock(),
                carrier_name=name,
                offers={},
                agreement=None,
                challenge=None,
                outcome=None if status == "ok" else status,
            )
            data["carriers"][mc] = {"mc": mc, "authority": authority, "checked_at": self.clock()}
            return {"status": status, "carrier_name": name}

        return await self.operation(cid, "verify_carrier", {"mc": mc}, apply)

    async def reserve_code_budget(self, mc):
        for identity, limit in (("otp-rate:" + mc, 3), ("otp-rate:global", 10)):

            def reserve(row):
                times = [t for t in row.get("times", []) if t > self.clock() - 60]
                if len(times) >= limit:
                    return False
                row.update(kind="otp_throttle", times=times + [self.clock()])
                return True

            allowed = await self.repository.mutate("booking_claims", identity, reserve, initial={})
            if not allowed:
                return False
        return True

    async def send_code(self, cid):
        code = f"{secrets.randbelow(1000000):06d}"
        challenge = uuid.uuid4().hex

        def issue(data, call):
            if call.get("closed_at"):
                return {"status": "call_closed"}
            if not call["eligible"]:
                return {"status": "carrier_ineligible"}
            if call["failed_codes"] >= 3:
                return {"status": "code_failed"}
            if call["sends"] >= 2:
                return {"status": "send_limit"}
            if not self.values.get("DEMO_OTP_EMAIL"):
                return {"status": "no_trusted_contact"}
            call.update(challenge=challenge, verified_until=0, sends=call["sends"] + 1)
            return {"status": "submitting", "challenge_id": challenge, "mc": call["mc"]}

        result = await self.operation(cid, "send_code", {}, issue)
        if result.get("challenge_id") != challenge:
            if result["status"] == "submitting":
                return {"status": "delivery_pending", "channel": "email"}
            return result
        mc = result["mc"]
        allowed = await self.reserve_code_budget(mc)
        row = {
            "call_id": cid,
            "mc": mc,
            "purpose": "call-load-access",
            "destination_version": "configured-demo-inbox",
            "hash": self.digest(cid + "|" + mc + "|" + code),
            "expires_at": self.clock() + 300,
            "consumed_at": None,
            "delivery_status": "delivery_pending" if allowed else "send_throttled",
        }
        if not await self.repository.cas("otp_challenges", challenge, None, row):
            raise ValueError("Challenge already exists")
        receipt = {}
        if allowed:
            try:
                receipt = await self.notifier(code, cid)
                status = (
                    "sent"
                    if receipt.get("sent")
                    else ("delivery_pending" if receipt.get("submitted") else "delivery_unknown")
                )
            except Exception:
                status = "delivery_unknown"
        else:
            status = "send_throttled"

        def delivered(current):
            current.update(
                delivery_status=status,
                provider_message_id=receipt.get("message_id"),
                provider=receipt.get("source"),
            )

        await self.repository.mutate("otp_challenges", challenge, delivered)
        safe = {"status": status, "channel": "email", "destination": "configured demo inbox"}

        def finish(data, call):
            for op in call["operations"].values():
                if op["result"].get("challenge_id") == challenge:
                    op["result"] = safe
            self.event(data, cid, "code_delivery", status)
            return safe

        return await self.repository.update_call(cid, finish, self.new_call(cid))

    async def verify_code(self, cid, code):
        code = str(code)

        def prepare(data, call):
            if call.get("closed_at"):
                return {"status": "call_closed"}
            if not call["eligible"]:
                return {"status": "carrier_ineligible"}
            if call["failed_codes"] >= 3:
                return {"status": "code_failed"}
            challenge = data["otp_challenges"].get(call.get("challenge"))
            if (
                not challenge
                or challenge["expires_at"] <= self.clock()
                or challenge["consumed_at"]
                or "invalidated_at" in challenge
            ):
                return {"status": "code_expired_or_used"}
            if challenge["mc"] != call["mc"] or challenge["delivery_status"] not in {
                "sent",
                "delivery_pending",
            }:
                return {"status": "delivery_unknown"}
            if not re.fullmatch(r"[0-9]{6}", code) or not hmac.compare_digest(
                challenge["hash"], self.digest(cid + "|" + call["mc"] + "|" + code)
            ):
                call["failed_codes"] += 1
                if call["failed_codes"] >= 3:
                    call["outcome"] = "code_failed"
                return {"status": "code_failed" if call["failed_codes"] >= 3 else "wrong_code"}
            return {"status": "consume", "challenge_id": call["challenge"], "mc": call["mc"]}

        result = await self.operation(cid, "verify_code", {"code_hash": self.digest(code)}, prepare)
        if result.get("status") != "consume":
            return result
        challenge_id, mc = result["challenge_id"], result["mc"]

        def consume(row):
            if (
                row.get("consumed_at")
                or row["expires_at"] <= self.clock()
                or row.get("invalidated_at")
            ):
                return False
            if row["call_id"] != cid or row["mc"] != mc:
                return False
            row["consumed_at"] = self.clock()
            return True

        if not await self.repository.mutate("otp_challenges", challenge_id, consume):
            return {"status": "code_expired_or_used"}

        def promote(data, call):
            if (
                call.get("closed_at")
                or not call.get("eligible")
                or call.get("mc") != mc
                or call.get("challenge") != challenge_id
                or call["failed_codes"] >= 3
            ):
                return {"status": "code_expired_or_used"}
            call.update(verified_until=self.clock() + 1800, code_passed_at=self.clock())
            safe = {"status": "ok", "code_passed": True}
            for op in call["operations"].values():
                if (
                    op["result"].get("challenge_id") == challenge_id
                    and op["result"].get("status") == "consume"
                ):
                    op["result"] = safe
            return safe

        return await self.repository.update_call(cid, promote, self.new_call(cid))

    def terms(self, load):
        return price_load(
            load.load_id,
            load.loadboard_rate,
            load.max_rate,
            self.policy,
            self.values["PRICING_SECRET"].encode(),
        )

    def public_load(self, load, offer):
        data = asdict(load)
        for key in ("max_rate", "loadboard_rate", "evidence", "status"):
            data.pop(key, None)
        for key in ("pickup_datetime", "delivery_datetime"):
            if data[key]:
                data[key] = data[key].isoformat()
        data.update(
            offer=offer,
            origin_city=load.origin.city,
            origin_state=load.origin.state,
            destination_city=load.destination.city,
            destination_state=load.destination.state,
        )
        return data

    async def search(self, cid, criteria):
        _, data = await self.repository.read_call(cid)
        call = data["calls"].get(cid, self.new_call(cid))
        denied = self.gate(call)
        if denied:
            return denied
        criteria = {
            k: v.strip().upper() for k, v in criteria.items() if isinstance(v, str) and v.strip()
        }
        criteria["equipment"] = {
            "VAN": "DRY_VAN",
            "DRY VAN": "DRY_VAN",
            "REFRIGERATED": "REEFER",
        }.get(criteria.get("equipment"), criteria.get("equipment", "DRY_VAN"))
        try:
            summaries = await self.tms.query(**criteria, limit=100)
            blocked = await self.booking_store.blocked_load_ids([row.load_id for row in summaries])
            selected = select_offers(
                summaries,
                datetime.now(timezone.utc),
                blocked | PROTECTED,
                **{k: criteria.get(k) for k in ("equipment", "origin_state", "dest_state")},
            )
            loads = await asyncio.gather(
                *(self.tms.get(row.load_id) for row in selected), return_exceptions=True
            )
        except TmsUnavailable:
            return await self.set_outcome(cid, "tms_unavailable")
        blocked = await self.booking_store.blocked_load_ids([row.load_id for row in selected])
        priced = []
        for load in loads:
            if isinstance(load, Exception) or load is None:
                continue
            if not select_offers([load], datetime.now(timezone.utc), blocked | PROTECTED):
                continue
            terms = self.terms(load)
            if terms:
                priced.append((load, terms))

        def save(data, call):
            denied = self.gate(call)
            if denied:
                return denied
            current_blocked = {
                b["load_id"] for b in data["bookings"].values() if b["state"] != "FAILED"
            }
            offers = [
                (load, terms) for load, terms in priced if load.load_id not in current_blocked
            ]
            if not offers:
                status = (
                    "pricing_review_required"
                    if any(not isinstance(x, Exception) and x for x in loads)
                    else "no_match"
                )
                call["outcome"] = status
                data["unmet_demand"][uuid.uuid4().hex] = {
                    "call_id": cid,
                    "mc": call["mc"],
                    "at": self.clock(),
                    **criteria,
                }
                return {"status": status, "loads": []}
            for load, terms in offers:
                call["offers"][load.load_id] = {"current_offer": terms.opening}
            call.setdefault("first_offer_at", self.clock())
            return {
                "status": "ok",
                "loads": [self.public_load(load, terms.opening) for load, terms in offers],
            }

        return await self.operation(cid, "search", criteria, save)

    async def negotiate(self, cid, load_id, rate):
        _, data = await self.repository.read_call(cid)
        call = data["calls"].get(cid, self.new_call(cid))
        denied = self.gate(call)
        if denied:
            return denied
        if load_id not in call["offers"]:
            return {"status": "search_required"}
        try:
            load = await self.tms.get(load_id)
        except TmsUnavailable:
            return await self.set_outcome(cid, "tms_unavailable")
        if load is None or not select_offers([load], datetime.now(timezone.utc), PROTECTED):
            return {"status": "load_gone"}
        if load_id in await self.booking_store.blocked_load_ids([load_id]):
            return {"status": "load_gone"}
        terms = self.terms(load)
        if terms is None:
            return await self.set_outcome(cid, "pricing_review_required")

        def act(data, call):
            denied = self.gate(call)
            if denied:
                return denied
            if call["outcome"] == "negotiation_failed":
                return {"status": "negotiation_failed"}
            if any(
                b["load_id"] == load_id and b["state"] != "FAILED"
                for b in data["bookings"].values()
            ):
                return {"status": "load_gone"}
            step = respond(
                terms,
                call["rounds"],
                min(call["offers"][load_id]["current_offer"], terms.cap),
                rate,
            )
            if step.action is not Action.ACCEPT:
                call["agreement"] = None
            if step.rounds_used > call["rounds"]:
                call["rounds"] = step.rounds_used
                data["negotiation_rounds"][uuid.uuid4().hex] = {
                    "call_id": cid,
                    "load_id": load_id,
                    "round": step.rounds_used,
                    "ask": rate,
                    "response": step.rate,
                }
            if step.action is Action.ACCEPT:
                call["agreement"] = {
                    "load_id": load_id,
                    "rate": step.rate,
                    "version": uuid.uuid4().hex,
                }
                return {"status": "agreed", "load_id": load_id, "rate": step.rate}
            if step.action is Action.FAILED:
                call["outcome"] = "negotiation_failed"
                return {"status": "negotiation_failed", "handoff_allowed": False}
            if step.rate:
                call["offers"][load_id]["current_offer"] = step.rate
            return {
                "status": "ask_again" if step.action is Action.ASK_AGAIN else "counter",
                "offer": step.rate,
                "round": step.rounds_used,
                "final": step.action is Action.FINAL_OFFER,
            }

        return await self.operation(cid, "negotiate", {"load_id": load_id, "rate": rate}, act)

    async def book(self, cid, deadline):
        _, data = await self.repository.read_call(cid)
        call = data["calls"].get(cid, self.new_call(cid))
        existing = [
            b
            for b in data["bookings"].values()
            if b["call_id"] == cid and (b["state"] != "FAILED" or b.get("write_intent_id"))
        ]
        if existing:
            return agent_view(decode(existing[0]))
        denied = self.gate(call)
        if denied:
            return denied
        agreement = call["agreement"]
        if not agreement:
            return {"status": "agreement_required"}
        if call.get("outcome") == "negotiation_failed":
            return {"status": "negotiation_failed"}
        # Price agreement is not booking consent. Live calls need a fresh, platform-owned
        # affirmative answer to a completed question containing the exact total.
        if self.repository.label == "LIVE" and self.tms.booking_enabled:
            try:
                if self.confirmation is None:
                    raise ValueError("No trusted dialogue source")
                evidence = await self.confirmation(
                    cid,
                    agreement["load_id"],
                    agreement["rate"],
                    agreement.get("confirmation_anchor"),
                )
            except Exception:
                return {"status": "confirmation_unavailable"}

            def record(data):
                if data["calls"][cid].get("booking_id"):
                    return False
                current = data["calls"][cid]["agreement"]
                if not current or current["version"] != agreement["version"]:
                    return False
                if not evidence.get("approved"):
                    current["confirmation_anchor"] = evidence.get("anchor")
                current["booking_consent"] = bool(evidence.get("approved"))
                if evidence.get("approved"):
                    current["consent_proof"] = {
                        k: evidence.get(k) for k in ("question_id", "answer_id", "session_id")
                    }
                    current["consent_proof"]["agreement_version"] = agreement["version"]
                self.event(
                    data,
                    cid,
                    "booking_consent",
                    "approved" if evidence.get("approved") else "required",
                )
                return True

            if not await self.repository.update_call(
                cid, lambda state, call: record(state), self.new_call(cid)
            ):
                try:
                    known = await self.booking_store.for_call(cid)
                    if known:
                        return agent_view(decode(known))
                except BookingConflict:
                    return {"status": "in_progress"}
                return {"status": "agreement_required"}
            if not evidence.get("approved"):
                return {
                    "status": "confirmation_required",
                    "load_id": agreement["load_id"],
                    "agreed_rate": agreement["rate"],
                    "confirmation_prompt": (
                        f"May I book load {agreement['load_id']} " f"at ${agreement['rate']} total?"
                    ),
                }
            if call.get("cohort") != "real":
                return {"status": "consent_verified", "booking_submitted": False}
            if permission(data, cid, agreement["load_id"]) is None:
                return {"status": "live_campaign_complete"}
        try:
            booking = await self.bookings.request(
                call_id=cid,
                operation_id=agreement["version"],
                load_id=agreement["load_id"],
                mc=call["mc"],
                rate=agreement["rate"],
                agreement_version=agreement["version"],
                deadline=deadline,
            )
        except BookingConflict:
            return {"status": "booking_failed"}
        outcome = "booking_failed" if booking.state is State.FAILED else "agreed_pending_rep"
        try:
            await self.set_outcome(cid, outcome)
        except Exception:
            pass  # A known receipt is not invalidated by call-summary storage.
        return agent_view(booking)

    async def set_outcome(self, cid, status):
        def save(data):
            data["calls"].setdefault(cid, self.new_call(cid))["outcome"] = status
            self.event(data, cid, "outcome", status)
            return {"status": status}

        return await self.repository.update_call(
            cid, lambda state, call: save(state), self.new_call(cid)
        )

    async def close(self, cid):
        def close(data, call):
            bookings = [b for b in data["bookings"].values() if b["call_id"] == cid]
            if bookings and bookings[-1]["state"] in {"ACK_PENDING", "UNKNOWN", "CONFIRMED"}:
                call.update(outcome="agreed_pending_rep", handoff_mocked=True)
            call.update(
                closed_at=self.clock(),
                verified_until=0,
                outcome=call.get("outcome") or "ended_without_booking",
            )
            return {"status": "closed", "outcome": call["outcome"]}

        return await self.operation(cid, "close", {}, close)

    async def snapshot(self):
        _, data = await self.repository.read()
        calls = list(data["calls"].values())
        bookings = list(data["bookings"].values())
        real = [c for c in calls if c["cohort"] == "real"]
        rb = [b for b in bookings if b.get("cohort") == "real"]
        verified = sum(bool(c.get("code_passed_at")) for c in real)
        handoffs = sum(
            b["state"] in {"ACK_PENDING", "CONFIRMED"}
            and bool(b.get("reference"))
            and data["calls"][b["call_id"]].get("handoff_mocked", False)
            and bool((data["calls"][b["call_id"]].get("agreement") or {}).get("booking_consent"))
            and b.get("reason") != "caller_confirmation_review"
            for b in rb
        )
        queue = []
        for b in bookings:
            queue.append(
                {
                    k: b.get(k)
                    for k in [
                        "id",
                        "call_id",
                        "load_id",
                        "mc",
                        "rate",
                        "state",
                        "reference",
                        "tms_status",
                        "rep_decision",
                        "rep",
                        "review_required",
                        "reason",
                        "cohort",
                        "created_at",
                    ]
                }
            )
        return {
            "status": "ok",
            "queue": queue,
            "calls": [
                {
                    **{
                        k: c.get(k)
                        for k in [
                            "id",
                            "mc",
                            "cohort",
                            "outcome",
                            "rounds",
                            "started_at",
                            "closed_at",
                            "code_passed_at",
                            "carrier_name",
                        ]
                    },
                    "transcript": data["call_transcripts"].get(c["id"]),
                }
                for c in calls
            ],
            "kpis": {
                "real_calls": len(real),
                "code_passed_calls": verified,
                "acknowledged_handoffs": handoffs,
                "northstar": handoffs / verified if verified else 0,
                "tms_confirmed": sum(b["state"] == "CONFIRMED" for b in rb),
                "rep_confirmed": sum(b["rep_decision"] == "confirmed" for b in rb),
                "unknown": sum(b["state"] == "UNKNOWN" for b in rb),
                "synthetic_calls": len(calls) - len(real),
                "unmet_demand": len(data["unmet_demand"]),
            },
        }
