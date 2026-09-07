from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

import anyio

from src.config.settings import settings

logger = logging.getLogger(__name__)


class Mailer:
    async def send_verification_code(self, email: str, code: str) -> None:
        subject = "ImmersJP: подтверждение почты"
        body = (
            "Твой код подтверждения для ImmersJP: "
            f"{code}\n\n"
            "Если ты не создавал аккаунт, просто проигнорируй это письмо."
        )
        await self._send(email, subject, body)

    async def _send(self, email: str, subject: str, body: str) -> None:
        if not settings.smtp.smtp_host:
            logger.info("Mailer skipped (no SMTP host): to=%s subject=%s", email, subject)
            return
        await anyio.to_thread.run_sync(self._send_sync, email, subject, body)

    @staticmethod
    def _send_sync(email: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = settings.smtp.smtp_from
        message["To"] = email
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(settings.smtp.smtp_host, settings.smtp.smtp_port, timeout=10) as smtp:
            if settings.smtp.smtp_use_tls:
                smtp.starttls()
            if settings.smtp.smtp_username and settings.smtp.smtp_password:
                smtp.login(settings.smtp.smtp_username, settings.smtp.smtp_password)
            smtp.send_message(message)
