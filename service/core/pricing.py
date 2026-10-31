"""The versioned pricing policy (architecture 6.5).

Each load's numbers are derived from its posted rate and validated ceiling, using
a keyed seed: the same load gives the same numbers on every call, and knowing the
policy without the secret does not reveal the gap. A load that cannot be priced
safely returns None, which means pricing_review_required.
"""

from dataclasses import dataclass
import hashlib
import hmac
import json
from pathlib import Path

BPS = 10_000
DEFAULT_POLICY = Path(__file__).resolve().parents[1] / "policy" / "pricing-v1.json"


@dataclass(frozen=True)
class PricingPolicy:
    version: str
    rounding_step: int
    ceiling_gap_bps: tuple
    opening_discount_bps: int
    opening_spread_bps: tuple
    round_target_bps: tuple

    @classmethod
    def load(cls, path=DEFAULT_POLICY):
        data = json.loads(Path(path).read_text())
        return cls(
            version=data["version"],
            rounding_step=data["rounding_step"],
            ceiling_gap_bps=tuple(data["ceiling_gap_bps"]),
            opening_discount_bps=data["opening_discount_bps"],
            opening_spread_bps=tuple(data["opening_spread_bps"]),
            round_target_bps=tuple(data["round_target_bps"]),
        )


@dataclass(frozen=True)
class Terms:
    load_id: str
    policy_version: str
    opening: int
    targets: tuple
    cap: int


def _draw(secret, policy, load_id, purpose, band):
    message = f"{policy.version}|{load_id}|{purpose}".encode()
    digest = hmac.new(secret, message, hashlib.sha256).digest()
    low, high = band
    return low + int.from_bytes(digest, "big") % (high - low + 1)


def _less_bps(amount, bps):
    return amount * (BPS - bps) // BPS


def price_load(load_id, posted, ceiling, policy, secret):
    """Return the load's Terms, or None if it needs pricing review."""
    if not secret:
        raise ValueError("A pricing secret is required.")
    if not ceiling or ceiling <= 0:
        return None

    def round_down(amount):
        return amount // policy.rounding_step * policy.rounding_step

    gap = _draw(secret, policy, load_id, "ceiling_gap", policy.ceiling_gap_bps)
    cap = round_down(_less_bps(ceiling, gap))

    opening = round_down(_less_bps(posted, policy.opening_discount_bps)) if posted else 0
    if not 0 < opening < cap:
        spread = _draw(secret, policy, load_id, "opening_spread", policy.opening_spread_bps)
        opening = round_down(_less_bps(cap, spread))

    if not 0 < opening < cap < ceiling:
        return None

    targets = [
        round_down(opening + (cap - opening) * bps // BPS) for bps in policy.round_target_bps
    ]
    targets[-1] = cap
    if any(not opening <= target <= cap for target in targets) or targets != sorted(targets):
        return None
    return Terms(load_id, policy.version, opening, tuple(targets), cap)
