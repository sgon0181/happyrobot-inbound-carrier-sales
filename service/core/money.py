"""Money as positive whole numbers in the TMS's own units.

Anything else is refused as None and never rounded, because a rounded rate
is a different agreement. Reading these units as US dollars is assumption D-10.
"""

import re

MAX_DIGITS = 12
_TMS_AMOUNT = re.compile(rf"[0-9]{{1,{MAX_DIGITS}}}")
_ASK = re.compile(rf"([0-9]{{1,{MAX_DIGITS}}})(?:\.0+)?")


def parse_tms_amount(text: str | None) -> int | None:
    """Read a zero-padded TMS amount such as "0002150". Zero is not an amount."""
    if text is None or not _TMS_AMOUNT.fullmatch(text):
        return None
    return int(text) or None


def parse_ask(value: int | float | str | None) -> int | None:
    """Read a carrier's ask from the voice agent: "1500.00" is 1500, "1500.50" is refused."""
    match = _ASK.fullmatch(str(value).strip())
    if match is None:
        return None
    return int(match.group(1)) or None
