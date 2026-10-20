import os
import unittest
from datetime import UTC, datetime
from unittest.mock import Mock, patch
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.auth.models.refresh_token import RefreshToken
from app.auth.models.user import Role, User
from app.auth.schemas import LoginRequest, SignUpRequest
from app.auth.security import hash_password, verify_password, verify_refresh_token
from app.auth.service import (
    EmailAlreadyRegisteredError,
    EmailNotFoundError,
    EmailNotVerifiedError,
    PasswordMismatchError,
    authenticate_user,
    create_user,
    issue_refresh_token,
    login_user,
)


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
    def _login_user(self, *, verified: bool = True) -> User:
        return User(
            user_id=uuid4(),
            email="user@example.com",
            nickname="철학탐험가",
            password_hash=hash_password("password123!"),
            role=Role.USER,
            email_verified_at=datetime.now(UTC).replace(tzinfo=None)
            if verified
            else None,
        )

    def test_create_user_hashes_password_and_persists_user(self) -> None:
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

        with self.assertRaises(EmailAlreadyRegisteredError):
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

    def test_issue_refresh_token_adds_hashed_token_record_with_matching_jti(
        self,
    ) -> None:
        db = Mock()
        user = self._login_user()

        refresh_token = issue_refresh_token(db, user)

        payload = verify_refresh_token(refresh_token)
        db.add.assert_called_once()
        db.commit.assert_called_once()
        saved_token = db.add.call_args.args[0]
        self.assertIsInstance(saved_token, RefreshToken)
        self.assertEqual(str(saved_token.token_id), payload["jti"])
        self.assertEqual(saved_token.user_id, user.user_id)
        self.assertTrue(verify_password(refresh_token, saved_token.token_hash))

    def test_login_user_combines_authentication_and_token_issuance(self) -> None:
        db = Mock()
        user = self._login_user()
        request = LoginRequest(email="user@example.com", password="password123!")

        with (
            patch(
                "app.auth.service.authenticate_user", return_value=user
            ) as authenticate,
            patch(
                "app.auth.service.issue_refresh_token", return_value="refresh-token"
            ) as issue,
            patch(
                "app.auth.service.create_access_token", return_value="access-token"
            ) as access,
        ):
            tokens = login_user(db, request)

        self.assertEqual(tokens, ("access-token", "refresh-token"))
        authenticate.assert_called_once_with(db, request)
        issue.assert_called_once_with(db, user)
        access.assert_called_once_with(user.user_id)

    def test_authenticate_user_rejects_unverified_account_separately(self) -> None:
        db = Mock()
        db.scalar.return_value = self._login_user(verified=False)
        request = LoginRequest(email="user@example.com", password="password123!")

        with self.assertRaises(EmailNotVerifiedError):
            authenticate_user(db, request)

    def test_authenticate_user_rejects_nonexistent_email(self) -> None:
        db = Mock()
        db.scalar.return_value = None
        request = LoginRequest(email="missing@example.com", password="password123!")

        with self.assertRaises(EmailNotFoundError):
            authenticate_user(db, request)

    def test_authenticate_user_rejects_mismatched_password(self) -> None:
        db = Mock()
        db.scalar.return_value = self._login_user()
        request = LoginRequest(email="user@example.com", password="incorrect-password!")

        with self.assertRaises(PasswordMismatchError):
            authenticate_user(db, request)


if __name__ == "__main__":
    unittest.main()
