import os
import unittest
from unittest.mock import patch

from sqlalchemy.exc import IntegrityError

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.auth.schemas import SignUpRequest
from app.auth.security import verify_password
from app.auth.service import EmailAlreadyRegisteredError, create_user


class FakeSession:
    def __init__(self) -> None:
        self.added = []
        self.commit_calls = 0
        self.rollback_calls = 0

    def add(self, user) -> None:
        self.added.append(user)

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1


class FailingSession(FakeSession):
    def __init__(self, error: IntegrityError) -> None:
        super().__init__()
        self.error = error

    def commit(self) -> None:
        super().commit()
        raise self.error


class AuthServiceTests(unittest.TestCase):
    @patch("app.auth.service.logger")
    def test_create_user_hashes_password_and_persists_user(self, logger) -> None:
        db = FakeSession()
        request = SignUpRequest(
            email="User@Example.com",
            nickname="철학탐험가",
            password="password123!",
        )

        user = create_user(db, request)

        self.assertEqual(db.added, [user])
        self.assertEqual(db.commit_calls, 1)
        self.assertEqual(user.email, "user@example.com")
        self.assertEqual(user.nickname, request.nickname)
        self.assertLessEqual(len(user.password_hash), 255)
        self.assertTrue(verify_password(request.password, user.password_hash))
        logger.info.assert_called_once_with("회원가입에 성공했습니다.")

    def test_create_user_maps_only_active_email_constraint_to_duplicate_error(
        self,
    ) -> None:
        db = FailingSession(
            IntegrityError(
                None,
                None,
                Exception("Duplicate entry for key 'uq_users_email_active_marker'"),
            )
        )
        request = SignUpRequest(
            email="user@example.com",
            nickname="철학탐험가",
            password="password123!",
        )

        with self.assertRaisesRegex(
            EmailAlreadyRegisteredError, "이미 등록된 이메일 주소입니다."
        ):
            create_user(db, request)

        self.assertEqual(db.rollback_calls, 1)

    def test_create_user_reraises_other_integrity_errors(self) -> None:
        error = IntegrityError(None, None, Exception("Column 'role' cannot be null"))
        db = FailingSession(error)
        request = SignUpRequest(
            email="user@example.com",
            nickname="철학탐험가",
            password="password123!",
        )

        with self.assertRaises(IntegrityError) as raised:
            create_user(db, request)

        self.assertIs(raised.exception, error)
        self.assertEqual(db.rollback_calls, 1)


if __name__ == "__main__":
    unittest.main()
