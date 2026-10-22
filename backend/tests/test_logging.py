import io
import logging
import sys

import pytest

from app.core import logging as app_logging


@pytest.mark.parametrize(
    ("message", "secret"),
    [
        ("password=plain-password", "plain-password"),
        ("password_hash=argon2-value", "argon2-value"),
        ("access_token=access-value", "access-value"),
        ("refresh-token: refresh-value", "refresh-value"),
        ("email_verification_token=email-value", "email-value"),
        ("jwt=jwt-value", "jwt-value"),
        ("secret_key=secret-value", "secret-value"),
        ("api-key: api-value", "api-value"),
        ("token_hash=hash-value", "hash-value"),
        ("Authorization: Bearer auth-value", "Bearer auth-value"),
        ("Cookie: session=cookie-value; theme=dark", "session=cookie-value"),
        ("Set-Cookie: refresh=cookie-value; HttpOnly", "refresh=cookie-value"),
    ],
)
def test_redact_sensitive_values(message: str, secret: str) -> None:
    redacted = app_logging._redact(message)

    assert secret not in redacted
    assert "[REDACTED]" in redacted


def test_redact_is_idempotent() -> None:
    message = "password=secret Authorization: Bearer token-value"

    redacted = app_logging._redact(message)

    assert app_logging._redact(redacted) == redacted


def test_redact_preserves_json_structure() -> None:
    message = (
        '{"password": "secret", "Authorization": "Bearer auth-token", '
        '"items": ["keep"]}'
    )

    expected = (
        '{"password": "[REDACTED]", "Authorization": "[REDACTED]", '
        '"items": ["keep"]}'
    )
    assert app_logging._redact(message) == expected
    assert app_logging._redact(app_logging._redact(message)) == expected


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ('password="secret"', 'password="[REDACTED]"'),
        ("password='secret'", "password='[REDACTED]'"),
        ('Authorization: "Bearer auth-token"', 'Authorization: "[REDACTED]"'),
        ("Cookie='session=cookie-value'", "Cookie='[REDACTED]'"),
        ('Set-Cookie="refresh=cookie-value"', 'Set-Cookie="[REDACTED]"'),
    ],
)
def test_redact_preserves_quotes(message: str, expected: str) -> None:
    assert app_logging._redact(message) == expected
    assert app_logging._redact(app_logging._redact(message)) == expected


@pytest.mark.parametrize(
    "message",
    [
        "ordinary log message [with brackets]",
        "password=[REDACTED]",
        'password="[REDACTED]"',
        "password='[REDACTED]'",
        '{"password": "[REDACTED]", "items": ["keep"]}',
        "Authorization: [REDACTED]",
        'Authorization: "[REDACTED]"',
        "Bearer [REDACTED]",
        "Cookie='[REDACTED]'",
        'Set-Cookie="[REDACTED]"',
    ],
)
def test_redact_preserves_normal_and_already_redacted_strings(message: str) -> None:
    assert app_logging._redact(message) == message


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Authorization: Bearer auth-token", "Authorization: [REDACTED]"),
        ("Bearer auth-token", "Bearer [REDACTED]"),
    ],
)
def test_redact_authorization_and_bearer(message: str, expected: str) -> None:
    assert app_logging._redact(message) == expected
    assert app_logging._redact(app_logging._redact(message)) == expected


@pytest.mark.parametrize(
    ("message", "expected", "secret_fragments"),
    [
        ("token=[REDACTED]secret", "token=[REDACTED]", ("secret",)),
        ('password="abc\n123"', 'password="[REDACTED]"', ("abc", "123")),
        ('password="abc\n123', 'password="[REDACTED]', ("abc", "123")),
        ("password=abc]def", "password=[REDACTED]", ("abc", "def")),
        (
            "Authorization: Bearer [REDACTED]",
            "Authorization: [REDACTED]",
            ("Bearer",),
        ),
    ],
)
def test_redact_handles_sensitive_edge_cases(
    message: str, expected: str, secret_fragments: tuple[str, ...]
) -> None:
    redacted = app_logging._redact(message)

    assert redacted == expected
    assert app_logging._redact(redacted) == redacted
    for secret in secret_fragments:
        assert secret not in redacted


