"""The app builds from settings, refuses to start without them, and keeps httpx quiet."""

import logging

import pytest
from fastapi.testclient import TestClient

from service.config import SettingsError, load_settings
from service.main import build, create
from service.tests.test_config import ENV


def test_the_app_builds_from_valid_settings_and_needs_keys() -> None:
    with TestClient(build(load_settings(ENV))) as client:
        assert client.post("/otp/send", json={}).status_code == 401
        headers = {"Authorization": f"Bearer {ENV['AGENT_API_KEY']}"}
        assert client.post("/otp/send", json={}, headers=headers).status_code == 400


def test_the_service_will_not_start_without_its_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ENV:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(SettingsError):
        create()


def test_request_urls_are_never_logged_because_fmcsas_carries_its_key() -> None:
    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING
