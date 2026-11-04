"""The code email, sent over Gmail SMTP to the one configured demo inbox (D-3, D-12).

The destination comes from configuration, never from the conversation. The code goes
only into the email body, so it never enters a HappyRobot run.
"""

import asyncio
import smtplib
import ssl
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Any

SUBJECT = "HappyRobot Logistics verification code"


class EmailFailed(Exception):
    """The email may or may not have gone. The send still counts against the limit."""


class NoTrustedContact(EmailFailed):
    """No independently enrolled recipient exists for this MC."""


class DeliveryLimited(EmailFailed):
    """This process protected the inbox before calling the SMTP server."""


@dataclass(frozen=True, kw_only=True)
class EmailSettings:
    user: str
    credential: str = field(repr=False)
    inbox: str = field(repr=False)
    contacts: dict[str, str] | None = field(default=None, repr=False)
    host: str = "smtp.gmail.com"
    port: int = 465
    timeout_seconds: float = 5.0


class CodeMailer:
    def __init__(
        self,
        settings: EmailSettings,
        smtp: Callable[..., Any] = smtplib.SMTP_SSL,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.settings = settings
        self._smtp, self._clock = smtp, clock
        self._recent: defaultdict[str, deque[float]] = defaultdict(deque)

    async def send(self, code: str, mc: str) -> None:
        contacts = self.settings.contacts
        recipient = self.settings.inbox if contacts is None else contacts.get(mc)
        if not recipient:
            raise NoTrustedContact("No trusted recipient for this carrier.")
        self._admit(recipient.casefold())
        await asyncio.to_thread(self._send, code, recipient)

    def _admit(self, recipient: str) -> None:
        # One service process. No await before admission, and failed SMTP sends still count.
        now = self._clock()
        windows = ((self._recent[recipient], 4), (self._recent[""], 100))
        for window, limit in windows:
            while window and window[0] <= now - 600:
                window.popleft()
            if len(window) >= limit:
                raise DeliveryLimited("Code delivery limit reached.")
        for window, _ in windows:
            window.append(now)

    def _send(self, code: str, recipient: str) -> None:
        settings = self.settings
        message = EmailMessage()
        message["From"] = settings.user
        message["To"] = recipient
        message["Subject"] = SUBJECT
        message.set_content(f"Your verification code is {code}. It expires in five minutes.")
        try:
            with self._smtp(
                settings.host,
                settings.port,
                timeout=settings.timeout_seconds,
                context=ssl.create_default_context(),
            ) as server:
                server.login(settings.user, settings.credential)
                server.send_message(message)
        except (OSError, smtplib.SMTPException):
            raise EmailFailed("The code email could not be sent.") from None
