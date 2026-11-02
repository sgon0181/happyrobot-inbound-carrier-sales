"""TMS fields become the PDF's fields. Unusable values become None rather than guesses."""

from datetime import timedelta

import pytest

from service.adapters.tms.mapping import to_load, to_summary
from service.adapters.tms.protocol import MalformedReply
from service.core.models import Place
from service.tests.fake_tms import make_load


def test_a_full_record_maps_to_pdf_fields() -> None:
    load = to_load(make_load("LD1", RATE="0002709", MAX_BUY="0002922"))
    assert (load.load_id, load.loadboard_rate, load.max_rate) == ("LD1", 2709, 2922)
    assert load.origin == Place(city="Dallas", state="TX", zip_code="75201")
    assert (load.weight, load.num_of_pieces, load.miles) == (42000, 24, 780)
    assert load.equipment_type == "DRY_VAN"
    assert load.status == "OPEN"


def test_a_search_record_has_no_detail_fields() -> None:
    summary = to_summary(make_load("LD1"))
    assert summary.load_id == "LD1"
    assert not hasattr(summary, "max_rate")


@pytest.mark.parametrize(
    ("dims", "expected"),
    [
        ("40ft x 8ft x 9ft", "480 x 96 x 108 in"),  # live records use feet
        ("53FT X 8FT X 9FT", "636 x 96 x 108 in"),
        ("48X40 STD PALLETS", "48X40 STD PALLETS"),  # free text stays as written
        ("", ""),
    ],
)
def test_dimensions_convert_from_feet_to_inches(dims: str, expected: str) -> None:
    assert to_load(make_load(DIMS=dims)).dimensions == expected


@pytest.mark.parametrize("value", ["0", "abc", "12.5", ""])
def test_an_unusable_ceiling_becomes_none(value: str) -> None:
    assert to_load(make_load(MAX_BUY=value)).max_rate is None


def test_a_missing_ceiling_becomes_none() -> None:
    record = make_load()
    del record["MAX_BUY"]
    assert to_load(record).max_rate is None


def test_timestamps_are_read_as_utc_and_bad_ones_become_none() -> None:
    pickup = to_load(make_load(PICKUP_DT="20261031030801")).pickup_datetime
    assert pickup is not None
    assert (pickup.utcoffset(), pickup.hour) == (timedelta(0), 3)
    assert to_load(make_load(PICKUP_DT="2026-10-31")).pickup_datetime is None


def test_blank_notes_stay_blank() -> None:
    assert to_load(make_load(NOTES="")).notes == ""


def test_a_record_without_a_load_id_is_refused() -> None:
    with pytest.raises(MalformedReply):
        to_summary(make_load(""))
