"""The versioned pricing policy (D-4, architecture section 9).

Each load gets three kinds of number: a working cap below the ceiling, an
opening offer and one target per round. The gap below the ceiling and the
fallback spread are drawn per load with an HMAC under a server secret, so a
load gets the same numbers on every call, and knowing the policy without the
secret does not reveal the gap. A load that cannot be priced safely returns
None, which means pricing review (D-11).
"""

import hashlib
import hmac
import json
from dataclasses import dataclass

BPS = 10_000  # basis points in 100%


@dataclass(frozen=True, kw_only=True)
class PricingPolicy:
    version: str
    rounding_step: int
    ceiling_gap_bps: tuple[int, ...]  # (low, high) band
    opening_discount_bps: int
    opening_spread_bps: tuple[int, ...]  # (low, high) band
    round_target_bps: tuple[int, ...]  # share of the way from opening to cap, per round

    def __post_init__(self) -> None:
        bands = (self.ceiling_gap_bps, self.opening_spread_bps)
        targets = self.round_target_bps
        checks = (
            self.rounding_step > 0,
            all(len(band) == 2 and 0 <= band[0] <= band[1] < BPS for band in bands),
            0 <= self.opening_discount_bps < BPS,
            all(0 <= bps <= BPS for bps in targets) and list(targets) == sorted(targets),
            targets[-1:] == (BPS,),  # the last round reaches the cap
        )
        if not all(checks):
            raise ValueError(f"Invalid pricing policy {self.version!r}.")

    @classmethod
    def from_json(cls, text: str) -> "PricingPolicy":
        data = json.loads(text)
        return cls(
            version=data["version"],
            rounding_step=data["rounding_step"],
            ceiling_gap_bps=tuple(data["ceiling_gap_bps"]),
            opening_discount_bps=data["opening_discount_bps"],
            opening_spread_bps=tuple(data["opening_spread_bps"]),
            round_target_bps=tuple(data["round_target_bps"]),
        )


@dataclass(frozen=True, kw_only=True)
class Terms:
    """One load's prices. The ceiling itself is not kept here."""

    load_id: str
    policy_version: str
    opening: int
    targets: tuple[int, ...]  # the last one is the cap
    cap: int


def price_load(
    load_id: str, posted: int | None, ceiling: int | None, policy: PricingPolicy, secret: bytes
) -> Terms | None:
    """Return the load's Terms, or None if it needs pricing review."""
    if not secret:
        raise ValueError("A pricing secret is required.")
    if ceiling is None or ceiling <= 0:
        return None

    step = policy.rounding_step
    gap = _draw(secret, policy, load_id, "ceiling_gap", policy.ceiling_gap_bps)
    cap = _round_down(_less(ceiling, gap), step)
    opening = _opening(secret, policy, load_id, posted, cap)
    if not 0 < opening < cap < ceiling:
        return None

    targets = tuple(
        _round_down(opening + (cap - opening) * bps // BPS, step) for bps in policy.round_target_bps
    )
    return Terms(
        load_id=load_id, policy_version=policy.version, opening=opening, targets=targets, cap=cap
    )


def _opening(
    secret: bytes, policy: PricingPolicy, load_id: str, posted: int | None, cap: int
) -> int:
    """The posted rate less the discount if that leaves room below the cap, else a drawn spread."""
    if posted:
        opening = _round_down(_less(posted, policy.opening_discount_bps), policy.rounding_step)
        if 0 < opening < cap:
            return opening
    spread = _draw(secret, policy, load_id, "opening_spread", policy.opening_spread_bps)
    return _round_down(_less(cap, spread), policy.rounding_step)


def _draw(
    secret: bytes, policy: PricingPolicy, load_id: str, purpose: str, band: tuple[int, ...]
) -> int:
    """A number in the band that is fixed for this load but unpredictable without the secret."""
    message = f"{policy.version}|{load_id}|{purpose}".encode()
    digest = hmac.new(secret, message, hashlib.sha256).digest()
    low, high = band
    return low + int.from_bytes(digest, "big") % (high - low + 1)


def _less(amount: int, bps: int) -> int:
    return amount * (BPS - bps) // BPS


def _round_down(amount: int, step: int) -> int:
    return amount // step * step
