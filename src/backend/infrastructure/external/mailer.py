from __future__ import annotations

import smtplib
from email.message import EmailMessage

import anyio

from src.backend.dependencies.settings import Settings


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
        if not Settings.smtp_host:
            print(f"[mailer] to={email} subject={subject} body={body}")
            return
        await anyio.to_thread.run_sync(self._send_sync, email, subject, body)

    @staticmethod
    def _send_sync(email: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = Settings.smtp_from
        message["To"] = email
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(Settings.smtp_host, Settings.smtp_port, timeout=10) as smtp:
            if Settings.smtp_use_tls:
                smtp.starttls()
            if Settings.smtp_username and Settings.smtp_password:
                smtp.login(Settings.smtp_username, Settings.smtp_password)
            smtp.send_message(message)
