"""The code email goes only to the configured inbox, and a failure never shows the password."""

import asyncio
import smtplib
from dataclasses import replace
from email.message import EmailMessage
from typing import Any, ClassVar

import pytest

from service.adapters.email import SUBJECT, CodeMailer, EmailFailed, EmailSettings

SETTINGS = EmailSettings(
    user="sender@example.test", credential="app-password", inbox="inbox@example.test"
)


class FakeSmtp:
    sent: ClassVar[list[EmailMessage]] = []
    logins: ClassVar[list[tuple[str, str]]] = []
    fail_with: ClassVar[Exception | None] = None

    def __init__(self, host: str, port: int, **options: Any) -> None:
        self.address = (host, port, options["timeout"])

    def __enter__(self) -> "FakeSmtp":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def login(self, user: str, credential: str) -> None:
        if FakeSmtp.fail_with:
            raise FakeSmtp.fail_with
        FakeSmtp.logins.append((user, credential))

    def send_message(self, message: EmailMessage) -> None:
        FakeSmtp.sent.append(message)


@pytest.fixture(autouse=True)
def _reset() -> None:
    FakeSmtp.sent, FakeSmtp.logins, FakeSmtp.fail_with = [], [], None


def test_the_code_goes_to_the_configured_inbox_only() -> None:
    asyncio.run(CodeMailer(SETTINGS, FakeSmtp).send("123456", "138328"))
    message = FakeSmtp.sent[0]
    assert (message["To"], message["From"], message["Subject"]) == (
        "inbox@example.test",
        "sender@example.test",
        SUBJECT,
    )
    assert "123456" in message.get_content()
    assert "123456" not in message["Subject"]
    assert FakeSmtp.logins == [("sender@example.test", "app-password")]


@pytest.mark.parametrize(
    "error",
    [
        smtplib.SMTPAuthenticationError(535, b"bad credentials app-password"),
        TimeoutError(),
        OSError(),
    ],
)
def test_a_failed_send_is_reported_without_the_password(error: Exception) -> None:
    FakeSmtp.fail_with = error
    with pytest.raises(EmailFailed) as caught:
        asyncio.run(CodeMailer(SETTINGS, FakeSmtp).send("123456", "138328"))
    assert "app-password" not in str(caught.value)
    assert "app-password" not in repr(SETTINGS)


def test_carrier_specific_roster_does_not_fall_back_to_demo_inbox() -> None:
    mail = CodeMailer(replace(SETTINGS, contacts={"138328": "approved@example.test"}), FakeSmtp)
    asyncio.run(mail.send("432100", "138328"))
    with pytest.raises(EmailFailed):
        asyncio.run(mail.send("432101", "138329"))
    assert [msg["To"] for msg in FakeSmtp.sent] == ["approved@example.test"]
