"""Application-wide exception handling."""

from collections.abc import Mapping
from typing import cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ExceptionHandler

from app.chats.exceptions import (
    CHAT_FIELD_LABELS,
    CHAT_REQUIRED_FIELD_MESSAGES,
    ChatDomainError,
)

REQUIRED_FIELD_MESSAGES: dict[str, str] = {
    "email": "이메일은 필수 입력값입니다.",
    "nickname": "닉네임은 필수 입력값입니다.",
    "password": "비밀번호는 필수 입력값입니다.",
    **CHAT_REQUIRED_FIELD_MESSAGES,
}

FIELD_LABELS: dict[str, tuple[str, str]] = {
    "nickname": ("닉네임", "은"),
    "password": ("비밀번호", "는"),
    **CHAT_FIELD_LABELS,
}


async def chat_domain_error_handler(
    _request: Request, error: ChatDomainError
) -> JSONResponse:
    """Return a consistent JSON response for chat domain business errors."""
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.detail},
    )


async def unhandled_exception_handler(
    _request: Request, _error: Exception
) -> JSONResponse:
    """Return a safe, consistent response for unexpected server errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "서버 내부 오류가 발생했습니다."},
    )


async def request_validation_error_handler(
    _request: Request, error: RequestValidationError
) -> JSONResponse:
    """Return all validation errors without exposing submitted input values."""
    raw_errors = cast(list[Mapping[str, object]], error.errors())
    errors = [
        {
            "loc": list(cast(tuple[str | int, ...], validation_error.get("loc", ()))),
            "type": str(validation_error.get("type", "")),
            "msg": _validation_error_message(validation_error),
        }
        for validation_error in raw_errors
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            # Preserve the existing summary shape for clients already using detail.
            "detail": errors[0]["msg"] if errors else "요청 값이 올바르지 않습니다.",
            "errors": errors,
        },
    )


def _validation_error_message(validation_error: Mapping[str, object]) -> str:
    """Translate known validation errors while retaining unknown Pydantic messages."""
    location = cast(tuple[str | int, ...], validation_error.get("loc", ()))
    raw_field_name = location[-1] if location else None
    field_name = raw_field_name if isinstance(raw_field_name, str) else None
    error_type = str(validation_error.get("type", ""))

    if field_name == "email" and error_type == "value_error":
        return "이메일 형식이 올바르지 않습니다."
    if error_type == "missing" and field_name is not None:
        message = REQUIRED_FIELD_MESSAGES.get(field_name)
        if message:
            return message

    field = FIELD_LABELS.get(field_name) if field_name is not None else None
    context = cast(Mapping[str, object], validation_error.get("ctx", {}))

    if field and error_type == "string_too_short":
        label, particle = field
        return f"{label}{particle} 최소 {context['min_length']}자 이상 입력해야 합니다."

    if field and error_type == "string_too_long":
        label, particle = field
        return (
            f"{label}{particle} 최대 {context['max_length']}자까지 입력할 수 있습니다."
        )

    if field and error_type == "greater_than":
        label, particle = field
        return f"{label}{particle} {context['gt']}보다 커야 합니다."

    if field and error_type == "greater_than_equal":
        label, particle = field
        return f"{label}{particle} 최소 {context['ge']} 이상이어야 합니다."

    if field and error_type == "less_than_equal":
        label, particle = field
        return f"{label}{particle} 최대 {context['le']} 이하이어야 합니다."

    if error_type == "uuid_parsing":
        if field:
            label, particle = field
            return f"{label}{particle} 올바른 UUID 형식이어야 합니다."
        return "올바른 UUID 형식이 아닙니다."

    if error_type in ("int_parsing", "int_type"):
        if field:
            label, particle = field
            return f"{label}{particle} 숫자 형식이어야 합니다."
        return "올바른 숫자 형식이 아닙니다."

    return str(validation_error.get("msg", ""))


# 정의한 예외 처리 함수를 FastAPI 애플리케이션에 등록
def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide exception handlers."""
    app.add_exception_handler(
        ChatDomainError,
        cast(ExceptionHandler, chat_domain_error_handler),
    )
    app.add_exception_handler(
        RequestValidationError,
        cast(ExceptionHandler, request_validation_error_handler),
    )
    app.add_exception_handler(Exception, unhandled_exception_handler)
