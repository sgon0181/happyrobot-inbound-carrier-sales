"""Restricted operating vocabulary for the candidate feed. Anything else needs operations review."""

import re

from service.core.models import Load, Place

# Complete operating clauses observed on the candidate feed. Unknown free text requires a
# rep to interpret it, since reading even one arbitrary clause may disclose private terms.
_NOTE_CLAUSES = re.compile(
    r"coil load|coil racks required|drop trailer at destination|appt required|"
    r"live unload|[0-9]{1,2}h detention free, then \$[0-9]{1,3}/h|"
    r"reefer set -?[0-9]{1,2}f continuous",
    re.IGNORECASE | re.ASCII,
)


OPERATING_CLAUSES = frozenset(
    {
        "backhaul preferred",
        "empty trailer at pu",
        "bring two copies of bol",
        "cdl class a only",
        "call dispatch on arrival",
        "dock 14",
        "sign in at guard shack",
        "driver assist required",
        "driver pays, will reimburse with receipt",
        "driver supplies",
        "edge protectors at pu",
        "eight-point securement",
        "equipment rolls on/off",
        "frozen",
        "late = reschedule",
        "lumber tarps",
        "lumper on receiver",
        "match seal# at pu",
        "no paperwork at pickup",
        "no straps over coils",
        "no touch",
        "pickup numbers on rate con",
        "place near rear doors",
        "pre-loaded trailer",
        "ramps at receiver",
        "securement to load pu",
        "steel banding only",
        "strict appt window",
        "travel daylight only",
        "chains required: 4x grade 70",
        "straps required: 4x 4-inch",
        "tarps required (2x 24ft)",
        "set 0f continuous",
        "multi-temp: front zone 34f, rear zone 0f",
        "tempurature recorder required",
    }
)

COMMODITIES = frozenset(
    {
        "auto parts",
        "beverages",
        "electronics",
        "frozen goods",
        "general freight",
        "machinery",
        "paper products",
        "lumber",
        "produce",
        "steel coils",
    }
)
_DIMENSIONS = re.compile(r"[1-9][0-9]{0,4} x [1-9][0-9]{0,4} x [1-9][0-9]{0,4} in")


def safe_to_quote(load: Load) -> bool:
    """Only carrier-operating vocabulary crosses the TMS free-text boundary."""
    return (
        valid_load_id(load.load_id)
        and all(_public_place(place) for place in (load.origin, load.destination))
        and load.equipment_type in {"DRY_VAN", "REEFER", "FLATBED", "STEP_DECK", "POWER_ONLY"}
        and _valid_shipment(load)
        and _consistent_notes(load)
        and bool(load.commodity_type and load.commodity_type.lower() in COMMODITIES)
        and bool(_DIMENSIONS.fullmatch(load.dimensions))
        and quotable_notes(load.notes)
    )


def valid_load_id(load_id: str) -> bool:
    return bool(re.fullmatch(r"LD[0-9]{1,16}", load_id))


def _public_place(place: Place) -> bool:
    return place.city in MARKETS.get(place.state, ()) and bool(
        re.fullmatch(r"[0-9]{5}", place.zip_code)
    )


def _valid_shipment(load: Load) -> bool:
    if (
        not load.pickup_datetime
        or not load.delivery_datetime
        or load.delivery_datetime <= load.pickup_datetime
    ):
        return False
    return all(isinstance(v, int) and v > 0 for v in (load.weight, load.num_of_pieces, load.miles))


def _consistent_notes(load: Load) -> bool:
    notes = load.notes.lower()
    if (
        any(word in notes for word in ("reefer", "continuous", "frozen", "multi-temp"))
        and load.equipment_type != "REEFER"
    ):
        return False
    return not ("no touch" in notes and "driver assist required" in notes)


def quotable_notes(notes: str) -> bool:
    clauses = [part.strip() for part in notes.rstrip(".").split(".") if part.strip()]
    return all(
        clause.lower() in OPERATING_CLAUSES or _NOTE_CLAUSES.fullmatch(clause) for clause in clauses
    )


MARKETS: dict[str, tuple[str, ...]] = {
    "AK": ("Anchorage",),
    "AL": ("Birmingham", "Huntsville", "Mobile"),
    "AR": ("Little Rock",),
    "AZ": ("Phoenix", "Tucson"),
    "CA": (
        "Anaheim",
        "Bakersfield",
        "Fresno",
        "Long Beach",
        "Los Angeles",
        "Oakland",
        "Sacramento",
        "San Diego",
        "San Francisco",
        "San Jose",
        "Stockton",
    ),
    "CO": ("Colorado Springs", "Denver"),
    "CT": ("Hartford", "New Haven"),
    "DC": ("Washington",),
    "FL": (
        "Fort Lauderdale",
        "Jacksonville",
        "Miami",
        "Orlando",
        "Sarasota",
        "Tallahassee",
        "Tampa",
        "West Palm Beach",
    ),
    "GA": ("Atlanta", "Augusta", "Savannah"),
    "HI": ("Honolulu",),
    "IA": ("Cedar Rapids", "Des Moines"),
    "ID": ("Boise",),
    "IL": ("Chicago", "Springfield"),
    "IN": ("Fort Wayne", "Indianapolis"),
    "KS": ("Wichita",),
    "KY": ("Lexington", "Louisville"),
    "LA": ("Baton Rouge", "New Orleans", "Shreveport"),
    "MA": ("Boston", "Worcester"),
    "MD": ("Baltimore",),
    "ME": ("Portland",),
    "MI": ("Detroit", "Flint"),
    "MN": ("Saint Paul",),
    "MO": ("Kansas City", "St. Louis"),
    "MS": ("Jackson",),
    "MT": ("Billings",),
    "NC": ("Charlotte", "Greensboro", "Raleigh"),
    "ND": ("Fargo",),
    "NE": ("Omaha",),
    "NJ": ("Jersey City", "Newark"),
    "NM": ("Albuquerque",),
    "NV": ("Las Vegas", "Reno"),
    "NY": ("Albany", "Buffalo", "New York", "Rochester", "Syracuse"),
    "OH": ("Akron", "Cincinnati", "Cleveland", "Columbus", "Dayton", "Toledo"),
    "OK": ("Oklahoma City", "Tulsa"),
    "OR": ("Eugene", "Portland", "Salem"),
    "PA": ("Allentown", "Philadelphia", "Pittsburgh"),
    "RI": ("Providence",),
    "SC": ("Charleston", "Columbia", "Greenville"),
    "SD": ("Sioux Falls",),
    "TN": ("Chattanooga", "Knoxville", "Memphis", "Nashville"),
    "TX": (
        "Amarillo",
        "Austin",
        "Corpus Christi",
        "Dallas",
        "El Paso",
        "Fort Worth",
        "Houston",
        "Lubbock",
        "San Antonio",
    ),
    "UT": ("Salt Lake City",),
    "VA": ("Norfolk", "Richmond", "Virginia Beach"),
    "WA": ("Seattle", "Spokane", "Tacoma"),
    "WI": ("Green Bay", "Madison", "Milwaukee"),
    "WY": ("Cheyenne",),
}
