import os
import unittest
from unittest.mock import AsyncMock, patch

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.auth.email import (
    EmailDeliveryError,
    deliver_email_verification_email,
    send_email_verification_email,
)
from app.core.config import settings


class EmailDeliveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_sends_frontend_verification_url_over_smtp(self) -> None:
        original = {
            "frontend_url": settings.frontend_url,
            "smtp_host": settings.smtp_host,
            "smtp_port": settings.smtp_port,
            "smtp_username": settings.smtp_username,
            "smtp_password": settings.smtp_password,
            "smtp_from_email": settings.smtp_from_email,
            "smtp_use_tls": settings.smtp_use_tls,
        }
        settings.frontend_url = "https://app.example.com/"
        settings.smtp_host = "smtp.example.com"
        settings.smtp_port = 587
        settings.smtp_username = "sender@example.com"
        settings.smtp_password = "password"
        settings.smtp_from_email = "Philo <sender@example.com>"
        settings.smtp_use_tls = True
        smtp_send = AsyncMock()

        try:
            with patch("app.auth.email.aiosmtplib.send", smtp_send):
                await send_email_verification_email("user@example.com", "a token")
        finally:
            for name, value in original.items():
                setattr(settings, name, value)

        smtp_send.assert_awaited_once()
        message = smtp_send.await_args.args[0]
        self.assertEqual(smtp_send.await_args.kwargs["hostname"], "smtp.example.com")
        self.assertEqual(smtp_send.await_args.kwargs["port"], 587)
        self.assertEqual(smtp_send.await_args.kwargs["username"], "sender@example.com")
        self.assertEqual(smtp_send.await_args.kwargs["password"], "password")
        self.assertTrue(smtp_send.await_args.kwargs["start_tls"])
        self.assertEqual(message["To"], "user@example.com")
        self.assertTrue(message.is_multipart())
        text_part, html_part = message.iter_parts()
        self.assertIn(
            "https://app.example.com/verify-email?token=a+token",
            text_part.get_content(),
        )
        self.assertEqual(text_part.get_content_type(), "text/plain")
        self.assertEqual(html_part.get_content_type(), "text/html")
        self.assertIn(
            'href="https://app.example.com/verify-email?token=a+token"',
            html_part.get_content(),
        )
        self.assertIn(
            ">https://app.example.com/verify-email?token=a+token</a>",
            html_part.get_content(),
        )

    async def test_delivery_logs_smtp_failure_without_token(self) -> None:
        with (
            patch(
                "app.auth.email.send_email_verification_email",
                new=AsyncMock(side_effect=EmailDeliveryError("SMTP unavailable")),
            ),
            self.assertLogs("app.auth.email", level="ERROR") as logs,
            self.assertRaises(EmailDeliveryError),
        ):
            await deliver_email_verification_email("user@example.com", "secret-token")

        output = "\n".join(logs.output)
        self.assertIn("이메일 인증 메일 SMTP 전송에 실패했습니다.", output)
        self.assertNotIn("user@example.com", output)
        self.assertNotIn("secret-token", output)
        self.assertNotIn("SMTP unavailable", output)

    async def test_delivery_logs_smtp_success_without_sensitive_data(self) -> None:
        with (
            patch(
                "app.auth.email.send_email_verification_email", new=AsyncMock()
            ),
            self.assertLogs("app.auth.email", level="INFO") as logs,
        ):
            await deliver_email_verification_email("user@example.com", "secret-token")

        output = "\n".join(logs.output)
        self.assertIn("이메일 인증 메일 SMTP 전송에 성공했습니다.", output)
        self.assertNotIn("user@example.com", output)
        self.assertNotIn("secret-token", output)


if __name__ == "__main__":
    unittest.main()
