"""Explicit inventory exclusions, separate from dynamic durable booking claims."""

import json
from pathlib import Path


def blocked_loads():
    policy = json.loads((Path(__file__).parents[1] / "policy/blocked-loads-v1.json").read_text())
    return frozenset(load for group in ("spent", "protected", "void") for load in policy[group])


BLOCKED_LOADS = blocked_loads()
