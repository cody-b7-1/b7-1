import os
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import BackgroundTasks, HTTPException, Response

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.auth.router import (
    login,
    send_email_verification_link,
    sign_up,
    verify_email_link_token,
)
from app.auth.schemas import (
    EmailSendRequest,
    EmailVerifyRequest,
    LoginRequest,
    SignUpRequest,
)
from app.auth.security import (
    create_refresh_token,
    verify_refresh_token,
)
from app.auth.service import (
    EmailNotFoundError,
    InvalidEmailVerificationTokenError,
    PasswordMismatchError,
)


class AuthRouterTests(unittest.TestCase):
    def test_login_sets_access_and_refresh_token_cookies(self) -> None:
        user_id = uuid4()
        response = Response()
        db = Mock()
        refresh_token = create_refresh_token(user_id)

        with (
            patch(
                "app.auth.router.login_user",
                return_value=("access-token", refresh_token),
            ) as login_service,
        ):
            result = login(
                LoginRequest(email="user@example.com", password="password123!"),
                response,
                db,
            )

        self.assertIsNone(result)

        cookies = response.headers.getlist("set-cookie")
        self.assertEqual(len(cookies), 2)
        access_cookie = next(
            cookie for cookie in cookies if cookie.startswith("accessToken=")
        )
        refresh_cookie = next(
            cookie for cookie in cookies if cookie.startswith("refreshToken=")
        )
        self.assertEqual(access_cookie.split(";", 1)[0], "accessToken=access-token")
        cookie_refresh_token = refresh_cookie.split(";", 1)[0].split("=", 1)[1]
        refresh_payload = verify_refresh_token(cookie_refresh_token)
        self.assertEqual(refresh_payload["sub"], str(user_id))
        for cookie in (access_cookie, refresh_cookie):
            self.assertIn("HttpOnly", cookie)
            self.assertIn("Secure", cookie)
            self.assertIn("SameSite=lax", cookie)
        self.assertIn("Path=/api", access_cookie)
        self.assertIn("Path=/api/auth", refresh_cookie)

        login_service.assert_called_once_with(
            db, LoginRequest(email="user@example.com", password="password123!")
        )
        self.assertEqual(db.mock_calls, [])

    def test_login_returns_same_401_for_invalid_login_information(self) -> None:
        request = LoginRequest(email="user@example.com", password="password123!")

        for error in (EmailNotFoundError(), PasswordMismatchError()):
            with (
                self.subTest(error=type(error).__name__),
                patch("app.auth.router.login_user", side_effect=error),
                self.assertRaises(HTTPException) as raised,
            ):
                login(request, Response(), Mock())

            self.assertEqual(raised.exception.status_code, 401)
            self.assertEqual(
                raised.exception.detail,
                "이메일 주소 또는 비밀번호가 일치하지 않습니다.",
            )

    def test_sign_up_creates_and_queues_email_verification_link(self) -> None:
        request = SignUpRequest(
            email="user@example.com", nickname="철학탐험가", password="password123!"
        )
        user = Mock(email="user@example.com")
        db = Mock()
        background_tasks = BackgroundTasks()

        with (
            patch("app.auth.router.create_user", return_value=user) as create,
            patch(
                "app.auth.router.create_email_verification", return_value="token"
            ) as issue,
        ):
            result = sign_up(request, background_tasks, db)

        self.assertIsNone(result)
        create.assert_called_once_with(db, request)
        issue.assert_called_once_with(db, user)
        self.assertEqual(len(background_tasks.tasks), 1)
        task = background_tasks.tasks[0]
        self.assertEqual(task.func.__name__, "deliver_email_verification_email")
        self.assertEqual(task.args, ("user@example.com", "token"))

    def test_email_resend_only_queues_for_unverified_user(self) -> None:
        request = EmailSendRequest(email="user@example.com")
        user = Mock(email="user@example.com")
        db = Mock()
        db.scalar.return_value = user
        background_tasks = BackgroundTasks()

        with patch(
            "app.auth.router.create_email_verification", return_value="new-token"
        ):
            result = send_email_verification_link(request, background_tasks, db)

        self.assertIsNone(result)
        self.assertEqual(len(background_tasks.tasks), 1)
        self.assertEqual(
            background_tasks.tasks[0].args, ("user@example.com", "new-token")
        )

        db.scalar.return_value = None
        no_account_tasks = BackgroundTasks()
        self.assertIsNone(send_email_verification_link(request, no_account_tasks, db))
        self.assertEqual(no_account_tasks.tasks, [])

    def test_verify_email_token_maps_invalid_token_to_bad_request(self) -> None:
        with (
            patch(
                "app.auth.router.verify_email_verification_token",
                side_effect=InvalidEmailVerificationTokenError,
            ),
            self.assertRaises(HTTPException) as raised,
        ):
            verify_email_link_token(EmailVerifyRequest(token="invalid-token"), Mock())

        self.assertEqual(raised.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
