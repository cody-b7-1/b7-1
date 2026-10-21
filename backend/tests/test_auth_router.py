import os
import unittest
from datetime import timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException, Response

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.auth.router import login, logout, refresh_access_token
from app.auth.router import router as auth_router
from app.auth.dependencies import (
    get_optional_refresh_token,
    get_required_refresh_token,
)
from app.auth.schemas import LoginRequest
from app.auth.security import create_refresh_token, verify_refresh_token
from app.auth.service import (
    EmailNotFoundError,
    InvalidRefreshTokenError,
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

    def test_logout_revokes_refresh_token_and_expires_cookies(self) -> None:
        response = Response()
        db = Mock()
        refresh_token = create_refresh_token(uuid4())
        payload = verify_refresh_token(refresh_token)

        with patch("app.auth.router.revoke_refresh_token") as revoke:
            result = logout(
                response=response,
                db=db,
                refresh_token=(payload, refresh_token),
            )

        self.assertIsNone(result)
        revoke.assert_called_once_with(db, refresh_token)
        cookies = response.headers.getlist("set-cookie")
        self.assertEqual(len(cookies), 2)
        self.assertTrue(any(cookie.startswith("accessToken=") for cookie in cookies))
        self.assertTrue(any(cookie.startswith("refreshToken=") for cookie in cookies))

    def test_refresh_rotates_tokens_and_sets_login_compatible_cookies(self) -> None:
        user_id = uuid4()
        original_token = create_refresh_token(user_id)
        payload = verify_refresh_token(original_token)
        response = Response()
        db = Mock()

        with patch(
            "app.auth.router.rotate_refresh_token",
            return_value=("new-access-token", "new-refresh-token"),
        ) as rotate:
            result = refresh_access_token(
                response=response,
                db=db,
                refresh_token=(payload, original_token),
            )

        self.assertIsNone(result)
        rotate.assert_called_once_with(db, payload, original_token)
        cookies = response.headers.getlist("set-cookie")
        self.assertEqual(len(cookies), 2)
        self.assertTrue(
            any(cookie.startswith("accessToken=new-access-token;") for cookie in cookies)
        )
        self.assertTrue(
            any(
                cookie.startswith("refreshToken=new-refresh-token;")
                for cookie in cookies
            )
        )
        for cookie in cookies:
            self.assertIn("HttpOnly", cookie)
            self.assertIn("Secure", cookie)
            self.assertIn("SameSite=lax", cookie)

    def test_refresh_returns_401_when_verified_token_is_not_valid_in_db(self) -> None:
        original_token = create_refresh_token(uuid4())
        payload = verify_refresh_token(original_token)

        with (
            patch(
                "app.auth.router.rotate_refresh_token",
                side_effect=InvalidRefreshTokenError,
            ),
            self.assertRaises(HTTPException) as raised,
        ):
            refresh_access_token(
                response=Response(),
                db=Mock(),
                refresh_token=(payload, original_token),
            )

        self.assertEqual(raised.exception.status_code, 401)

    def test_logout_without_refresh_token_still_expires_cookies(self) -> None:
        response = Response()

        with patch("app.auth.router.revoke_refresh_token") as revoke:
            logout(
                response=response,
                db=Mock(),
                refresh_token=None,
            )

        revoke.assert_not_called()
        self.assertEqual(len(response.headers.getlist("set-cookie")), 2)

    def test_logout_with_invalid_refresh_token_skips_db_revocation(self) -> None:
        response = Response()

        with patch("app.auth.router.revoke_refresh_token") as revoke:
            logout(
                response=response,
                db=Mock(),
                refresh_token=None,
            )

        revoke.assert_not_called()
        self.assertEqual(len(response.headers.getlist("set-cookie")), 2)

    def test_refresh_request_verifies_refresh_token_once(self) -> None:
        refresh_token = create_refresh_token(uuid4())
        db = Mock()
        response = Response()

        with (
            patch(
                "app.auth.dependencies.verify_refresh_token",
                wraps=verify_refresh_token,
            ) as verify,
            patch(
                "app.auth.router.rotate_refresh_token",
                return_value=("new-access-token", "new-refresh-token"),
            ) as rotate,
        ):
            verified_token = get_optional_refresh_token(refresh_token)
            required_token = get_required_refresh_token(verified_token)
            result = refresh_access_token(
                response=response,
                db=db,
                refresh_token=required_token,
            )

        self.assertIsNone(result)
        verify.assert_called_once_with(refresh_token)
        payload = verify_refresh_token(refresh_token)
        rotate.assert_called_once_with(db, payload, refresh_token)

    def test_logout_returns_204_for_missing_expired_or_tampered_token(self) -> None:
        valid_token = create_refresh_token(uuid4())
        tampered_token = valid_token.rsplit(".", 1)[0] + ".invalid-signature"
        tokens = (
            None,
            create_refresh_token(
                uuid4(), expires_delta=timedelta(seconds=-1)
            ),
            tampered_token,
        )

        for refresh_token in tokens:
            with (
                self.subTest(refresh_token=refresh_token),
                patch("app.auth.router.revoke_refresh_token") as revoke,
            ):
                response = Response()
                result = logout(
                    response=response,
                    db=Mock(),
                    refresh_token=get_optional_refresh_token(refresh_token),
                )

            self.assertIsNone(result)
            revoke.assert_not_called()
            self.assertEqual(len(response.headers.getlist("set-cookie")), 2)

        logout_route = next(
            route for route in auth_router.routes if route.path == "/auth/logout"
        )
        self.assertEqual(logout_route.status_code, 204)

    def test_refresh_returns_401_for_missing_expired_or_tampered_token(self) -> None:
        valid_token = create_refresh_token(uuid4())
        tampered_token = valid_token.rsplit(".", 1)[0] + ".invalid-signature"
        tokens = (
            None,
            create_refresh_token(
                uuid4(), expires_delta=timedelta(seconds=-1)
            ),
            tampered_token,
        )

        for refresh_token in tokens:
            with (
                self.subTest(refresh_token=refresh_token),
                patch("app.auth.router.rotate_refresh_token") as rotate,
                self.assertRaises(HTTPException) as raised,
            ):
                get_required_refresh_token(
                    get_optional_refresh_token(refresh_token)
                )

            self.assertEqual(raised.exception.status_code, 401)
            rotate.assert_not_called()

if __name__ == "__main__":
    unittest.main()
