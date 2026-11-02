"""One-time codes: 5 minutes, 2 sends, 3 wrong tries per call, and only a hash is kept."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from service.core.codes import (
    Checked,
    CodeState,
    Issued,
    check,
    code_hash,
    for_new_mc,
    issue,
    new_code,
    normalize_code,
    tries_left,
)

NOW = datetime(2026, 11, 2, 12, tzinfo=UTC)
SECRET = b"code-secret"
RIGHT = code_hash(SECRET, "run-1", "123456")
WRONG = code_hash(SECRET, "run-1", "654321")


def issued(**changes: object) -> CodeState:
    state, _ = issue(CodeState(), RIGHT, NOW)
    return replace(state, **changes)  # type: ignore[arg-type]


def test_codes_are_six_random_digits() -> None:
    codes = {new_code() for _ in range(200)}
    assert all(len(code) == 6 and code.isdigit() for code in codes)
    assert len(codes) > 190


def test_the_hash_is_bound_to_the_call_and_the_secret() -> None:
    assert code_hash(SECRET, "run-1", "123456") != code_hash(SECRET, "run-2", "123456")
    assert code_hash(SECRET, "run-1", "123456") != code_hash(b"other", "run-1", "123456")
    assert "123456" not in RIGHT


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("123456", "123456"),
        ("123 456", "123456"),
        ("12-34-56", "123456"),
        ("12345", None),
        ("12345a", None),
    ],
)
def test_spoken_codes_are_normalized(text: str, expected: str | None) -> None:
    assert normalize_code(text) == expected


def test_a_code_lasts_five_minutes_and_uses_a_send() -> None:
    state, result = issue(CodeState(), RIGHT, NOW)
    assert result is Issued.ISSUED
    assert (state.hash, state.expires_at, state.sends) == (RIGHT, NOW + timedelta(minutes=5), 1)


def test_a_third_send_is_refused() -> None:
    state, _ = issue(issued(), WRONG, NOW)
    assert state.sends == 2
    assert issue(state, RIGHT, NOW) == (state, Issued.SEND_LIMIT)


def test_no_code_is_sent_once_verified_or_locked() -> None:
    assert issue(issued(consumed_at=NOW), RIGHT, NOW)[1] is Issued.ALREADY_VERIFIED
    assert issue(issued(failed=3), RIGHT, NOW)[1] is Issued.LOCKED


def test_the_right_code_is_consumed_in_the_same_state_change() -> None:
    state, result = check(issued(), RIGHT, NOW + timedelta(minutes=4))
    assert result is Checked.VERIFIED
    assert state.consumed_at == NOW + timedelta(minutes=4)
    assert check(state, WRONG, NOW)[1] is Checked.VERIFIED  # a repeat answers from state


def test_three_wrong_tries_lock_the_call() -> None:
    state = issued()
    results = []
    for _ in range(3):
        state, result = check(state, WRONG, NOW)
        results.append((result, tries_left(state)))
    assert results == [(Checked.WRONG, 2), (Checked.WRONG, 1), (Checked.LOCKED, 0)]
    assert check(state, RIGHT, NOW)[1] is Checked.LOCKED  # even the right code, now


def test_an_expired_code_fails_without_using_a_try() -> None:
    state, result = check(issued(), RIGHT, NOW + timedelta(minutes=5))
    assert result is Checked.EXPIRED
    assert state.failed == 0


def test_checking_before_any_code_was_sent() -> None:
    assert check(CodeState(), RIGHT, NOW) == (CodeState(), Checked.NO_CODE)


def test_a_new_mc_needs_a_new_code_but_keeps_the_budgets() -> None:
    state = for_new_mc(issued(failed=2, consumed_at=NOW))
    assert (state.hash, state.expires_at, state.consumed_at) == (None, None, None)
    assert (state.sends, state.failed) == (1, 2)
