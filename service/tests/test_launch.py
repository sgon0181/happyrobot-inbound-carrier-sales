"""Deployment targets are explicit, readiness is authenticated, and review stays local."""

import json
import time
import urllib.request
from io import BytesIO
from pathlib import Path

import pytest

from tools import launch


def configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP", "isolated-review")
    monkeypatch.setenv("APP_URL", "https://proposal.happyrobot.dev/")
    monkeypatch.setenv("OPS_API_KEY", "fixture-operations-key")


def test_missing_or_untrusted_deploy_target_cannot_run_a_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []
    monkeypatch.setattr(launch, "run", lambda *args, **kwargs: calls.append(args))
    monkeypatch.delenv("APP", raising=False)
    with pytest.raises(SystemExit, match="explicit Fly target"):
        launch.deploy(secrets_only=False)
    configured(monkeypatch)
    for url in (
        "http://proposal.happyrobot.dev",
        "https://happyrobot.dev.attacker.test",
        "file:///tmp/a",
    ):
        monkeypatch.setenv("APP_URL", url)
        with pytest.raises(SystemExit, match="HTTPS HappyRobot App"):
            launch.deploy(secrets_only=False)
    assert not calls


def test_cloud_deploy_opens_only_after_successful_authenticated_readiness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured(monkeypatch)
    commands: list[tuple[str, ...]] = []
    checks: list[tuple[str, str]] = []
    opened: list[str] = []
    monkeypatch.setattr(launch, "run", lambda *args, **kwargs: commands.append(args))

    def ready(app: str, key: str) -> bool:
        checks.append((app, key))
        return True

    monkeypatch.setattr(launch, "ready", ready)
    monkeypatch.setattr(launch, "open_app", opened.append)
    launch.deploy(secrets_only=False)
    assert commands == [
        (
            "fly",
            "deploy",
            "--config",
            str(launch.ROOT / "fly.toml"),
            "--app",
            "isolated-review",
            "--ha=false",
        )
    ]
    assert checks == [("isolated-review", "fixture-operations-key")]
    assert opened == ["https://proposal.happyrobot.dev/"]


def test_failed_readiness_never_opens_the_app(monkeypatch: pytest.MonkeyPatch) -> None:
    configured(monkeypatch)
    opened: list[str] = []
    monkeypatch.setattr(launch, "run", lambda *args, **kwargs: None)
    monkeypatch.setattr(launch, "ready", lambda *args: False)
    monkeypatch.setattr(time, "sleep", lambda seconds: None)
    monkeypatch.setattr(launch, "open_app", opened.append)
    with pytest.raises(SystemExit, match="readiness failed"):
        launch.deploy(secrets_only=False)
    assert opened == []


def test_settings_are_literals_and_only_service_keys_are_imported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(launch, "ROOT", tmp_path)
    (tmp_path / ".env").write_text(
        "OTP_CONTACTS_JSON='{\"138328\":\"dispatch@example.invalid\"}'\nNOT_SERVICE=secret\nOPS_API_KEY='$(never-execute)'\n"
    )
    monkeypatch.delenv("OPS_API_KEY", raising=False)
    actual = launch.settings()
    assert actual["OPS_API_KEY"] == "$(never-execute)"
    assert actual["OTP_CONTACTS_JSON"] == '{"138328":"dispatch@example.invalid"}'
    assert "NOT_SERVICE" not in actual


def test_local_launcher_uses_compose_readiness_without_cloud_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []
    opened: list[str] = []
    monkeypatch.setattr(launch, "run", lambda *args, **kwargs: calls.append(args))
    monkeypatch.setattr(launch, "open_app", opened.append)
    launch.local(stop=False)
    assert calls[0][-3:] == ("--build", "--force-recreate", "--wait")
    assert calls[0][0] == "docker"
    assert opened == ["http://127.0.0.1:3081/enter/rep"]
    launch.local(stop=True)
    assert calls[-1][-2:] == ("down", "--volumes")


@pytest.mark.parametrize(
    "tms,expected", [("reachable", True), ("unreachable", False), (None, False)]
)
def test_readiness_requires_authenticated_service_and_tms_reachability(
    monkeypatch: pytest.MonkeyPatch, tms: str | None, expected: bool
) -> None:
    def response(request: urllib.request.Request, timeout: int) -> BytesIO:
        assert request.full_url == "https://isolated-review.fly.dev/health"
        assert request.get_header("Authorization") == "Bearer fixture-key"
        assert timeout == 5
        return BytesIO(json.dumps({"status": "ok", "tms": tms}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", response)
    assert launch.ready("isolated-review", "fixture-key") is expected
