import os
import unittest
from unittest.mock import MagicMock, patch

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.auth.email import (
    EmailDeliveryError,
    deliver_email_verification_email,
    send_email_verification_email,
)
from app.core.config import settings


class EmailDeliveryTests(unittest.TestCase):
    def test_sends_frontend_verification_url_over_smtp(self) -> None:
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
        smtp = MagicMock()
        smtp.__enter__.return_value = smtp

        try:
            with patch("app.auth.email.smtplib.SMTP", return_value=smtp):
                send_email_verification_email("user@example.com", "a token")
        finally:
            for name, value in original.items():
                setattr(settings, name, value)

        smtp.starttls.assert_called_once()
        smtp.login.assert_called_once_with("sender@example.com", "password")
        message = smtp.send_message.call_args.args[0]
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

    def test_background_delivery_logs_smtp_failure_without_token(self) -> None:
        with (
            patch(
                "app.auth.email.send_email_verification_email",
                side_effect=EmailDeliveryError("SMTP unavailable"),
            ),
            self.assertLogs("app.auth.email", level="ERROR") as logs,
        ):
            deliver_email_verification_email("user@example.com", "secret-token")

        self.assertIn("Email verification delivery failed", logs.output[0])
        self.assertNotIn("secret-token", "\n".join(logs.output))


if __name__ == "__main__":
    unittest.main()
