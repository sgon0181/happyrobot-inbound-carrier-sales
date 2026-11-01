"""Verification email goes only to the private configured inbox."""

import asyncio
from email.message import EmailMessage
import smtplib
import ssl


class EmailNotifier:
    def __init__(self, values, platform=None):
        self.values = values

    async def __call__(self, code, run_id):
        def send():
            user = self.values.get("OTP_EMAIL_USER") or self.values["DEMO_OTP_EMAIL"]
            message = EmailMessage()
            message["From"] = user
            message["To"] = self.values["DEMO_OTP_EMAIL"]
            message["Subject"] = "HappyRobot Logistics verification code"
            message.set_content(
                "Your verification code is " + code + ". It expires in five minutes."
            )
            with smtplib.SMTP_SSL(
                "smtp.gmail.com", 465, timeout=5, context=ssl.create_default_context()
            ) as server:
                server.login(user, self.values["OTP_EMAIL_CREDENTIAL"])
                server.send_message(message)
            return {"sent": True, "source": "LIVE_SMTP"}

        return await asyncio.to_thread(send)
