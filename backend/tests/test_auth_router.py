import os
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException, Response

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.auth.router import login
from app.auth.schemas import LoginRequest
from app.auth.security import (
    create_refresh_token,
    verify_refresh_token,
)
from app.auth.service import EmailNotFoundError, PasswordMismatchError


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
        access_cookie = next(cookie for cookie in cookies if cookie.startswith("accessToken="))
        refresh_cookie = next(cookie for cookie in cookies if cookie.startswith("refreshToken="))
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
            with self.subTest(error=type(error).__name__), patch(
                "app.auth.router.login_user", side_effect=error
            ):
                with self.assertRaises(HTTPException) as raised:
                    login(request, Response(), Mock())

            self.assertEqual(raised.exception.status_code, 401)
            self.assertEqual(
                raised.exception.detail,
                "이메일 주소 또는 비밀번호가 일치하지 않습니다.",
            )


if __name__ == "__main__":
    unittest.main()
