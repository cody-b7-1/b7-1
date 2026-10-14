import os
import subprocess
import sys
import unittest
from datetime import UTC, datetime, timedelta

os.environ["APP_ENV"] = "development"
os.environ["JWT_SECRET_KEY"] = "test-signing-key-with-at-least-32-bytes"

import jwt

from app.dev.router import TEST_USER_EMAIL, issue_test_access_token
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


class DevTestAuthTests(unittest.TestCase):
    def test_issues_expiring_token_and_reuses_test_user(self) -> None:
        db = FakeSession()

        first = issue_test_access_token(db)
        second = issue_test_access_token(db)

        self.assertEqual(db.add_calls, 1)
        self.assertEqual(db.user.email, TEST_USER_EMAIL)
        self.assertTrue(db.user.is_active)
        self.assertIsNotNone(db.user.email_verified_at)
        self.assertEqual(first.user_id, second.user_id)
        self.assertEqual(first.token_type, "bearer")
        self.assertEqual(first.model_dump(by_alias=True).keys(), {"userId", "accessToken", "tokenType"})

        payload = jwt.decode(
            first.access_token,
            "test-signing-key-with-at-least-32-bytes",
            algorithms=["HS256"],
        )
        self.assertEqual(payload["sub"], first.user_id)
        self.assertIn("exp", payload)
        expires_at = datetime.fromtimestamp(payload["exp"], UTC)
        self.assertLessEqual(
            abs(expires_at - (datetime.now(UTC) + timedelta(days=7))), timedelta(seconds=2)
        )

    def test_route_is_registered_in_local_development(self) -> None:
        operation = app.openapi()["paths"]["/dev/test-auth"]["post"]

        self.assertEqual(operation["responses"]["200"]["description"], "Successful Response")
        self.assertIn("500", operation["responses"])
        self.assertEqual(
            operation["responses"]["500"]["content"]["application/json"]["schema"]["$ref"],
            "#/components/schemas/TestAuthErrorResponse",
        )
        self.assertEqual(
            operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"],
            "#/components/schemas/TestAuthResponse",
        )

    def test_docs_and_openapi_endpoints_are_enabled(self) -> None:
        self.assertEqual(app.docs_url, "/docs")
        self.assertEqual(app.openapi_url, "/openapi.json")

    def test_route_is_not_registered_in_production(self) -> None:
        environment = os.environ.copy()
        environment["APP_ENV"] = "production"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from app.main import app; "
                "assert '/dev/test-auth' not in app.openapi()['paths']",
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
