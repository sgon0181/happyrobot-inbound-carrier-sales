"""Explicit cutover from a frozen private backup to authoritative entity rows."""

import argparse
import asyncio
import copy
import hashlib
import json
from pathlib import Path

from service.config import ROOT, settings
from service.scripts.cli_platform import CliPlatform
from service.adapters.twin.client import literal
from service.adapters.twin.repository import CONTROL, GROUPS, TwinRepository


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


async def migrate(source, apply=False):
    target = ROOT / "docs/prototype-evidence/candidate-storage-cutover.json"
    if target.exists():
        raise RuntimeError(
            "Cutover already recorded. Never restore frozen state over live entities."
        )
    backup = json.loads(source.read_text())
    original = backup["canonical"]
    expected = copy.deepcopy(original["data"])
    platform = CliPlatform(settings())
    repository = TwinRepository(platform)
    frozen = (
        await platform.sql(f"SELECT id,version,data FROM proto_calls WHERE id={literal(CONTROL)}")
    )["rows"][0]
    if frozen != original:
        raise RuntimeError("Control row changed since backup; export again before cutover")
    enriched = 0
    for bid, booking in expected["bookings"].items():
        if booking["state"] == "FAILED" and not booking.get("write_intent_id"):
            continue
        for key in ("load:" + booking["load_id"], "call:" + booking["call_id"]):
            previous = expected["booking_claims"].get(key)
            if previous and previous.get("active") and previous["booking_id"] != bid:
                raise RuntimeError("Conflicting historical active claim")
            expected["booking_claims"][key] = {
                **(previous or {}),
                "booking_id": bid,
                "active": True,
                "load_id": booking["load_id"],
                "call_id": booking["call_id"],
                "write_intent_id": booking.get("write_intent_id"),
            }
        call = expected["calls"].get(booking["call_id"])
        if call is not None:
            call["booking_id"] = bid
        enriched += 1
    repaired = []
    for group in GROUPS:
        actual = {key: (version, row) for key, version, row in await repository.rows(group)}
        for key, row in expected[group].items():
            version, before = actual.get(key, (None, None))
            if before != row:
                repaired.append({"table": group, "id": key})
                if apply and not await repository.cas(group, key, version, row):
                    raise RuntimeError("Concurrent row change during cutover")
    if apply:
        for group in GROUPS:
            actual = {key: row for key, _, row in await repository.rows(group)}
            for key, row in expected[group].items():
                if actual.get(key) != row:
                    raise RuntimeError("Cutover row verification failed")
        after = (
            await platform.sql(
                f"SELECT id,version,data FROM proto_calls WHERE id={literal(CONTROL)}"
            )
        )["rows"][0]
        if after != original:
            raise RuntimeError("Frozen control row was modified")
    result = {
        "label": "LIVE_TWIN_ENTITY_CUTOVER" if apply else "CUTOVER_READ_ONLY_PLAN",
        "original_projection_mismatches": len(backup["mismatches"]),
        "entity_counts": {g: len(expected[g]) for g in GROUPS},
        "rows_repaired_or_enriched": repaired,
        "active_bookings_claims_rebuilt": enriched,
        "frozen_control_unchanged": True,
        "frozen_control_sha256": digest(original),
        "all_expected_entities_verified": bool(apply),
        "new_tms_sends": 0,
        "limit": (
            "No multi-table transaction. New hot paths use entity CAS "
            "and durable primary-key claims."
        ),
    }
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps({k: v for k, v in result.items() if k != "rows_repaired_or_enriched"}, indent=2)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    asyncio.run(migrate(args.source, args.apply))


if __name__ == "__main__":
    main()
