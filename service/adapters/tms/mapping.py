"""The one mapping from TMS field names to the PDF's (docs/tms-contract.md, field mapping)."""

import re
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from service.adapters.tms.protocol import MalformedReply
from service.core.models import Load, LoadSummary, Place
from service.core.money import parse_tms_amount

_FEET = re.compile(r"\s*([0-9]{1,4})ft\s*x\s*([0-9]{1,4})ft\s*x\s*([0-9]{1,4})ft\s*", re.I)
_TIMESTAMP = re.compile(r"[0-9]{14}")


def to_summary(record: Mapping[str, str]) -> LoadSummary:
    """One LOAD_QUERY record."""
    return LoadSummary(**_summary_fields(record))


def to_load(record: Mapping[str, str]) -> Load:
    """One LOAD_GET record. MAX_BUY becomes max_rate, a candidate mapping (D-10)."""
    return Load(
        **_summary_fields(record),
        delivery_datetime=parse_timestamp(record.get("DELIVERY_DT")),
        weight=parse_tms_amount(record.get("WEIGHT")),
        commodity_type=record.get("COMMODITY", ""),
        num_of_pieces=parse_tms_amount(record.get("PIECES")),
        dimensions=to_inches(record.get("DIMS", "")),
        notes=record.get("NOTES", ""),
        max_rate=parse_tms_amount(record.get("MAX_BUY")),
    )


def parse_timestamp(text: str | None) -> datetime | None:
    """Read exactly YYYYMMDDhhmmss. The TMS timezone is unconfirmed, so UTC is an assumption."""
    # strptime alone accepts short fields, so a truncated value could become a valid future date.
    if text is None or not _TIMESTAMP.fullmatch(text):
        return None
    try:
        return datetime.strptime(text, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
    except ValueError:  # 14 digits that are not a real date, such as month 13
        return None


def to_inches(dimensions: str) -> str:
    """Live records use feet and the PDF asks for inches. Free text stays as written."""
    match = _FEET.fullmatch(dimensions)
    if match is None:
        return dimensions
    length, width, height = (int(value) * 12 for value in match.groups())
    return f"{length} x {width} x {height} in"


def _summary_fields(record: Mapping[str, str]) -> dict[str, Any]:
    load_id = record.get("LOAD_ID")
    if not load_id:
        raise MalformedReply("Record without a load ID.")
    return {
        "load_id": load_id,
        "origin": _place(record, "ORIG"),
        "destination": _place(record, "DEST"),
        "pickup_datetime": parse_timestamp(record.get("PICKUP_DT")),
        "equipment_type": record.get("EQTYPE", ""),
        "loadboard_rate": parse_tms_amount(record.get("RATE")),
        "miles": parse_tms_amount(record.get("MILES")),
        "status": record.get("STATUS", ""),
    }


def _place(record: Mapping[str, str], prefix: str) -> Place:
    return Place(
        city=record.get(f"{prefix}_CITY", ""),
        state=record.get(f"{prefix}_STATE", ""),
        zip_code=record.get(f"{prefix}_ZIP", ""),
    )
