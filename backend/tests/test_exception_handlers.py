import asyncio
import json
import os
import unittest

from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.auth.schemas import SignUpRequest
from app.core.exceptions import (
    request_validation_error_handler,
    unhandled_exception_handler,
)
from app.main import app


class ExceptionHandlerTests(unittest.TestCase):
    def test_registers_global_unhandled_exception_handler(self) -> None:
        self.assertIs(app.exception_handlers[Exception], unhandled_exception_handler)
        self.assertIs(
            app.exception_handlers[RequestValidationError],
            request_validation_error_handler,
        )

    def test_returns_safe_internal_server_error_response(self) -> None:
        response = asyncio.run(
            unhandled_exception_handler(None, RuntimeError("database failure"))
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.body),
            {"detail": "서버 내부 오류가 발생했습니다."},
        )

    def test_returns_korean_message_for_invalid_email_format(self) -> None:
        error = RequestValidationError(
            [
                {
                    "type": "value_error",
                    "loc": ("body", "email"),
                    "msg": "invalid email",
                    "input": "not-an-email",
                }
            ]
        )

        response = asyncio.run(request_validation_error_handler(None, error))

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            json.loads(response.body),
            {
                "detail": "이메일 형식이 올바르지 않습니다.",
                "errors": [
                    {
                        "loc": ["body", "email"],
                        "type": "value_error",
                        "msg": "이메일 형식이 올바르지 않습니다.",
                    }
                ],
            },
        )

    def test_returns_korean_message_for_missing_required_fields(self) -> None:
        expected_messages = {
            "email": "이메일은 필수 입력값입니다.",
            "nickname": "닉네임은 필수 입력값입니다.",
            "password": "비밀번호는 필수 입력값입니다.",
        }

        for field, message in expected_messages.items():
            with self.subTest(field=field):
                error = RequestValidationError(
                    [
                        {
                            "type": "missing",
                            "loc": ("body", field),
                            "msg": "Field required",
                            "input": {},
                        }
                    ]
                )

                response = asyncio.run(request_validation_error_handler(None, error))

                self.assertEqual(response.status_code, 422)
                self.assertEqual(json.loads(response.body)["detail"], message)
                self.assertEqual(json.loads(response.body)["errors"][0]["msg"], message)

    def test_returns_korean_message_for_string_length_limits(self) -> None:
        cases = [
            (
                "password",
                "string_too_short",
                {"min_length": 8},
                "비밀번호는 최소 8자 이상 입력해야 합니다.",
            ),
            (
                "password",
                "string_too_long",
                {"max_length": 128},
                "비밀번호는 최대 128자까지 입력할 수 있습니다.",
            ),
            (
                "nickname",
                "string_too_long",
                {"max_length": 50},
                "닉네임은 최대 50자까지 입력할 수 있습니다.",
            ),
        ]

        for field, error_type, context, message in cases:
            with self.subTest(field=field, error_type=error_type):
                error = RequestValidationError(
                    [
                        {
                            "type": error_type,
                            "loc": ("body", field),
                            "msg": "String length validation failed",
                            "input": "x",
                            "ctx": context,
                        }
                    ]
                )

                response = asyncio.run(request_validation_error_handler(None, error))

                self.assertEqual(response.status_code, 422)
                self.assertEqual(json.loads(response.body)["detail"], message)
                self.assertEqual(json.loads(response.body)["errors"][0]["msg"], message)

    def test_returns_all_pydantic_errors_without_sensitive_input(self) -> None:
        with self.assertRaises(ValidationError) as raised:
            SignUpRequest.model_validate(
                {
                    "email": "not-an-email",
                    "nickname": "x" * 51,
                    "password": "secret",
                }
            )

        response = asyncio.run(
            request_validation_error_handler(
                None, RequestValidationError(raised.exception.errors())
            )
        )
        body = json.loads(response.body)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(body["detail"], "이메일 형식이 올바르지 않습니다.")
        self.assertEqual(
            body["errors"],
            [
                {
                    "loc": ["email"],
                    "type": "value_error",
                    "msg": "이메일 형식이 올바르지 않습니다.",
                },
                {
                    "loc": ["nickname"],
                    "type": "string_too_long",
                    "msg": "닉네임은 최대 50자까지 입력할 수 있습니다.",
                },
                {
                    "loc": ["password"],
                    "type": "string_too_short",
                    "msg": "비밀번호는 최소 8자 이상 입력해야 합니다.",
                },
            ],
        )
        self.assertNotIn("input", json.dumps(body))
        self.assertNotIn("secret", json.dumps(body))


if __name__ == "__main__":
    unittest.main()
