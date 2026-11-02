"""Who may be offered loads: the FMCSA authority rule (architecture section 8).

A carrier is eligible only on positive evidence: active registration, allowed to
operate, active common or contract authority, and an out-of-service date that is
present and empty. Anything missing or unknown fails closed. Inactive carriers still
show allowedToOperate Y, so that field alone proves nothing (docs/test-carriers.md).
"""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

ELIGIBLE = "active_carrier_authority_verified"


@dataclass(frozen=True)
class Authority:
    eligible: bool
    reason: str
    carrier_name: str | None = None


def normalize_mc(text: str) -> str | None:
    """'MC-138328', 'mc 138 328' and '138328' all become '138328'. Anything else is None."""
    digits = re.sub(r"[\s-]", "", text).upper().removeprefix("MC")
    if not re.fullmatch(r"[0-9]{1,8}", digits) or int(digits) == 0:
        return None
    return str(int(digits))


def assess(carriers: Sequence[Mapping[str, object]]) -> Authority:
    """Decide from the FMCSA records returned for one MC."""
    if not carriers:
        return Authority(False, "not_found")
    if len(carriers) > 1:
        return Authority(False, "ambiguous_carrier_match")
    carrier = carriers[0]
    name = _flag(carrier, "legalName", upper=False) or _flag(carrier, "dbaName", upper=False)
    refusal = _refusal(carrier)
    return Authority(refusal is None, refusal or ELIGIBLE, name)


def _refusal(carrier: Mapping[str, object]) -> str | None:
    authorities = (
        _flag(carrier, "commonAuthorityStatus"),
        _flag(carrier, "contractAuthorityStatus"),
    )
    if _flag(carrier, "statusCode") != "A":
        return "registration_not_active"
    if _flag(carrier, "allowedToOperate") != "Y":
        return "not_allowed_to_operate"
    if "A" not in authorities:
        return "no_active_authority"
    if _out_of_service_or_unknown(carrier):
        return "out_of_service_or_unknown"
    return None


def _out_of_service_or_unknown(carrier: Mapping[str, object]) -> bool:
    """oosDate must be present and empty. Any other out-of-service field must also say no."""
    if "oosDate" not in carrier or carrier["oosDate"] is not None:
        return True
    if "outOfService" in carrier and _flag(carrier, "outOfService") != "N":
        return True
    return carrier.get("outOfServiceDate") is not None


def _flag(carrier: Mapping[str, object], key: str, *, upper: bool = True) -> str | None:
    value = carrier.get(key)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip().upper() if upper else value.strip()
