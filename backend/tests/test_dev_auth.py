import os
import subprocess
import sys
import unittest
from datetime import UTC, datetime, timedelta
from uuid import uuid4

os.environ["APP_ENV"] = "local"
os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.auth.models.refresh_token import RefreshToken
from app.auth.models.user import User
from app.auth.security import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    verify_refresh_token_hash,
)
from app.dev.router import DEV_USER_EMAIL, issue_dev_access_token
from jwt.exceptions import InvalidTokenError
from starlette.responses import Response


class FakeSession:
    def __init__(self) -> None:
        self.user = None
        self.refresh_tokens = []
        self.user_add_calls = 0
        self.commit_calls = 0

    def scalar(self, _statement):
        return self.user

    def add(self, instance) -> None:
        if isinstance(instance, User):
            self.user_add_calls += 1
            self.user = instance
        elif isinstance(instance, RefreshToken):
            self.refresh_tokens.append(instance)

    def commit(self) -> None:
        self.commit_calls += 1

    def refresh(self, _user) -> None:
        pass


class DevAuthTests(unittest.TestCase):
    def test_sets_login_compatible_token_cookies_and_reuses_dev_user(self) -> None:
        db = FakeSession()
        first_response = Response(status_code=204)

        issue_dev_access_token(first_response, db)
        issue_dev_access_token(Response(status_code=204), db)

        self.assertEqual(db.user_add_calls, 1)
        self.assertEqual(len(db.refresh_tokens), 2)
        self.assertEqual(db.user.email, DEV_USER_EMAIL)
        self.assertIsNotNone(db.user.email_verified_at)
        self.assertEqual(first_response.status_code, 204)
        self.assertEqual(first_response.body, b"")

        cookies = {
            header.partition(b"=")[0].decode(): header.decode()
            for name, header in first_response.raw_headers
            if name == b"set-cookie"
        }
        self.assertEqual(cookies.keys(), {"accessToken", "refreshToken"})
        self.assertIn("HttpOnly", cookies["accessToken"])
        self.assertIn("Secure", cookies["accessToken"])
        self.assertIn("SameSite=lax", cookies["accessToken"])
        self.assertIn("Path=/api;", cookies["accessToken"])
        self.assertIn("HttpOnly", cookies["refreshToken"])
        self.assertIn("Secure", cookies["refreshToken"])
        self.assertIn("SameSite=lax", cookies["refreshToken"])
        self.assertIn("Path=/api/auth", cookies["refreshToken"])

        access_token = cookies["accessToken"].split(";", 1)[0].split("=", 1)[1]
        refresh_token = cookies["refreshToken"].split(";", 1)[0].split("=", 1)[1]
        stored_refresh_token = db.refresh_tokens[0]
        self.assertEqual(stored_refresh_token.user_id, db.user.user_id)
        self.assertFalse(stored_refresh_token.is_revoked)
        self.assertTrue(
            verify_refresh_token_hash(refresh_token, stored_refresh_token.token_hash)
        )
        payload = verify_access_token(access_token)
        self.assertEqual(payload["sub"], str(db.user.user_id))
        self.assertEqual(payload["type"], "access")
        self.assertIn("exp", payload)
        expires_at = datetime.fromtimestamp(payload["exp"], UTC)
        self.assertLessEqual(
            abs(expires_at - (datetime.now(UTC) + timedelta(days=7))),
            timedelta(seconds=2),
        )
        self.assertEqual(
            verify_refresh_token(refresh_token)["sub"], str(db.user.user_id)
        )
        refresh_payload = verify_refresh_token(refresh_token)
        self.assertEqual(refresh_payload["sub"], str(db.user.user_id))
        self.assertEqual(refresh_payload["jti"], str(stored_refresh_token.token_id))

    def test_validates_token_types(self) -> None:
        user_id = uuid4()
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        with self.assertRaisesRegex(
            InvalidTokenError, "토큰 유형이 올바르지 않습니다."
        ):
            verify_access_token(refresh_token)

        with self.assertRaisesRegex(
            InvalidTokenError, "토큰 유형이 올바르지 않습니다."
        ):
            verify_refresh_token(access_token)

        payload = verify_refresh_token(refresh_token)
        self.assertEqual(payload["sub"], str(user_id))
        self.assertEqual(payload["type"], "refresh")

    def test_route_is_not_registered_in_production(self) -> None:
        environment = os.environ.copy()
        environment["APP_ENV"] = "production"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from app.main import app; "
                "assert '/api/dev/auth' not in app.openapi()['paths']",
            ],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
