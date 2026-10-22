import os
import unittest
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

import jwt
from app.auth.dependencies import (
    get_current_user,
    get_optional_refresh_token,
    get_required_refresh_token,
)
from app.auth.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.core.config import settings
from fastapi import HTTPException
from jwt.exceptions import InvalidTokenError


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
        access_token = create_access_token(uuid4())

        self.assertIs(get_current_user(db, access_token), user)
        self.assertEqual(db.scalar_calls, 1)

    def test_rejects_missing_or_invalid_token(self) -> None:
        for access_token in (
            None,
            "not-a-token",
            create_refresh_token(uuid4()),
        ):
            with self.assertRaises(HTTPException) as error:
                get_current_user(FakeSession(), access_token)

            self.assertEqual(error.exception.status_code, 401)
            self.assertIsNone(error.exception.headers)

    def test_rejects_when_token_user_does_not_exist(self) -> None:
        access_token = create_access_token(uuid4())

        with self.assertRaises(HTTPException) as error:
            get_current_user(FakeSession(), access_token)

        self.assertEqual(error.exception.status_code, 401)


class RefreshTokenDependencyTests(unittest.TestCase):
    def test_returns_verified_original_refresh_token(self) -> None:
        refresh_token = create_refresh_token(uuid4())

        verified_refresh_token = get_optional_refresh_token(refresh_token)
        payload, original_token = get_required_refresh_token(verified_refresh_token)

        self.assertEqual(original_token, refresh_token)
        self.assertEqual(payload, verify_refresh_token(refresh_token))

    def test_rejects_missing_or_invalid_refresh_token(self) -> None:
        for refresh_token in (
            None,
            "not-a-token",
            create_access_token(uuid4()),
            create_refresh_token(uuid4(), expires_delta=timedelta(seconds=-1)),
        ):
            with (
                self.subTest(refresh_token=refresh_token),
                self.assertRaises(HTTPException) as error,
            ):
                get_required_refresh_token(get_optional_refresh_token(refresh_token))

            self.assertEqual(error.exception.status_code, 401)

    def test_optional_token_returns_none_for_missing_or_invalid_token(self) -> None:
        for refresh_token in (
            None,
            "not-a-token",
            create_access_token(uuid4()),
            create_refresh_token(uuid4(), expires_delta=timedelta(seconds=-1)),
        ):
            with self.subTest(refresh_token=refresh_token):
                self.assertIsNone(get_optional_refresh_token(refresh_token))

    def test_optional_token_returns_verified_original_refresh_token(self) -> None:
        refresh_token = create_refresh_token(uuid4())

        payload, original_token = get_optional_refresh_token(refresh_token)

        self.assertEqual(original_token, refresh_token)
        self.assertEqual(payload, verify_refresh_token(refresh_token))

    def test_refresh_token_is_verified_only_once_across_dependencies(self) -> None:
        refresh_token = create_refresh_token(uuid4())

        with patch(
            "app.auth.dependencies.verify_refresh_token",
            wraps=verify_refresh_token,
        ) as verify:
            verified_refresh_token = get_optional_refresh_token(refresh_token)
            result = get_required_refresh_token(verified_refresh_token)

        self.assertEqual(result, verified_refresh_token)
        verify.assert_called_once_with(refresh_token)

    def test_refresh_token_requires_all_claims(self) -> None:
        refresh_token = create_refresh_token(uuid4())
        payload = jwt.decode(
            refresh_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        for claim in ("sub", "iat", "exp", "type", "jti"):
            invalid_payload = payload.copy()
            invalid_payload.pop(claim)
            invalid_token = jwt.encode(
                invalid_payload,
                settings.jwt_secret_key,
                algorithm=settings.jwt_algorithm,
            )

            with (
                self.subTest(claim=claim),
                self.assertRaises(InvalidTokenError),
            ):
                verify_refresh_token(invalid_token)

    def test_refresh_token_rejects_invalid_identifier_claims(self) -> None:
        refresh_token = create_refresh_token(uuid4())
        payload = jwt.decode(
            refresh_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        for claim in ("sub", "jti"):
            invalid_payload = payload | {claim: "not-a-uuid"}
            invalid_token = jwt.encode(
                invalid_payload,
                settings.jwt_secret_key,
                algorithm=settings.jwt_algorithm,
            )

            with (
                self.subTest(claim=claim),
                self.assertRaises(InvalidTokenError),
            ):
                verify_refresh_token(invalid_token)


if __name__ == "__main__":
    unittest.main()
