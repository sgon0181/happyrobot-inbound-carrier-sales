"""Load selection: only open, future, unblocked loads on the asked lane, earliest first."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from service.adapters.tms.mapping import to_load
from service.core.loads import MAX_OFFERS, is_offerable, public_view, search_terms, select_offers
from service.core.models import LoadSummary, Place
from service.tests.fake_tms import make_load

NOW = datetime(2026, 11, 2, 12, tzinfo=UTC)
CENTRAL = ZoneInfo("America/Chicago")


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


def test_search_terms_are_normalized_and_blank_means_unset() -> None:
    assert search_terms(" Dry-Van ", "tx", "") == {
        "equipment": "DRY_VAN",
        "origin_state": "TX",
        "dest_state": None,
    }
    assert search_terms("refrigerated", None, None) == {
        "equipment": "REEFER",
        "origin_state": None,
        "dest_state": None,
    }


def test_unreadable_or_missing_search_terms_are_refused() -> None:
    for terms in (("boat", "TX", None), (None, "Texas", None), (None, None, "G"), ("", " ", None)):
        assert search_terms(*terms) is None


def test_the_public_view_is_an_allowlist_without_the_rates() -> None:
    load = to_load(make_load(MAX_BUY="2345", RATE="2000"))
    view = public_view(load, 1900, display_timezone=CENTRAL)
    assert view["offer"] == 1900
    assert (view["origin"], view["destination"]) == ("Dallas, TX", "Atlanta, GA")
    assert view["pickup_datetime"] == "2099-12-31T08:00:00+00:00"
    assert not {"max_rate", "loadboard_rate", "status"} & set(view)


@pytest.mark.parametrize(
    ("pickup", "display"),
    [
        ("20261115231400", "November 15 at 5:14 PM Central (CST)"),
        ("20260715231400", "July 15 at 6:14 PM Central (CDT)"),
        ("20261108050400", "November 7 at 11:04 PM Central (CST)"),
        ("20261101063000", "November 1 at 1:30 AM Central (CDT)"),
        ("20261101073000", "November 1 at 1:30 AM Central (CST)"),
        ("20261108013600", "November 7 at 7:36 PM Central (CST)"),
        ("20261108010600", "November 7 at 7:06 PM Central (CST)"),
        ("20261108060000", "November 8 at 12:00 AM Central (CST)"),
        ("20261108180000", "November 8 at 12:00 PM Central (CST)"),
    ],
)
def test_voice_times_match_central_display_including_day_and_dst_changes(
    pickup: str, display: str
) -> None:
    view = public_view(
        to_load(make_load(PICKUP_DT=pickup, DELIVERY_DT=pickup)), 1900, display_timezone=CENTRAL
    )
    assert view["pickup_time_display"] == display
    assert view["delivery_time_display"] == display
    assert str(view["pickup_datetime"]).endswith("+00:00")  # source instant is retained
    assert not {"max_rate", "loadboard_rate"} & set(view)


def test_missing_load_times_have_no_invented_speech_time() -> None:
    view = public_view(
        to_load(make_load(PICKUP_DT="", DELIVERY_DT="")), 1900, display_timezone=CENTRAL
    )
    assert view["pickup_time_display"] is None
    assert view["delivery_time_display"] is None
