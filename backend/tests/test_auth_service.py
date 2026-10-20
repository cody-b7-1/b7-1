import os
import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.auth.models.refresh_token import RefreshToken
from app.auth.models.user import Role, User
from app.auth.schemas import LoginRequest, SignUpRequest
from app.auth.security import (
    hash_password,
    hash_refresh_token,
    verify_password,
    verify_refresh_token,
    verify_refresh_token_hash,
)
from app.auth.service import (
    EmailAlreadyRegisteredError,
    EmailNotFoundError,
    EmailNotVerifiedError,
    InvalidEmailVerificationTokenError,
    PasswordMismatchError,
    authenticate_user,
    create_email_verification,
    create_user,
    issue_refresh_token,
    login_user,
    revoke_refresh_token,
    verify_email_verification_token,
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
        self.assertEqual(saved_token.token_hash, hash_refresh_token(refresh_token))
        self.assertEqual(len(saved_token.token_hash), 64)
        self.assertTrue(
            verify_refresh_token_hash(refresh_token, saved_token.token_hash)
        )

    def test_revoke_refresh_token_marks_matching_sha256_record_revoked(self) -> None:
        refresh_token = "refresh-token"
        stored_token = RefreshToken(
            token_id=uuid4(),
            user_id=uuid4(),
            token_hash=hash_refresh_token(refresh_token),
            expires_at=datetime.now(UTC).replace(tzinfo=None),
        )
        db = Mock()
        db.scalar.return_value = stored_token

        revoke_refresh_token(db, refresh_token)

        self.assertTrue(stored_token.is_revoked)
        db.commit.assert_called_once_with()

    def test_revoke_refresh_token_ignores_missing_record(self) -> None:
        db = Mock()
        db.scalar.return_value = None

        revoke_refresh_token(db, "unknown-refresh-token")

        db.commit.assert_not_called()

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

    def test_reissue_replaces_the_previous_verification_token(self) -> None:
        db = Mock()
        user = self._login_user(verified=False)
        verification = SimpleNamespace(
            token_hash=hash_password("old-token"),
            expires_at=datetime.now(UTC).replace(tzinfo=None),
        )
        # First scalar call locks the user, second loads its 1:1 verification row.
        db.scalar.side_effect = [user, verification]

        token = create_email_verification(db, user)

        self.assertFalse(verify_password("old-token", verification.token_hash))
        self.assertTrue(verify_password(token, verification.token_hash))
        self.assertGreater(
            verification.expires_at, datetime.now(UTC).replace(tzinfo=None)
        )
        db.commit.assert_called_once()

    def test_valid_verification_token_marks_user_and_consumes_record(self) -> None:
        db = Mock()
        token = "valid-token"
        user = SimpleNamespace(deleted_at=None, email_verified_at=None)
        verification = SimpleNamespace(
            token_hash=hash_password(token),
            user=user,
            expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1),
        )
        db.scalars.return_value.all.return_value = [verification]

        verify_email_verification_token(db, token)

        self.assertIsNotNone(user.email_verified_at)
        db.delete.assert_called_once_with(verification)
        db.commit.assert_called_once()

    def test_expired_or_invalid_verification_token_is_rejected(self) -> None:
        db = Mock()
        expired_token = "expired-token"
        expired_verification = SimpleNamespace(
            token_hash=hash_password(expired_token),
            user=SimpleNamespace(deleted_at=None, email_verified_at=None),
            expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1),
        )
        # The query excludes expired records and the service defensively checks
        # expiry again before consuming a token.
        db.scalars.return_value.all.return_value = [expired_verification]

        with self.assertRaises(InvalidEmailVerificationTokenError):
            verify_email_verification_token(db, expired_token)

        db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
