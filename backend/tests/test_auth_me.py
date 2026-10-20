import os
import unittest
from types import SimpleNamespace

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.auth.router import get_me


class CurrentUserEndpointTests(unittest.TestCase):
    def test_returns_authenticated_users_email_and_nickname(self) -> None:
        user = SimpleNamespace(email="user@example.com", nickname="철학탐험가")

        response = get_me(user)

        self.assertEqual(
            response.model_dump(mode="json"),
            {"email": "user@example.com", "nickname": "철학탐험가"},
        )


if __name__ == "__main__":
    unittest.main()
