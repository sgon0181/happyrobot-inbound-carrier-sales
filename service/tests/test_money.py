"""Money is a positive whole number. Anything else is refused, never rounded."""

import pytest

from service.core.money import parse_ask, parse_tms_amount


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2709", 2709),
        ("0002150", 2150),  # the TMS pads numbers with zeros
        ("999999999999", 999999999999),  # 12 digits, the most allowed
        ("1234567890123", None),  # 13 digits
        ("0", None),  # zero is not an amount
        ("-1", None),
        ("12.5", None),
        ("1e3", None),
        (" 12", None),  # the protocol trims padding before this runs
        ("abc", None),
        ("", None),
        (None, None),
    ],
)
def test_tms_amounts(text: str | None, expected: int | None) -> None:
    assert parse_tms_amount(text) == expected


@pytest.mark.parametrize(
    ("ask", "expected"),
    [
        (1500, 1500),
        ("1500", 1500),
        (" 1500 ", 1500),
        ("1500.00", 1500),
        (1500.0, 1500),
        (1500.5, None),  # never rounded
        ("1500.50", None),
        ("$1,500", None),  # the agent must send a plain number
        ("1e3", None),
        (-5, None),
        (0, None),
        ("0", None),
        (True, None),
        ("", None),
        (None, None),
    ],
)
def test_carrier_asks(ask: int | float | str | None, expected: int | None) -> None:
    assert parse_ask(ask) == expected
