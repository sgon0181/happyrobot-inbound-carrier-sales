"""Load selection: only open, future, unblocked loads on the asked lane, earliest first."""

from datetime import UTC, datetime, timedelta

from service.core.loads import MAX_OFFERS, is_offerable, select_offers
from service.core.models import LoadSummary, Place

NOW = datetime(2026, 11, 2, 12, tzinfo=UTC)


def a_load(
    load_id: str = "LD1",
    *,
    status: str = "OPEN",
    hours: float | None = 24,
    equipment: str = "DRY_VAN",
    origin: str = "CA",
    destination: str = "KY",
) -> LoadSummary:
    return LoadSummary(
        load_id=load_id,
        origin=Place(city="Fresno", state=origin, zip_code="93650"),
        destination=Place(city="Louisville", state=destination, zip_code="40202"),
        pickup_datetime=None if hours is None else NOW + timedelta(hours=hours),
        equipment_type=equipment,
        loadboard_rate=3000,
        miles=2100,
        status=status,
    )


def test_an_open_future_load_is_offerable() -> None:
    assert is_offerable(a_load(), NOW)


def test_pending_past_undated_and_excluded_loads_are_not() -> None:
    assert not is_offerable(a_load(status="PENDING"), NOW)
    assert not is_offerable(a_load(hours=-1), NOW)
    assert not is_offerable(a_load(hours=0), NOW)  # picking up right now is too late
    assert not is_offerable(a_load(hours=None), NOW)
    assert not is_offerable(a_load("LD9"), NOW, frozenset({"LD9"}))


def test_offers_match_the_lane_and_come_earliest_first() -> None:
    loads = [
        a_load("late", hours=48),
        a_load("reefer", equipment="REEFER"),
        a_load("texas", origin="TX"),
        a_load("ohio", destination="OH"),
        a_load("early", hours=2),
    ]
    picked = select_offers(loads, NOW, equipment="DRY_VAN", origin_state="CA", dest_state="KY")
    assert [load.load_id for load in picked] == ["early", "late"]


def test_unset_criteria_match_anything_and_at_most_three_are_offered() -> None:
    loads = [a_load(f"LD{hour}", hours=hour) for hour in (5, 1, 4, 2, 3)]
    picked = select_offers(loads, NOW)
    assert len(picked) == MAX_OFFERS
    assert [load.load_id for load in picked] == ["LD1", "LD2", "LD3"]
