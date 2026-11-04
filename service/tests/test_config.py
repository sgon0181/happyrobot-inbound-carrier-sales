"""Settings: a bad setting stops startup, named but never shown."""

import pytest

from service.config import SettingsError, blocked_loads, load_settings

ENV = {
    "TMS_HOST": "tms.example.test",
    "TMS_PORT": "9000",
    "TMS_TOKEN": "tms-token-value",
    "FMCSA_API_KEY": "fmcsa-key-value",
    "HAPPYROBOT_API_KEY": "twin-key-value",
    "HAPPYROBOT_ORG_ID": "org-id",
    "AGENT_API_KEY": "agent-key-" + "a" * 20,
    "OPS_API_KEY": "ops-key-" + "o" * 20,
    "OTP_HASH_SECRET": "otp-secret-" + "s" * 20,
    "PRICING_SECRET": "pricing-secret-" + "p" * 20,
    "OTP_EMAIL_USER": "sender@example.test",
    "OTP_EMAIL_CREDENTIAL": "app-password-value",
    "DEMO_OTP_EMAIL": "inbox@example.test",
}


def test_a_complete_environment_loads_with_safe_defaults() -> None:
    settings = load_settings(ENV)
    assert (settings.tms_port, settings.cohort, settings.live_booking) == (9000, "real", False)
    assert settings.pricing.version == "pricing-v1"
    assert {"LD01062", "LD01023", "LD01069"} <= settings.blocked_loads  # spent, protected, void


def test_secrets_never_appear_in_repr() -> None:
    text = repr(load_settings(ENV))
    for name in ("TMS_TOKEN", "FMCSA_API_KEY", "AGENT_API_KEY", "OTP_EMAIL_CREDENTIAL"):
        assert ENV[name] not in text


def test_every_missing_setting_is_named_at_once() -> None:
    with pytest.raises(SettingsError) as caught:
        load_settings({})
    message = str(caught.value)
    for name in ("TMS_HOST", "FMCSA_API_KEY", "AGENT_API_KEY", "DEMO_OTP_EMAIL"):
        assert f"{name} is missing" in message


@pytest.mark.parametrize(
    ("name", "value", "problem"),
    [
        ("AGENT_API_KEY", "short", "at least 24"),
        ("TMS_PORT", "90000", "not a port"),
        ("DEMO_OTP_EMAIL", "not-an-email", "not an email"),
        ("CALL_COHORT", "demo", "must be one of"),
        ("LIVE_BOOKING", "yes", "must be one of"),
        ("OPS_API_KEY", ENV["AGENT_API_KEY"], "must differ"),
    ],
)
def test_an_invalid_setting_is_named_without_its_value(name: str, value: str, problem: str) -> None:
    with pytest.raises(SettingsError, match=problem) as caught:
        load_settings(ENV | {name: value})
    assert value not in str(caught.value)


def test_live_booking_is_on_only_when_set_to_true() -> None:
    assert load_settings(ENV | {"LIVE_BOOKING": "TRUE"}).live_booking
    assert load_settings(ENV | {"CALL_COHORT": "synthetic"}).cohort == "synthetic"


def test_a_bad_load_id_in_the_blocked_list_is_refused() -> None:
    with pytest.raises(SettingsError):
        blocked_loads('{"version": "x", "spent": ["LD1", "DROP TABLE"]}')


def test_parse_private_contact_roster_without_echoing_addresses() -> None:
    assert load_settings(ENV).contacts is None
    assert load_settings(ENV | {"OTP_CONTACTS_JSON": "{}"}).contacts == {}
    contacts = '{"138328":"carrier@example.test"}'
    settings = load_settings(ENV | {"OTP_CONTACTS_JSON": contacts})
    assert settings.contacts == {"138328": "carrier@example.test"}
    assert "carrier@example.test" not in repr(settings)
    for invalid in [
        "bad",
        '{"001":"carrier@example.test"}',
        '{"12":"a@example.com,b@example.com"}',
    ]:
        with pytest.raises(SettingsError, match="OTP_CONTACTS_JSON") as caught:
            load_settings(ENV | {"OTP_CONTACTS_JSON": invalid})
        assert invalid not in str(caught.value)
