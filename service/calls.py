"""The voice flows. Each request reads the call's row, applies the core rules and writes back.

The model only asks; every decision uses the call's own stored state (rule 1). A call
is identified by the workflow's run_id, which the model cannot choose (D-16). Every
request leaves an event on the row in the same write as its change (INV-9).
"""

import copy
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Protocol

from service.adapters.email import EmailFailed
from service.adapters.fmcsa import Fmcsa, FmcsaUnavailable
from service.adapters.twin import Data, Twin
from service.core import codes
from service.core.carrier_policy import assess, normalize_mc

Reply = dict[str, Any]
Decide = Callable[[Data, datetime], Reply]


class Mailer(Protocol):
    async def send(self, code: str) -> None: ...


class Calls:
    def __init__(
        self,
        *,
        twin: Twin,
        fmcsa: Fmcsa,
        mailer: Mailer,
        code_secret: bytes,
        cohort: str,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.twin, self.fmcsa, self.mailer = twin, fmcsa, mailer
        self.code_secret, self.cohort, self.now = code_secret, cohort, now

    async def verify_carrier(self, run_id: str, mc_text: str) -> Reply:
        mc = normalize_mc(mc_text)
        if mc is None:
            return await self._step(run_id, "verify_carrier", _answer("invalid_mc"))
        await self._step(run_id, "verify_carrier", _select(mc))  # saved before FMCSA answers
        try:
            authority = assess(await self.fmcsa.carriers(mc))
        except FmcsaUnavailable:
            unavailable = _outcome("fmcsa_unavailable")
            return await self._step(run_id, "verify_carrier", _for_mc(mc, unavailable))

        def decide(data: Data, now: datetime) -> Reply:
            data["carrier_name"], data["eligible"] = authority.carrier_name, authority.eligible
            data["authority"] = {"reason": authority.reason, "checked_at": now.isoformat()}
            data["outcome"] = None if authority.eligible else "carrier_ineligible"
            if authority.eligible:
                return {"status": "eligible", "carrier_name": authority.carrier_name}
            if authority.reason == "not_found":
                return {"status": "not_found"}
            return {"status": "ineligible", "reason": authority.reason}

        return await self._step(run_id, "verify_carrier", _for_mc(mc, decide))

    async def send_code(self, run_id: str) -> Reply:
        code = codes.new_code()  # made before the write, which may be retried
        hashed = codes.code_hash(self.code_secret, run_id, code)

        def decide(data: Data, now: datetime) -> Reply:
            if not data["eligible"]:
                return {"status": "not_eligible"}
            state, result = codes.issue(_code_state(data), hashed, now)
            _store_code(data, state)
            return {"status": "code_issued" if result is codes.Issued.ISSUED else result.value}

        reply = await self._step(run_id, "send_code", decide)
        if reply["status"] != "code_issued":
            return reply
        try:  # the send is already counted, so a failure is never silently retried
            await self.mailer.send(code)
        except EmailFailed:
            return await self._step(run_id, "send_code", _answer("send_failed"))
        return {"status": "sent"}

    async def verify_code(self, run_id: str, code_text: str) -> Reply:
        code = codes.normalize_code(code_text)
        if code is None:
            return await self._step(run_id, "verify_code", _answer("invalid_code"))
        hashed = codes.code_hash(self.code_secret, run_id, code)

        def decide(data: Data, now: datetime) -> Reply:
            if not data["eligible"]:
                return {"status": "not_eligible"}
            state, result = codes.check(_code_state(data), hashed, now)
            _store_code(data, state)  # consuming the code and verifying are one write
            if result is codes.Checked.VERIFIED:
                data["verified_at"] = data["verified_at"] or now.isoformat()
            if result is codes.Checked.LOCKED:
                data["outcome"] = "code_failed"
            if result is codes.Checked.WRONG:
                return {"status": result.value, "tries_left": codes.tries_left(state)}
            return {"status": result.value}

        return await self._step(run_id, "verify_code", decide)

    async def _step(self, run_id: str, action: str, decide: Decide) -> Reply:
        """Apply one decision and its event to the call's row, in one version-checked write.

        The event keeps the call's MC after the step and the reply the agent was given,
        which never holds a code.
        """
        now = self.now()

        def edit(current: Data | None) -> tuple[Data, Reply]:
            data = copy.deepcopy(current) if current else new_call(self.cohort, now)
            reply = decide(data, now)
            data["last_activity"] = now.isoformat()
            event = {"at": now.isoformat(), "action": action, "mc": data["mc"], **reply}
            data["events"].append({"seq": len(data["events"]) + 1, **event})
            return data, reply

        return await self.twin.change("calls", run_id, edit)


def new_call(cohort: str, now: datetime) -> Data:
    """A call's row on its first request (architecture section 7)."""
    return {
        "cohort": cohort,
        "started_at": now.isoformat(),
        "last_activity": now.isoformat(),
        "closed_at": None,
        "mc": None,
        "carrier_name": None,
        "eligible": False,
        "authority": None,
        "otp": _code_fields(codes.CodeState()),
        "verified_at": None,
        "outcome": None,
        "events": [],
    }


def is_verified(data: Data) -> bool:
    """FMCSA eligibility and a passed code, both for the MC on the call (INV-3)."""
    return bool(data["eligible"] and data["verified_at"])


def _answer(status: str) -> Decide:
    return lambda data, now: {"status": status}


def _select(mc: str) -> Decide:
    """A different MC starts verification again, keeping the budgets (section 8). It is
    saved before the lookup, so a failed or slow lookup cannot leave an earlier MC verified.
    """

    def decide(data: Data, now: datetime) -> Reply:
        if data["mc"] != mc:
            _store_code(data, codes.for_new_mc(_code_state(data)))
            data.update(mc=mc, carrier_name=None, eligible=False, authority=None, verified_at=None)
        return {"status": "checking"}

    return decide


def _for_mc(mc: str, decide: Decide) -> Decide:
    """Apply a lookup's result only if the caller has not given another MC meanwhile."""
    return lambda data, now: decide(data, now) if data["mc"] == mc else {"status": "superseded"}


def _outcome(outcome: str) -> Decide:
    def decide(data: Data, now: datetime) -> Reply:
        data["outcome"] = outcome
        return {"status": outcome}

    return decide


def _code_state(data: Data) -> codes.CodeState:
    otp = data["otp"]
    return codes.CodeState(
        hash=otp["hash"],
        expires_at=_time(otp["expires_at"]),
        sends=otp["sends"],
        failed=otp["failed"],
        consumed_at=_time(otp["consumed_at"]),
    )


def _store_code(data: Data, state: codes.CodeState) -> None:
    data["otp"] = _code_fields(state)


def _code_fields(state: codes.CodeState) -> Data:
    return {
        "hash": state.hash,
        "expires_at": state.expires_at and state.expires_at.isoformat(),
        "sends": state.sends,
        "failed": state.failed,
        "consumed_at": state.consumed_at and state.consumed_at.isoformat(),
    }


def _time(text: str | None) -> datetime | None:
    return datetime.fromisoformat(text) if text else None
