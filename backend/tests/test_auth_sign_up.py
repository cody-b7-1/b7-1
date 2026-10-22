import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import BackgroundTasks

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.auth.router import sign_up
from app.auth.schemas import SignUpRequest


class SignUpEndpointTests(unittest.TestCase):
    @patch("app.auth.router.create_user")
    def test_returns_created_users_email_and_nickname(self, create_user) -> None:
        request = SignUpRequest(
            email="User@Example.com",
            nickname="철학탐험가",
            password="password123!",
        )
        db = object()
        create_user.return_value = SimpleNamespace(
            email="user@example.com",
            nickname="철학탐험가",
        )
        background_tasks = BackgroundTasks()

        with patch(
            "app.auth.router.create_email_verification", return_value="token"
        ) as create_verification:
            response = sign_up(request, background_tasks, db)

        create_user.assert_called_once_with(db, request)
        create_verification.assert_called_once_with(db, create_user.return_value)
        self.assertEqual(
            response.model_dump(mode="json"),
            {"email": "user@example.com", "nickname": "철학탐험가"},
        )


if __name__ == "__main__":
    unittest.main()
