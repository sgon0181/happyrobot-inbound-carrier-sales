"""Explicit cloud deployment or an isolated local simulator, followed by browser readiness."""

import argparse
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REVIEW_URL = "http://127.0.0.1:3081/enter/rep"
DEPLOY_KEYS = frozenset(
    [
        "TMS_HOST",
        "TMS_PORT",
        "TMS_TOKEN",
        "FMCSA_API_KEY",
        "HAPPYROBOT_API_KEY",
        "HAPPYROBOT_ORG_ID",
        "TWIN_ENVIRONMENT",
        "HAPPYROBOT_WORKSPACE_SLUG",
        "HAPPYROBOT_WORKFLOW_ID",
        "AGENT_API_KEY",
        "OPS_API_KEY",
        "OTP_HASH_SECRET",
        "PRICING_SECRET",
        "OTP_EMAIL_USER",
        "OTP_EMAIL_CREDENTIAL",
        "DEMO_OTP_EMAIL",
        "OTP_CONTACTS_JSON",
        "CALL_COHORT",
        "LIVE_BOOKING",
    ]
)


def run(executable: str, *args: str, input_text: str | None = None) -> None:
    binary = shutil.which(executable)
    if binary is None:
        raise SystemExit(f"Install {executable} before running this command.")
    subprocess.run(  # noqa: S603, resolved program and separate validated arguments, no shell
        [binary, *args], cwd=ROOT, input=input_text, text=True, check=True
    )


def settings() -> dict[str, str]:
    """Read dotenv literals without executing shell syntax or expanding substitutions."""
    values = {}
    path = ROOT / ".env"
    for line in path.read_text().splitlines() if path.exists() else []:
        key, _, value = line.partition("=")
        if key in DEPLOY_KEYS:
            values[key] = value.strip().strip('"').strip("'")
    values.update({key: value for key, value in os.environ.items() if key in DEPLOY_KEYS})
    return values


def target() -> tuple[str, str]:
    app, url = os.environ.get("APP", ""), os.environ.get("APP_URL", "")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,62}", app):
        raise SystemExit(
            "Choose an explicit Fly target: make deploy APP=<app> APP_URL=<native-app-url>"
        )
    parsed = urlparse(url)
    allowed = ("happyrobot.dev", "custom-apps.happyrobot.ai", "platform.happyrobot.ai")
    host = parsed.hostname or ""
    if (
        parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or not any(host == domain or host.endswith("." + domain) for domain in allowed)
    ):
        raise SystemExit("APP_URL must be the intended HTTPS HappyRobot App URL.")
    return app, url


def ready(app: str, key: str) -> bool:
    request = urllib.request.Request(
        f"https://{app}.fly.dev/health", headers={"Authorization": f"Bearer {key}"}
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310, fixed HTTPS host
            body = json.load(response)
        return (
            isinstance(body, dict) and body.get("status") == "ok" and body.get("tms") == "reachable"
        )
    except (OSError, ValueError, urllib.error.URLError):
        return False


def open_app(url: str) -> None:
    print(f"Ready: {url}")
    if not webbrowser.open(url):
        print("No browser was available. Open the ready URL above.")


def deploy(*, secrets_only: bool) -> None:
    app, url = target()
    values = settings()
    key = values.get("OPS_API_KEY", "")
    if not key:
        raise SystemExit("Set OPS_API_KEY in the environment or .env for authenticated readiness.")
    if secrets_only:
        payload = "".join(f"{name}={value}\n" for name, value in values.items())
        run("fly", "secrets", "import", "--app", app, "--stage", input_text=payload)
        return
    run("fly", "deploy", "--config", str(ROOT / "fly.toml"), "--app", app, "--ha=false")
    for _ in range(10):
        if ready(app, key):
            open_app(url)
            return
        time.sleep(2)
    raise SystemExit(
        "Deployment finished but authenticated readiness failed. The App was not opened."
    )


def local(*, stop: bool) -> None:
    compose = ("compose", "-f", str(ROOT / "compose.review.yml"))
    if stop:
        run("docker", *compose, "down", "--volumes")
        return
    run("docker", *compose, "up", "--build", "--force-recreate", "--wait")
    open_app(REVIEW_URL)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("review", "review-down", "deploy", "secrets"))
    args = parser.parse_args()
    if args.mode in {"review", "review-down"}:
        local(stop=args.mode == "review-down")
    else:
        deploy(secrets_only=args.mode == "secrets")


if __name__ == "__main__":
    main()
