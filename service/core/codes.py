"""The one-time code rules (architecture section 8, INV-5).

Only a keyed hash of the code is kept, bound to the call, so a code cannot be read
back from storage or used on another call. A code lasts 5 minutes. A call gets at most
2 sends and 3 wrong tries, and those budgets survive both a resend and an MC change.
"""

import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum

DIGITS = 6
LIFETIME = timedelta(minutes=5)
MAX_SENDS = 2
MAX_FAILURES = 3


@dataclass(frozen=True)
class CodeState:
    hash: str | None = None
    expires_at: datetime | None = None
    sends: int = 0
    failed: int = 0
    consumed_at: datetime | None = None


class Issued(Enum):
    ISSUED = "issued"
    SEND_LIMIT = "send_limit"
    LOCKED = "locked"
    ALREADY_VERIFIED = "already_verified"


class Checked(Enum):
    VERIFIED = "verified"
    WRONG = "wrong_code"
    EXPIRED = "expired"
    NO_CODE = "no_code"
    LOCKED = "locked"


def new_code() -> str:
    return f"{secrets.randbelow(10**DIGITS):0{DIGITS}d}"


def code_hash(secret: bytes, run_id: str, code: str) -> str:
    return hmac.new(secret, f"{run_id}:{code}".encode(), hashlib.sha256).hexdigest()


def normalize_code(text: str) -> str | None:
    """'123 456' and '123-456' become '123456'. Anything but six digits is None."""
    digits = re.sub(r"[\s-]", "", text)
    return digits if re.fullmatch(rf"[0-9]{{{DIGITS}}}", digits) else None


def issue(state: CodeState, new_hash: str, now: datetime) -> tuple[CodeState, Issued]:
    """Replace any earlier code with a new one, if the call's budgets allow it."""
    if state.consumed_at is not None:
        return state, Issued.ALREADY_VERIFIED
    if state.failed >= MAX_FAILURES:
        return state, Issued.LOCKED
    if state.sends >= MAX_SENDS:
        return state, Issued.SEND_LIMIT
    issued = replace(state, hash=new_hash, expires_at=now + LIFETIME, sends=state.sends + 1)
    return issued, Issued.ISSUED


def check(state: CodeState, supplied_hash: str, now: datetime) -> tuple[CodeState, Checked]:
    """Compare in constant time. Consuming the code is part of the same new state."""
    if state.consumed_at is not None:
        return state, Checked.VERIFIED  # a repeat of a check that already passed (D-26)
    if state.failed >= MAX_FAILURES:
        return state, Checked.LOCKED
    if state.hash is None or state.expires_at is None:
        return state, Checked.NO_CODE
    if now >= state.expires_at:
        return state, Checked.EXPIRED
    if hmac.compare_digest(supplied_hash, state.hash):
        return replace(state, consumed_at=now), Checked.VERIFIED
    failed = replace(state, failed=state.failed + 1)
    return failed, Checked.LOCKED if failed.failed >= MAX_FAILURES else Checked.WRONG


def tries_left(state: CodeState) -> int:
    return max(0, MAX_FAILURES - state.failed)


def for_new_mc(state: CodeState) -> CodeState:
    """A different MC needs a fresh code, but keeps the call's send and failure budgets."""
    return replace(state, hash=None, expires_at=None, consumed_at=None)
