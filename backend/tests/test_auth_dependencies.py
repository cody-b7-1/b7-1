import os
import unittest
from uuid import uuid4

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from fastapi import HTTPException

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, create_refresh_token


class FakeSession:
    def __init__(self, user=None) -> None:
        self.user = user
        self.scalar_calls = 0

    def scalar(self, _statement):
        self.scalar_calls += 1
        return self.user


class CurrentUserDependencyTests(unittest.TestCase):
    def test_returns_user_from_access_token_subject(self) -> None:
        user = object()
        db = FakeSession(user)
        credentials = create_access_token(uuid4())

        self.assertIs(get_current_user(credentials, db), user)
        self.assertEqual(db.scalar_calls, 1)

    def test_rejects_missing_or_invalid_token(self) -> None:
        for credentials in (
            None, #인증정보 x
            "not-a-token", #jwt 형식이 유효 x
            create_refresh_token(uuid4()), #refresh token을 access token에 전달
        ):
            with self.assertRaises(HTTPException) as error:
                get_current_user(credentials, FakeSession())

            self.assertEqual(error.exception.status_code, 401)
            self.assertIsNone(error.exception.headers)

    def test_rejects_when_token_user_does_not_exist(self) -> None:
        credentials = create_access_token(uuid4())

        with self.assertRaises(HTTPException) as error:
            get_current_user(credentials, FakeSession())

        self.assertEqual(error.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
