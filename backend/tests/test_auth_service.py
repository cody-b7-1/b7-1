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
from app.auth.security import (
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_access_token,
    verify_password,
    verify_refresh_token,
    verify_refresh_token_hash,
)
from app.auth.service import (
    EmailAlreadyRegisteredError,
    EmailNotFoundError,
    EmailNotVerifiedError,
    InvalidEmailVerificationTokenError,
    InvalidRefreshTokenError,
    PasswordMismatchError,
    authenticate_user,
    create_user,
    issue_refresh_token,
    login_user,
    revoke_refresh_token,
    rotate_refresh_token,
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

    @patch("app.auth.service.logger")
    def test_verify_email_logs_success_without_sensitive_data(self, logger) -> None:
        user = self._login_user(verified=False)
        verification = Mock(
            verification_id=uuid4(),
            user_id=user.user_id,
        )
        db = Mock()
        db.scalar.side_effect = [verification, user, verification]

        verify_email_verification_token(db, "secret-verification-token")

        logger.info.assert_called_once_with("이메일 인증이 완료되었습니다.")
        logger.warning.assert_not_called()

    @patch("app.auth.service.logger")
    def test_verify_email_logs_invalid_token_without_sensitive_data(self, logger) -> None:
        db = Mock()
        db.scalar.return_value = None

        with self.assertRaises(InvalidEmailVerificationTokenError):
            verify_email_verification_token(db, "secret-verification-token")

        db.rollback.assert_called_once_with()
        logger.warning.assert_called_once_with(
            "유효하지 않거나 만료된 이메일 인증 토큰으로 인증을 시도했습니다."
        )
        logger.info.assert_not_called()

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
            patch("app.auth.service.logger") as logger,
        ):
            tokens = login_user(db, request)

        self.assertEqual(tokens, ("access-token", "refresh-token"))
        authenticate.assert_called_once_with(db, request)
        issue.assert_called_once_with(db, user)
        access.assert_called_once_with(user.user_id)
        logger.info.assert_called_once_with("로그인에 성공했습니다.")

    def test_rotate_refresh_token_atomically_replaces_stored_token(self) -> None:
        user = self._login_user()
        old_token = create_refresh_token(user.user_id)
        payload = verify_refresh_token(old_token)
        db = Mock()
        db.execute.return_value.rowcount = 1

        access_token, new_token = rotate_refresh_token(db, payload, old_token)

        self.assertNotEqual(new_token, old_token)
        self.assertEqual(verify_access_token(access_token)["sub"], payload["sub"])
        new_payload = verify_refresh_token(new_token)
        self.assertEqual(new_payload["sub"], payload["sub"])
        db.execute.assert_called_once()
        db.add.assert_called_once()
        saved_token = db.add.call_args.args[0]
        self.assertEqual(str(saved_token.token_id), new_payload["jti"])
        self.assertEqual(saved_token.token_hash, hash_refresh_token(new_token))
        db.commit.assert_called_once_with()

    def test_rotate_refresh_token_rejects_missing_or_concurrently_used_token(
        self,
    ) -> None:
        user = self._login_user()
        old_token = create_refresh_token(user.user_id)
        db = Mock()
        db.execute.return_value.rowcount = 0

        with self.assertRaises(InvalidRefreshTokenError):
            rotate_refresh_token(db, verify_refresh_token(old_token), old_token)

        db.rollback.assert_called_once_with()
        db.add.assert_not_called()
        db.commit.assert_not_called()

    @patch("app.auth.service.logger")
    def test_authenticate_user_rejects_unverified_account_separately(
        self, logger
    ) -> None:
        db = Mock()
        db.scalar.return_value = self._login_user(verified=False)
        request = LoginRequest(email="user@example.com", password="password123!")

        with self.assertRaises(EmailNotVerifiedError):
            authenticate_user(db, request)

        logger.debug.assert_called_once_with(
            "이메일 인증이 완료되지 않아 로그인에 실패했습니다."
        )
        logger.warning.assert_not_called()

    @patch("app.auth.service.logger")
    def test_authenticate_user_rejects_nonexistent_email(self, logger) -> None:
        db = Mock()
        db.scalar.return_value = None
        request = LoginRequest(email="missing@example.com", password="password123!")

        with self.assertRaises(EmailNotFoundError):
            authenticate_user(db, request)

        logger.warning.assert_called_once_with("로그인 인증에 실패했습니다.")
        logger.debug.assert_not_called()

    @patch("app.auth.service.logger")
    def test_authenticate_user_rejects_mismatched_password(self, logger) -> None:
        db = Mock()
        db.scalar.return_value = self._login_user()
        request = LoginRequest(email="user@example.com", password="incorrect-password!")

        with self.assertRaises(PasswordMismatchError):
            authenticate_user(db, request)

        logger.warning.assert_called_once_with("로그인 인증에 실패했습니다.")
        logger.debug.assert_not_called()


if __name__ == "__main__":
    unittest.main()
