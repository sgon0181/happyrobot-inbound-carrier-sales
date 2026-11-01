"""Owner-operated private Gmail app-password prompt. Makes no network requests."""

import getpass
import argparse
import os
import re
import sys
import warnings
from service.config import ROOT, settings


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    if not sys.stdin.isatty():
        raise SystemExit("Run this yourself in Terminal. A private interactive prompt is required.")
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        value = getpass.getpass("Gmail app password (hidden, never your normal password): ")
    value = "".join(value.split())
    if not re.fullmatch(r"[A-Za-z]{16}", value):
        raise SystemExit("Expected a 16-letter Google app password. Nothing saved.")
    values = settings()
    if not values.get("DEMO_OTP_EMAIL"):
        raise SystemExit("Demo email is not configured. Nothing saved.")
    path = ROOT / ".env"
    lines = path.read_text().splitlines() if path.exists() else []
    updates = {"OTP_EMAIL_CREDENTIAL": value, "OTP_EMAIL_USER": values["DEMO_OTP_EMAIL"]}
    retained = [line for line in lines if line.split("=", 1)[0].strip() not in updates]
    retained.extend(key + "=" + item for key, item in updates.items())
    temporary = ROOT / "secrets/email-env-update"
    temporary.parent.mkdir(exist_ok=True, mode=0o700)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as file:
        file.write("\n".join(retained) + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)
    print("Saved privately in the ignored .env. No password was printed and no email was sent.")


if __name__ == "__main__":
    main()
