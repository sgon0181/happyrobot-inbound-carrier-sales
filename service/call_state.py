"""Persisted OTP and call state. Keep private credentials out of service replies."""

import copy
from datetime import datetime

from service.adapters.twin import Data
from service.core import codes


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
        "otp": code_fields(codes.CodeState()),
        "verified_at": None,
        "lookup": 0,  # counts MC lookups, so only the latest one's result is applied
        "search": None,
        "offers": {},  # load ID to the last offer we said
        "rounds": 0,
        "last_counter": None,
        "accepting": None,  # an acceptance claimed before its booking row is written
        "agreement": None,
        "policy_version": None,
        "outcome": None,
        "summary": None,
        "ended_at": None,  # from the workflow, after the voice agent finishes
        "ended_by": None,
        "duration_seconds": None,
        "events": [],
    }


def code_state(data: Data) -> codes.CodeState:
    otp = data["otp"]
    return codes.CodeState(
        hash=otp["hash"],
        expires_at=_time(otp["expires_at"]),
        sends=otp["sends"],
        failed=otp["failed"],
        consumed_at=_time(otp["consumed_at"]),
    )


def store_code(data: Data, state: codes.CodeState) -> None:
    data["otp"] = code_fields(state)


def code_fields(state: codes.CodeState) -> Data:
    return {
        "hash": state.hash,
        "expires_at": state.expires_at and state.expires_at.isoformat(),
        "sends": state.sends,
        "failed": state.failed,
        "consumed_at": state.consumed_at and state.consumed_at.isoformat(),
    }


def _time(text: str | None) -> datetime | None:
    return datetime.fromisoformat(text) if text else None


def permits_action(data: Data, action: str) -> bool:
    """Terminal calls accept only terminal retries and settlement of an existing claim."""
    if not (data["closed_at"] or data.get("ended_at")):
        return True
    if action in ("close", "call_ended"):
        return True
    return action in ("negotiate", "claim_recovery") and bool(data["accepting"])


def complete_call(
    current: Data | None, cohort: str, now: datetime, native_workflow: Data | None = None
) -> Data:
    """New calls receive trusted integration provenance. Existing rows never acquire it later."""
    data = new_call(cohort, now) | copy.deepcopy(current or {})
    if current is None and native_workflow:
        data["native_workflow"] = dict(native_workflow)
    return data
