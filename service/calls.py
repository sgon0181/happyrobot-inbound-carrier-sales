"""The call's row, and the verify flows that write it.

The model only asks; every decision uses the call's own stored state (rule 1). A call
is identified by the workflow's run_id, which the model cannot choose (D-16). State
changes share a write with their events (INV-9); refused carrier changes leave the row untouched.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from service.adapters.email import DeliveryLimited, EmailFailed, NoTrustedContact
from service.adapters.fmcsa import Fmcsa, FmcsaUnavailable
from service.adapters.twin import Data, Row, Twin
from service.call_state import code_state, complete_call, permits_action, store_code
from service.core import codes
from service.core.carrier_policy import assess, normalize_mc

Reply = dict[str, Any]


@dataclass(frozen=True)
class Unchanged:
    """A decision's reply when nothing happened, so the row is not written at all."""

    reply: Reply


FAILED = "negotiation_failed"  # terminal: no route may clear it
Decide = Callable[[Data, datetime], Reply | Unchanged]


class Mailer(Protocol):
    async def send(self, code: str, mc: str) -> None: ...


class CallRows:
    """Reads and writes call rows. Every write is one decision and its event."""

    def __init__(
        self,
        *,
        twin: Twin,
        cohort: str,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        native_workflow: Data | None = None,
    ) -> None:
        self.twin, self.cohort, self.now = twin, cohort, now
        self.native_workflow = dict(native_workflow) if native_workflow else None

    async def read(self, run_id: str) -> Data:
        """The call as stored, or a new call if it has no row yet. Nothing is written."""
        row = await self.twin.get("calls", run_id)
        return complete_call(
            row.data if row else None, self.cohort, self.now(), self.native_workflow
        )

    async def step(
        self,
        run_id: str,
        action: str,
        decide: Decide,
        detail: Data | None = None,
        *,
        previous: Row | None = None,
    ) -> Reply:
        edit = self._transition(action, decide, detail)
        if previous is not None:
            changed, result = edit(previous.data)
            if changed is not None and await self.twin.update(
                "calls", run_id, previous.version, changed
            ):
                return result
        return await self.twin.change("calls", run_id, edit)

    async def start_lookup(self, run_id: str, mc: str) -> tuple[Reply, Row | None]:
        """An initial call uses one INSERT. On collision, honor the persisted call state."""
        choose = _select(mc)
        data, reply = self._transition("verify_carrier", choose, None)(None)
        if data is not None and await self.twin.insert("calls", run_id, data):
            return reply, Row(1, data)
        return await self.step(run_id, "verify_carrier", choose), None

    def _transition(
        self, action: str, decide: Decide, detail: Data | None
    ) -> Callable[[Data | None], tuple[Data | None, Reply]]:
        now = self.now()

        def edit(current: Data | None) -> tuple[Data | None, Reply]:
            data = complete_call(current, self.cohort, now, self.native_workflow)
            if data.get("read_only") or not permits_action(data, action):
                return None, {"status": "call_closed"}
            ending = action in ("close", "call_ended")
            hint = {"_claim": data["accepting"]} if ending and data["accepting"] else {}
            reply = decide(data, now)
            if isinstance(reply, Unchanged):
                return None, reply.reply | hint
            if (current or {}).get("outcome") == FAILED:  # a failed negotiation stays failed
                data["outcome"] = FAILED
            data["last_activity"] = now.isoformat()
            event = {"at": now.isoformat(), "action": action, "mc": data["mc"]}
            event |= (detail or {}) | reply
            data["events"].append({"seq": len(data["events"]) + 1, **event})
            return data, reply | hint

        return edit


