"""Typed settings, read once at startup: the only code that reads the environment or policy files.

A missing or invalid setting stops the service before it serves anything. The error
names every bad setting, and never includes a value.
"""

import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from service.core.pricing import PricingPolicy

POLICY_DIR = Path(__file__).parent / "policy"
MIN_SECRET = 24
COHORTS = frozenset({"real", "synthetic"})


class SettingsError(ValueError):
    """Lists the bad settings by name only."""


@dataclass(frozen=True, kw_only=True)
class Settings:
    tms_host: str
    tms_port: int
    tms_token: str = field(repr=False)
    fmcsa_api_key: str = field(repr=False)
    twin_api_key: str = field(repr=False)
    twin_org_id: str
    twin_environment: str
    native_workflow: dict[str, str] | None
    agent_api_key: str = field(repr=False)
    ops_api_key: str = field(repr=False)
    otp_hash_secret: bytes = field(repr=False)
    pricing_secret: bytes = field(repr=False)
    email_user: str
    email_credential: str = field(repr=False)
    contacts: dict[str, str] | None = field(repr=False)
    demo_inbox: str  # the one inbox codes go to, never an address a caller gives (D-12)
    cohort: str  # stamped on each new call, so KPIs can count real calls only (D-21)
    live_booking: bool  # each LOAD_BOOK spends a load for good, so this stays off until slice 4
    pricing: PricingPolicy
    blocked_loads: frozenset[str]


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    read = _Reader(os.environ if env is None else env)
    settings = Settings(
        tms_host=read.text("TMS_HOST"),
        tms_port=read.port("TMS_PORT"),
        tms_token=read.text("TMS_TOKEN"),
        fmcsa_api_key=read.text("FMCSA_API_KEY"),
        twin_api_key=read.text("HAPPYROBOT_API_KEY"),
        twin_org_id=read.text("HAPPYROBOT_ORG_ID"),
        twin_environment=read.choice(
            "TWIN_ENVIRONMENT", {"production", "staging"}, default="production"
        ),
        native_workflow=read.workflow(),
        agent_api_key=read.secret("AGENT_API_KEY"),
        ops_api_key=read.secret("OPS_API_KEY"),
        otp_hash_secret=read.secret("OTP_HASH_SECRET").encode(),
        pricing_secret=read.secret("PRICING_SECRET").encode(),
        email_user=read.email("OTP_EMAIL_USER"),
        email_credential=read.text("OTP_EMAIL_CREDENTIAL"),
        contacts=read.contacts(),
        demo_inbox=read.email("DEMO_OTP_EMAIL"),
        cohort=read.choice("CALL_COHORT", COHORTS, default="real"),
        live_booking=read.choice("LIVE_BOOKING", {"true", "false"}, default="false") == "true",
        pricing=PricingPolicy.from_json((POLICY_DIR / "pricing-v1.json").read_text()),
        blocked_loads=blocked_loads((POLICY_DIR / "blocked-loads-v1.json").read_text()),
    )
    if settings.agent_api_key and settings.agent_api_key == settings.ops_api_key:
        read.problems.append("AGENT_API_KEY and OPS_API_KEY must differ")
    if settings.live_booking and (not settings.contacts or read.env.get("CALL_COHORT") != "real"):
        read.problems.append(
            "LIVE_BOOKING needs explicit real CALL_COHORT and nonempty OTP_CONTACTS_JSON"
        )
    if read.problems:
        raise SettingsError("Invalid settings: " + "; ".join(read.problems))
    return settings


def blocked_loads(text: str) -> frozenset[str]:
    """Every load ID in the policy file: spent, protected or void. None is ever offered."""
    data = json.loads(text)
    ids = frozenset(load_id for key, ids in data.items() if key != "version" for load_id in ids)
    if not all(re.fullmatch(r"LD[0-9]+", load_id) for load_id in ids):
        raise SettingsError("The blocked-load list has an invalid load ID.")
    return ids


class _Reader:
    def __init__(self, env: Mapping[str, str]) -> None:
        self.env = env
        self.problems: list[str] = []

    def text(self, name: str) -> str:
        value = self.env.get(name, "").strip()
        if not value:
            self.problems.append(f"{name} is missing")
        return value

    def secret(self, name: str) -> str:
        value = self.text(name)
        if value and len(value) < MIN_SECRET:
            self.problems.append(f"{name} needs at least {MIN_SECRET} characters")
        return value

    def email(self, name: str) -> str:
        value = self.text(name)
        if value and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            self.problems.append(f"{name} is not an email address")
        return value

    def workflow(self) -> dict[str, str] | None:
        workspace = self.env.get("HAPPYROBOT_WORKSPACE_SLUG", "").strip()
        workflow = self.env.get("HAPPYROBOT_WORKFLOW_ID", "").strip()
        if not workspace and not workflow:
            return None
        if all(re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value) for value in (workspace, workflow)):
            return {"workspace": workspace, "workflow_id": workflow}
        self.problems.append(
            "HAPPYROBOT_WORKSPACE_SLUG and HAPPYROBOT_WORKFLOW_ID need safe path identifiers"
        )
        return None

    def contacts(self) -> dict[str, str] | None:
        """Optional broker-maintained pilot roster. Never accept a destination from the call."""
        raw = self.env.get("OTP_CONTACTS_JSON")
        if raw is None:
            return None
        try:
            mapping = json.loads(raw)
            if isinstance(mapping, dict) and all(
                re.fullmatch(r"[1-9][0-9]{0,7}", mc)
                and isinstance(address, str)
                and re.fullmatch(r"[a-zA-Z0-9_.%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", address)
                for mc, address in mapping.items()
            ):
                return dict(mapping)
        except ValueError:
            pass
        self.problems.append("OTP_CONTACTS_JSON must map canonical MC numbers to single addresses")
        return None

    def port(self, name: str) -> int:
        value = self.text(name)
        if value and (not value.isdigit() or not 1 <= int(value) <= 65535):
            self.problems.append(f"{name} is not a port number")
            return 0
        return int(value) if value else 0

    def choice(self, name: str, options: frozenset[str] | set[str], *, default: str) -> str:
        value = self.env.get(name, "").strip().lower() or default
        if value not in options:
            self.problems.append(f"{name} must be one of {', '.join(sorted(options))}")
        return value
