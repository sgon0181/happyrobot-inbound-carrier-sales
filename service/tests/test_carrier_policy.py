"""Carrier eligibility: only positive FMCSA evidence passes. The ledger's real cases come first."""

import pytest

from service.core.carrier_policy import ELIGIBLE, Authority, assess, normalize_mc

ACTIVE = {
    "legalName": "WERNER ENTERPRISES INC",
    "allowedToOperate": "Y",
    "commonAuthorityStatus": "A",
    "contractAuthorityStatus": "A",
    "statusCode": "A",
    "oosDate": None,
}
INACTIVE = {  # MC 134652 and MC 872144 in docs/test-carriers.md look like this
    "legalName": "MALL TRUCKING",
    "allowedToOperate": "Y",
    "commonAuthorityStatus": "N",
    "contractAuthorityStatus": "I",
    "statusCode": "I",
    "oosDate": None,
}


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("138328", "138328"),
        ("MC-138328", "138328"),
        ("mc 138 328", "138328"),
        ("0138328", "138328"),
        ("MC", None),
        ("123456789", None),  # nine digits
        ("0", None),
        ("13832A", None),
        ("", None),
    ],
)
def test_mc_numbers_are_normalized(text: str, expected: str | None) -> None:
    assert normalize_mc(text) == expected


def test_an_active_carrier_passes_with_its_name() -> None:
    assert assess([ACTIVE]) == Authority(True, ELIGIBLE, "WERNER ENTERPRISES INC")


def test_an_inactive_carrier_fails_although_it_shows_allowed_to_operate() -> None:
    assert assess([INACTIVE]) == Authority(False, "registration_not_active", "MALL TRUCKING")


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"statusCode": None}, "registration_not_active"),
        ({"allowedToOperate": "N"}, "not_allowed_to_operate"),
        ({"allowedToOperate": None}, "not_allowed_to_operate"),
        ({"commonAuthorityStatus": "I", "contractAuthorityStatus": "N"}, "no_active_authority"),
        ({"oosDate": "2026-10-01"}, "out_of_service_or_unknown"),
        ({"outOfService": "Y"}, "out_of_service_or_unknown"),  # contradicts the empty date
        ({"outOfService": ""}, "out_of_service_or_unknown"),
        ({"outOfServiceDate": "2026-10-01"}, "out_of_service_or_unknown"),
    ],
)
def test_any_missing_or_negative_signal_fails_closed(
    change: dict[str, object], reason: str
) -> None:
    assert assess([ACTIVE | change]).reason == reason


def test_a_record_without_an_out_of_service_date_fails_closed() -> None:
    record = dict(ACTIVE)
    del record["oosDate"]
    assert assess([record]).reason == "out_of_service_or_unknown"


def test_an_explicit_no_on_the_out_of_service_flag_still_passes() -> None:
    assert assess([ACTIVE | {"outOfService": "N"}]).eligible


def test_one_active_authority_is_enough_and_case_does_not_matter() -> None:
    record = ACTIVE | {
        "commonAuthorityStatus": "n",
        "contractAuthorityStatus": "a",
        "statusCode": "a",
    }
    assert assess([record]).eligible


def test_no_records_or_several_records_are_not_eligible() -> None:
    assert assess([]) == Authority(False, "not_found")
    assert assess([ACTIVE, ACTIVE]) == Authority(False, "ambiguous_carrier_match")


def test_the_trading_name_is_used_when_there_is_no_legal_name() -> None:
    record = ACTIVE | {"legalName": " ", "dbaName": "WERNER"}
    assert assess([record]).carrier_name == "WERNER"