class Calls:
    def __init__(
        self,
        *,
        rows: CallRows,
        fmcsa: Fmcsa,
        mailer: Mailer,
        code_secret: bytes,
        trusted_contacts: bool = False,
    ) -> None:
        self.rows, self.fmcsa, self.mailer, self.code_secret = rows, fmcsa, mailer, code_secret
        self.delivery_route = "trusted_contact" if trusted_contacts else "demo_inbox"

    async def verify_carrier(self, run_id: str, mc_text: str) -> Reply:
        mc = normalize_mc(mc_text)
        if mc is None:
            return await self.rows.step(run_id, "verify_carrier", answer("invalid_mc"))
        selected, previous = await self.rows.start_lookup(run_id, mc)
        if selected["status"] != "checking":
            return selected
        lookup = selected["lookup"]
        try:
            authority = assess(await self.fmcsa.carriers(mc))
        except FmcsaUnavailable:
            unavailable = set_outcome("fmcsa_unavailable")
            return await self.rows.step(
                run_id, "verify_carrier", _latest(lookup, unavailable), previous=previous
            )

        def decide(data: Data, now: datetime) -> Reply:
            data["carrier_name"], data["eligible"] = authority.carrier_name, authority.eligible
            data["authority"] = {"reason": authority.reason, "checked_at": now.isoformat()}
            data["outcome"] = None if authority.eligible else "carrier_ineligible"
            if authority.eligible:
                return {"status": "eligible", "carrier_name": authority.carrier_name}
            if authority.reason == "not_found":
                return {"status": "not_found"}
            return {"status": "ineligible", "reason": authority.reason}

        return await self.rows.step(
            run_id, "verify_carrier", _latest(lookup, decide), previous=previous
        )

    async def send_code(self, run_id: str) -> Reply:
        code = codes.new_code()  # made before the write, which may be retried
        hashed = codes.code_hash(self.code_secret, run_id, code)

        def decide(data: Data, now: datetime) -> Reply:
            if not data["eligible"]:
                return {"status": "not_eligible"}
            state, result = codes.issue(code_state(data), hashed, now)
            store_code(data, state)
            if result is not codes.Issued.ISSUED:
                return {"status": result.value}
            data["otp_route"] = None
            return {"status": "code_issued", "mc": data["mc"], "send_number": state.sends}

        reply = await self.rows.step(run_id, "send_code", decide)
        if reply["status"] != "code_issued":
            return reply
        status, reason = "sent", None
        try:  # the send is already counted, so a failure is never silently retried
            await self.mailer.send(code, reply["mc"])
        except NoTrustedContact:
            status, reason = "locked", "no_trusted_contact"
        except DeliveryLimited:
            status, reason = "send_limit", "delivery_throttled"
        except EmailFailed:
            status, reason = "send_failed", "smtp_failed"
        delivery = {"mc": reply["mc"], "send_number": reply["send_number"], "delivery": status}
        if reason:
            delivery["reason"] = reason
        return await self.rows.step(
            run_id,
            "send_code",
            _delivery(hashed, reply["send_number"], status, self.delivery_route),
            delivery,
        )

    async def end(self, run_id: str, ended_by: str | None, seconds: float | None) -> Reply:
        """Record the call's end, from the workflow's request after the voice agent finishes.

        Every call gets a row this way, even one that ended before the agent called a tool,
        so a call is never counted, or missed, on the agent's word. A repeat changes nothing.
        """

        def decide(data: Data, now: datetime) -> Reply | Unchanged:
            if data["ended_at"] is not None:
                return Unchanged({"status": "ended"})
            data.update(ended_at=now.isoformat(), ended_by=ended_by, duration_seconds=seconds)
            return {"status": "ended", "ended_by": ended_by, "duration_seconds": seconds}

        return await self.rows.step(run_id, "call_ended", decide)

    async def verify_code(self, run_id: str, code_text: str) -> Reply:
        code = codes.normalize_code(code_text)
        if code is None:
            return await self.rows.step(run_id, "verify_code", answer("invalid_code"))
        hashed = codes.code_hash(self.code_secret, run_id, code)

        def decide(data: Data, now: datetime) -> Reply:
            if not data["eligible"]:
                return {"status": "not_eligible"}
            state, result = codes.check(code_state(data), hashed, now)
            store_code(data, state)  # consuming the code and verifying are one write
            if result is codes.Checked.VERIFIED:
                data["verified_at"] = data["verified_at"] or now.isoformat()
            if result is codes.Checked.LOCKED:
                data["outcome"] = "code_failed"
            if result is codes.Checked.WRONG:
                return {"status": result.value, "tries_left": codes.tries_left(state)}
            return {"status": result.value}

        return await self.rows.step(run_id, "verify_code", decide)


def is_verified(data: Data) -> bool:
    """FMCSA eligibility and a passed code, both for the MC on the call (INV-3)."""
    return bool(data["eligible"] and data["verified_at"])


def answer(status: str, reply: Reply | None = None) -> Decide:
    """A decision that changes nothing but the event."""
    return lambda data, now: dict(reply or {"status": status})


def set_outcome(outcome: str) -> Decide:
    def decide(data: Data, now: datetime) -> Reply:
        data["outcome"] = outcome
        return {"status": outcome}

    return decide


def _select(mc: str) -> Decide:
    """A different MC starts verification again, keeping the budgets (section 8). It is
    saved before the lookup, so a failed or slow lookup cannot leave an earlier MC verified.
    """

    def decide(data: Data, now: datetime) -> Reply | Unchanged:
        if data["mc"] != mc:
            if data["agreement"] is not None or data["accepting"] is not None:
                return Unchanged({"status": "carrier_locked"})
            store_code(data, codes.for_new_mc(code_state(data)))
            data.update(
                mc=mc,
                carrier_name=None,
                eligible=False,
                authority=None,
                verified_at=None,
                otp_route=None,
            )
            data.update(
                offers={},
                shipments={},
                lowest_asks={},
                last_counters={},
                counter_replies={},
                last_counter=None,
                outcome=None,
            )
        # Suspend freight access while rechecking even the same MC. Keep its valid OTP.
        data.update(eligible=False, authority=None)
        data["lookup"] += 1
        return {"status": "checking", "lookup": data["lookup"]}

    return decide


def _delivery(hashed: str, send_number: int, status: str, route: str) -> Decide:
    """A mail completion belongs to its issuance, even if a newer code has the same digits."""

    def decide(data: Data, now: datetime) -> Reply:
        otp = data["otp"]
        current = otp["hash"] == hashed and otp["sends"] == send_number
        if not current:
            return {"status": "superseded"}
        if status == "sent":
            data["otp_route"] = route
        elif status in ("locked", "send_limit"):
            store_code(data, codes.for_new_mc(code_state(data)))
        return {"status": status}

    return decide


def _latest(lookup: int, decide: Decide) -> Decide:
    """Apply a lookup's result only if no later lookup started, even for the same MC."""
    return lambda data, now: (
        decide(data, now) if data["lookup"] == lookup else {"status": "superseded"}
    )
