"""SMTP delivery for email verification links."""

import logging
import smtplib
from email.message import EmailMessage
from html import escape
from urllib.parse import urlencode

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    """email 전송 실패 시"""


def validate_smtp_settings() -> None:
    if (
        not settings.smtp_host
        or not settings.smtp_username
        or not settings.smtp_password
    ):
        raise EmailDeliveryError("SMTP 설정이 완료되지 않았습니다.")


def send_email_verification_email(email: str, token: str) -> None:

    # email 전송
    validate_smtp_settings()
    verification_url = (
        f"{settings.frontend_url.rstrip('/')}/verify-email?"
        f"{urlencode({'token': token})}"
    )

    # 메시지 생성
    message = EmailMessage()
    message["Subject"] = "Philo 이메일 인증"
    message["From"] = settings.smtp_from_email or settings.smtp_username
    message["To"] = email
    message.set_content(
        "Philo 계정의 이메일 인증을 완료하려면 아래 링크를 열어 주세요.\n\n"
        f"{verification_url}\n\n"
        f"이 링크는 {settings.email_verification_expire_hours}시간 동안 유효합니다."
    )

    safe_url = escape(verification_url, quote=True)
    message.add_alternative(
        f"""
        <html>
          <body>
            <p>Philo 계정의 이메일 인증을 완료하려면 아래 링크를 열어 주세요.</p>
            <br>
            <p>
              <a href="{safe_url}">{safe_url}</a>
            </p>
            <br>
            <p>이 링크는 {settings.email_verification_expire_hours}시간 동안 유효합니다.</p>
          </body>
        </html>
        """,
        subtype="html",
    )

    # 전송
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        raise EmailDeliveryError("인증 이메일을 발송하지 못했습니다.") from error


def deliver_email_verification_email(email: str, token: str) -> None:
    """Deliver in a background task and log the outcome without credentials or tokens."""
    try:
        send_email_verification_email(email, token)
    except EmailDeliveryError:
        logger.exception("Email verification delivery failed")
    else:
        logger.info("Email verification delivery succeeded")
