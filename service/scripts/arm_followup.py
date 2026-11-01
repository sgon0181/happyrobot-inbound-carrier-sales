"""Append permission for one fresh disposable load. Never sends LOAD_BOOK."""

import argparse
import asyncio
from datetime import datetime, timezone
import uuid
from service.config import settings
from service.adapters.tms.client import TmsClient, TmsSettings
from service.adapters.twin.repository import TwinRepository
from service.adapters.twin.bookings import PROTECTED
from service.scripts.cli_platform import CliPlatform
from service.core.campaign import intents
from service.core.loads import is_offerable


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--load-id", required=True)
    parser.add_argument("--one-additional-send", action="store_true", required=True)
    args = parser.parse_args()
    v = settings()
    tms = TmsClient(
        TmsSettings(v["TMS_HOST"], int(v["TMS_PORT"]), v["TMS_TOKEN"], booking_enabled=False)
    )
    load = await tms.get(args.load_id)
    if not load or not is_offerable(load, datetime.now(timezone.utc), PROTECTED | {"LD01094"}):
        raise SystemExit("Fresh eligible disposable load required. No permission added.")
    repository = TwinRepository(CliPlatform(v))
    identity = "followup-authorization-" + uuid.uuid4().hex

    def append(data):
        prior = intents(data)
        if len(prior) != 1 or prior[0].get("reference") != "3PUHTGRJNDQ5EKMM":
            raise ValueError("Unexpected prior ledger. Review instead of resetting.")
        if any(b["load_id"] == args.load_id and b.get("write_intent_id") for b in prior):
            raise ValueError("Load already spent.")
        if any(
            e.get("action") == "live_booking_authorization" and not e.get("consumed_intent_id")
            for e in data["call_events"].values()
        ):
            raise ValueError("An unconsumed permission already exists.")
        data["call_events"][identity] = {
            "action": "live_booking_authorization",
            "call_id": None,
            "load_id": args.load_id,
            "baseline_intent_ids": sorted(b["write_intent_id"] for b in prior),
            "consumed_intent_id": None,
            "mc": "138328",
            "at": datetime.now(timezone.utc).isoformat(),
            "source": "Owner continuation instruction on 2026-11-01 after corrected-live-call requirement was explained.",
            "scope": "Exactly one additional fresh-load send for the owner call. No resend, no namespace or cohort reset.",
        }
        return identity

    await repository.update(append)
    if repository.pending:
        await asyncio.gather(*repository.pending)
    print("Appended one-send permission for", args.load_id, "under", identity, "; no booking sent.")


if __name__ == "__main__":
    asyncio.run(main())
