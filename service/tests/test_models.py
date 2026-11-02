"""Load types keep the private ceiling out of anything printed or logged."""

import dataclasses

import pytest

from service.core.models import Load, Place

CEILING = 987654


def a_load() -> Load:
    place = Place(city="Atlanta", state="GA", zip_code="30303")
    return Load(
        load_id="LD1",
        origin=place,
        destination=place,
        pickup_datetime=None,
        equipment_type="DRY_VAN",
        loadboard_rate=2150,
        miles=785,
        status="OPEN",
        delivery_datetime=None,
        weight=42000,
        commodity_type="PALLETS",
        num_of_pieces=26,
        dimensions="",
        notes="",
        max_rate=CEILING,
    )


def test_the_ceiling_never_appears_when_a_load_is_printed() -> None:
    load = a_load()
    assert load.max_rate == CEILING
    assert str(CEILING) not in repr(load)
    assert str(CEILING) not in str(load)


def test_loads_cannot_be_changed_after_they_are_read() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        a_load().max_rate = 1  # type: ignore[misc]
