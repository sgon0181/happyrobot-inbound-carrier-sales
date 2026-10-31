"""The one mapping from TMS fields to the PDF's load fields."""

from datetime import datetime, timezone
import re

from service.adapters.tms.protocol import MalformedReply
from service.core.models import BookingEvidence, Load, LoadSummary, Place
from service.core.money import parse_tms_amount

_FEET = re.compile(r"\s*([0-9]{1,4})ft\s*x\s*([0-9]{1,4})ft\s*x\s*([0-9]{1,4})ft\s*", re.I)


def parse_timestamp(text):
    """Read YYYYMMDDhhmmss. The TMS timezone is unconfirmed, so UTC is an assumption."""
    try:
        return datetime.strptime(text or "", "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def to_inches(dimensions):
    """Live records use feet and the PDF asks for inches. Free text stays as written."""
    match = _FEET.fullmatch(dimensions)
    if not match:
        return dimensions
    length, width, height = (int(value) * 12 for value in match.groups())
    return f"{length} x {width} x {height} in"


def _place(record, prefix):
    return Place(
        record.get(f"{prefix}_CITY", ""),
        record.get(f"{prefix}_STATE", ""),
        record.get(f"{prefix}_ZIP", ""),
    )


def _summary_fields(record):
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


def to_summary(record):
    return LoadSummary(**_summary_fields(record))


def to_load(record):
    return Load(
        **_summary_fields(record),
        delivery_datetime=parse_timestamp(record.get("DELIVERY_DT")),
        weight=parse_tms_amount(record.get("WEIGHT")),
        commodity_type=record.get("COMMODITY", ""),
        num_of_pieces=parse_tms_amount(record.get("PIECES")),
        dimensions=to_inches(record.get("DIMS", "")),
        notes=record.get("NOTES", ""),
        max_rate=parse_tms_amount(record.get("MAX_BUY")),
        evidence=_evidence(record),
    )


def _evidence(record):
    reference = record.get("BOOKING_REF")
    mc = record.get("MC_NUM")
    rate = parse_tms_amount(record.get("AGREED_RATE"))
    if reference and mc and rate:
        return BookingEvidence(reference, mc, rate)
    return None