@pytest.mark.parametrize(
    ("message", "expected", "secrets"),
    [
        (
            '{"password": "abc\\\"secret123"}',
            '{"password": "[REDACTED]"}',
            ("abc", "secret123"),
        ),
        (
            'password="abc\\\"secret123',
            'password="[REDACTED]',
            ("abc", "secret123"),
        ),
        (
            'password="line1\\\"quoted\nline2"',
            'password="[REDACTED]"',
            ("line1", "quoted", "line2"),
        ),
    ],
)
def test_redact_handles_escaped_quotes(
    message: str, expected: str, secrets: tuple[str, ...]
) -> None:
    redacted = app_logging._redact(message)

    assert redacted == expected
    assert app_logging._redact(redacted) == redacted
    for secret in secrets:
        assert secret not in redacted


def test_redact_does_not_mask_user_id_or_normal_text() -> None:
    message = "user_id=123e4567-e89b-12d3-a456-426614174000 token count is 12"

    assert app_logging._redact(message) == message


def test_formatter_redacts_exception_message_and_traceback() -> None:
    formatter = app_logging.RedactingFormatter("%(message)s\n%(exc_text)s")
    try:
        raise ValueError("api_key=exception-secret")
    except ValueError:
        record = logging.LogRecord(
            "test", logging.ERROR, __file__, 1, "request failed", (), sys.exc_info()
        )

    output = formatter.format(record)

    assert "exception-secret" not in output
    assert "api_key=[REDACTED]" in output


def test_formatter_applies_redaction_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    redact = app_logging._redact

    def counting_redact(value: object) -> str:
        calls.append(str(value))
        return redact(value)

    monkeypatch.setattr(app_logging, "_redact", counting_redact)
    formatter = app_logging.RedactingFormatter("%(message)s")
    record = logging.LogRecord(
        "test", logging.INFO, __file__, 1, "password=%s", ("secret",), None
    )

    assert formatter.format(record) == "password=[REDACTED]"
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("app_env", "expected_level"),
    [
        ("local", logging.DEBUG),
        ("test", logging.WARNING),
        ("production", logging.INFO),
    ],
)
def test_setup_logging_sets_level_and_does_not_duplicate_handler(
    monkeypatch: pytest.MonkeyPatch, app_env: str, expected_level: int
) -> None:
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    root_logger.handlers = [
        handler
        for handler in root_logger.handlers
        if not getattr(handler, app_logging._HANDLER_MARKER, False)
    ]
    monkeypatch.setattr(app_logging.settings, "app_env", app_env)

    try:
        app_logging.setup_logging()
        app_logging.setup_logging()
        managed_handlers = [
            handler
            for handler in root_logger.handlers
            if getattr(handler, app_logging._HANDLER_MARKER, False)
        ]

        assert root_logger.level == expected_level
        assert len(managed_handlers) == 1
        assert isinstance(managed_handlers[0], logging.StreamHandler)
        assert managed_handlers[0].stream is sys.stdout
        assert managed_handlers[0].filters == []
        for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            uvicorn_logger = logging.getLogger(logger_name)
            assert uvicorn_logger.handlers == []
            assert uvicorn_logger.propagate is True
    finally:
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)


def test_setup_logging_preserves_and_redacts_unmanaged_root_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    unsafe_output = io.StringIO()
    unsafe_handler = logging.StreamHandler(unsafe_output)
    unsafe_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.handlers = [unsafe_handler]
    monkeypatch.setattr(app_logging.settings, "app_env", "local")

    try:
        app_logging.setup_logging()

        assert unsafe_handler in root_logger.handlers
        assert isinstance(unsafe_handler.formatter, app_logging.RedactingFormatter)

        root_logger.info("password=capture-secret")

        assert unsafe_output.getvalue() == "password=[REDACTED]\n"
    finally:
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)


def test_setup_logging_preserves_pytest_log_capture(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    root_logger = logging.getLogger()
    capture_handler = caplog.handler
    original_formatter = capture_handler.formatter
    monkeypatch.setattr(app_logging.settings, "app_env", "local")

    try:
        app_logging.setup_logging()
        logging.getLogger("capture-test").warning("password=pytest-secret")

        assert capture_handler in root_logger.handlers
        assert "pytest-secret" not in caplog.text
        assert "password=[REDACTED]" in caplog.text
    finally:
        capture_handler.setFormatter(original_formatter)
