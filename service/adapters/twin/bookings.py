"""One booking row plus durable call and load claims, without multi-table transactions."""

from dataclasses import asdict, fields, replace
import time

from service.core.booking import (
    Booking,
    State,
    RepDecision,
    ACTIVE,
    BookingConflict,
    OperationConflict,
)

from service.core.inventory import BLOCKED_LOADS


def encode(booking):
    row = asdict(booking)
    row["state"] = booking.state.value
    row["rep_decision"] = booking.rep_decision.value
    return row


def decode(row):
    data = {f.name: row[f.name] for f in fields(Booking) if f.name in row}
    data["state"] = State(data["state"])
    data["rep_decision"] = RepDecision(data["rep_decision"])
    return Booking(**data)


class TwinBookingStore:
    def __init__(self, repository, live=False, clock=time.time):
        self.repository, self.live, self.clock = repository, live, clock

    async def for_call(self, cid, bookings=None):
        _, claim = await self.repository.get("booking_claims", "call:" + cid)
        if claim and claim.get("active"):
            _, row = await self.repository.get("bookings", claim["booking_id"])
            if row is None:
                raise BookingConflict("An incomplete reservation requires review")
            return row
        rows = (
            bookings
            if bookings is not None
            else await self.repository.rows("bookings", call_id=cid)
        )
        return next(
            (r for _, _, r in rows if r["state"] != "FAILED" or r.get("write_intent_id")), None
        )

    async def claim(self, key, booking):
        row = {
            "booking_id": booking.id,
            "call_id": booking.call_id,
            "load_id": booking.load_id,
            "active": True,
            "write_intent_id": None,
        }
        return await self.repository.acquire_claim(key, row)

    async def create(self, booking, operation_id, fingerprint):
        rows = await self.repository.rows("bookings", call_id=booking.call_id)
        for _, _, row in rows:
            if row.get("operation_id") == operation_id:
                if row.get("fingerprint") != fingerprint:
                    raise OperationConflict("Changed booking operation")
                return decode(row), False
        existing = await self.for_call(booking.call_id, rows)
        if existing:
            if (
                existing.get("operation_id") == operation_id
                and existing.get("fingerprint") != fingerprint
            ):
                raise OperationConflict("Changed booking operation")
            return decode(existing), False
        if booking.load_id in BLOCKED_LOADS:
            raise BookingConflict("Load is excluded by inventory policy")
        # A past intent remains blocking even if its state later becomes FAILED.
        if booking.load_id in await self.blocked_load_ids([booking.load_id]):
            raise BookingConflict("Load already claimed")
        if not await self.claim("call:" + booking.call_id, booking):
            known = await self.for_call(booking.call_id)
            if known:
                return decode(known), False
            raise BookingConflict("Call already claimed")
        if not await self.claim("load:" + booking.load_id, booking):
            failed = replace(booking, state=State.FAILED, reason="load_claim_conflict")
            await self.repository.cas(
                "bookings",
                booking.id,
                None,
                {
                    **encode(failed),
                    "operation_id": operation_id,
                    "fingerprint": fingerprint,
                    "cohort": "synthetic" if not self.live else "real",
                    "created_at": time.time(),
                },
            )
            await self.release(failed)
            raise BookingConflict("Load already claimed")
        call = None
        cohort = "real" if self.live else "synthetic"
        if not self.live:
            _, call = await self.repository.get("calls", booking.call_id)
        if self.live or call is not None:

            def freeze(current):
                agreement = current.get("agreement")
                if agreement and agreement.get("version") != booking.agreement_version:
                    raise BookingConflict("Agreement changed before reservation")
                if self.live and (
                    not agreement
                    or not agreement.get("booking_consent")
                    or agreement.get("load_id") != booking.load_id
                    or agreement.get("rate") != booking.rate
                    or current.get("mc") != booking.mc
                    or current.get("cohort") != "real"
                    or not current.get("eligible")
                    or current.get("verified_until", 0) <= self.clock()
                    or current.get("closed_at")
                ):
                    raise BookingConflict("Fresh verified agreement and consent required")
                if current.get("booking_id") not in (None, booking.id):
                    raise BookingConflict("Call already reserved")
                current["booking_id"] = booking.id
                return current.get("cohort", cohort)

            cohort = await self.repository.mutate("calls", booking.call_id, freeze)
        row = {
            **encode(booking),
            "operation_id": operation_id,
            "fingerprint": fingerprint,
            "cohort": cohort,
            "created_at": time.time(),
        }
        if not await self.repository.cas("bookings", booking.id, None, row):
            raise BookingConflict("Booking identity already exists")
        return booking, True

    async def release(self, booking):
        if booking.state is not State.FAILED or booking.write_intent_id:
            return
        _, call = await self.repository.get("calls", booking.call_id)
        if call:

            def unfreeze(current):
                if current.get("booking_id") == booking.id:
                    current.pop("booking_id", None)

            await self.repository.mutate("calls", booking.call_id, unfreeze)
        # Keep the old call claim until its freeze and load claim are released.
        for key in ("load:" + booking.load_id, "call:" + booking.call_id):

            def clear(claim):
                if claim.get("booking_id") == booking.id and not claim.get("write_intent_id"):
                    claim["active"] = False

            _, claim = await self.repository.get("booking_claims", key)
            if claim:
                await self.repository.mutate("booking_claims", key, clear)

    async def update(self, booking_id, expected, **changes):
        if self.live and changes.get("state") is State.SUBMITTING:
            booking = await self.get(booking_id)
            _, call = await self.repository.get("calls", booking.call_id)
            agreement = (call or {}).get("agreement") or {}
            if (
                not call
                or call.get("cohort") != "real"
                or call.get("booking_id") != booking.id
                or not call.get("eligible")
                or call.get("verified_until", 0) <= self.clock()
                or call.get("closed_at")
                or not agreement.get("booking_consent")
                or agreement.get("version") != booking.agreement_version
            ):
                raise BookingConflict("Current verified call and consent required before intent")

        def change(row):
            booking = decode(row)
            if booking.state not in expected:
                return None
            if "rep_decision" in changes and booking.rep_decision not in {
                RepDecision.AWAITING,
                changes["rep_decision"],
            }:
                raise ValueError("The rep has already decided.")
            if (
                changes.get("rep_decision") is RepDecision.CONFIRMED
                and booking.reason == "caller_confirmation_review"
            ):
                raise ValueError("Caller consent requires review.")

            updated = replace(booking, **changes)
            row.update(encode(updated), updated_at=time.time())
            return updated

        updated = await self.repository.mutate("bookings", booking_id, change)
        if updated and updated.state is State.FAILED:
            await self.release(updated)
        return updated

    async def get(self, booking_id):
        _, row = await self.repository.get("bookings", booking_id)
        if row is None:
            raise KeyError(booking_id)
        return decode(row)

    async def in_states(self, states):
        rows = await self.repository.rows("bookings")
        return [decode(row) for _, _, row in rows if State(row["state"]) in states]

    async def blocked_load_ids(self, load_ids=None):
        ids = ["load:" + key for key in load_ids] if load_ids is not None else None
        claims = await self.repository.rows("booking_claims", ids=ids)
        blocked = {
            r["load_id"]
            for _, _, r in claims
            if r.get("load_id") and (r.get("active") or r.get("write_intent_id"))
        }
        # Memory fixtures may predate migration. Live rows always use durable claims.
        if hasattr(self.repository, "data"):
            rows = await self.repository.rows("bookings")
            blocked.update(
                r["load_id"]
                for _, _, r in rows
                if r["state"] != "FAILED" or r.get("write_intent_id")
            )
        return frozenset(blocked)
