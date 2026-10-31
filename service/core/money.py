"""Exact whole amounts in the TMS's own units. That these are US dollars is assumption D-10."""

import re

MAX_DIGITS = 12


def parse_tms_amount(text):
    """Return a positive whole amount from TMS text, or None if it is unusable."""
    if not isinstance(text, str) or not re.fullmatch(rf"[0-9]{{1,{MAX_DIGITS}}}", text):
        return None
    return int(text) or None


def parse_ask(value):
    """Return a carrier's ask as a positive whole amount, or None. Never rounds."""
    if isinstance(value, bool):
        return None
    match = re.fullmatch(rf"([0-9]{{1,{MAX_DIGITS}}})(\.0+)?", str(value).strip())
    return (int(match.group(1)) or None) if match else None
