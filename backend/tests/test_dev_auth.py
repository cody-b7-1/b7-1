import os
import subprocess
import sys
import unittest
from datetime import UTC, datetime, timedelta
from uuid import uuid4

os.environ["APP_ENV"] = "local"
os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from jwt.exceptions import InvalidTokenError

from app.auth.security import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
)
from app.dev.router import DEV_USER_EMAIL, issue_dev_access_token
from app.main import app


#Mock Session 
class FakeSession:
    def __init__(self) -> None:
        self.user = None
        self.add_calls = 0
        self.commit_calls = 0

    def scalar(self, _statement):
        return self.user

    def add(self, user) -> None:
        self.add_calls += 1
        self.user = user

    def commit(self) -> None:
        self.commit_calls += 1

    def refresh(self, _user) -> None:
        pass


class DevAuthTests(unittest.TestCase):

    def test_issues_expiring_token_and_reuses_dev_user(self) -> None:
        db = FakeSession()

        first = issue_dev_access_token(db)
        second = issue_dev_access_token(db)

        self.assertEqual(db.add_calls, 1)
        self.assertEqual(db.user.email, DEV_USER_EMAIL)
        self.assertTrue(db.user.is_active)
        self.assertIsNotNone(db.user.email_verified_at)
        self.assertEqual(first.user_id, second.user_id)
        self.assertEqual(first.token_type, "bearer")
        self.assertEqual(first.model_dump(by_alias=True).keys(), {"userId", "accessToken", "tokenType"})

        payload = verify_access_token(first.access_token)
        self.assertEqual(payload["sub"], first.user_id)
        self.assertEqual(payload["type"], "access")
        self.assertIn("exp", payload)
        expires_at = datetime.fromtimestamp(payload["exp"], UTC)
        self.assertLessEqual(
            abs(expires_at - (datetime.now(UTC) + timedelta(days=7))), timedelta(seconds=2)
        )

    def test_validates_token_types(self) -> None:
        user_id = uuid4()
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        with self.assertRaisesRegex(InvalidTokenError, "토큰 유형이 올바르지 않습니다."):
            verify_access_token(refresh_token)

        with self.assertRaisesRegex(InvalidTokenError, "토큰 유형이 올바르지 않습니다."):
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
