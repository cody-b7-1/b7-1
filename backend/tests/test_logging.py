import io
import logging
import sys
from logging.handlers import RotatingFileHandler

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


def test_console_handler_writes_redacted_log(monkeypatch: pytest.MonkeyPatch) -> None:
    output = io.StringIO()
    monkeypatch.setattr(sys, "stdout", output)
    handler = app_logging._create_console_handler()
    record = logging.LogRecord(
        "console-test", logging.INFO, __file__, 1, "password=%s", ("secret",), None
    )

    handler.handle(record)

    assert "password=[REDACTED]" in output.getvalue()
    assert "secret" not in output.getvalue()


@pytest.mark.parametrize(
    ("app_env", "expected_level"),
    [
        ("local", logging.DEBUG),
        ("test", logging.WARNING),
        ("production", logging.INFO),
    ],
)
def test_setup_logging_sets_level_and_does_not_duplicate_handler(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    app_env: str,
    expected_level: int,
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
    monkeypatch.setattr(app_logging, "LOG_FILE_PATH", tmp_path / "app.log")

    try:
        app_logging.setup_logging()
        app_logging.setup_logging()
        managed_handlers = [
            handler
            for handler in root_logger.handlers
            if getattr(handler, app_logging._HANDLER_MARKER, False)
        ]

        assert root_logger.level == expected_level
        assert len(managed_handlers) == 2
        handlers_by_kind = {
            getattr(handler, app_logging._HANDLER_MARKER): handler
            for handler in managed_handlers
        }
        console_handler = handlers_by_kind["console"]
        file_handler = handlers_by_kind["file"]
        assert isinstance(console_handler, logging.StreamHandler)
        assert console_handler.stream is sys.stdout
        assert console_handler.filters == []
        assert isinstance(file_handler, RotatingFileHandler)
        assert file_handler.maxBytes == 10 * 1024 * 1024
        assert file_handler.backupCount == 4
        for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            uvicorn_logger = logging.getLogger(logger_name)
            assert uvicorn_logger.handlers == []
            assert uvicorn_logger.propagate is True
    finally:
        for handler in root_logger.handlers[:]:
            if handler not in original_handlers:
                root_logger.removeHandler(handler)
                handler.close()
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)


def test_setup_logging_preserves_and_redacts_unmanaged_root_handler(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    unsafe_output = io.StringIO()
    unsafe_handler = logging.StreamHandler(unsafe_output)
    unsafe_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.handlers = [unsafe_handler]
    monkeypatch.setattr(app_logging.settings, "app_env", "local")
    monkeypatch.setattr(app_logging, "LOG_FILE_PATH", tmp_path / "app.log")

    try:
        app_logging.setup_logging()

        assert unsafe_handler in root_logger.handlers
        assert isinstance(unsafe_handler.formatter, app_logging.RedactingFormatter)

        root_logger.info("password=capture-secret")

        assert unsafe_output.getvalue() == "password=[REDACTED]\n"
    finally:
        for handler in root_logger.handlers[:]:
            if handler is not unsafe_handler:
                root_logger.removeHandler(handler)
                handler.close()
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)


def test_file_handler_rotates_and_redacts_sensitive_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    log_path = tmp_path / "logs" / "app.log"
    monkeypatch.setattr(app_logging, "LOG_FILE_PATH", log_path)
    monkeypatch.setattr(app_logging, "MAX_LOG_FILE_SIZE", 512)
    monkeypatch.setattr(app_logging, "LOG_BACKUP_COUNT", 4)
    handler = app_logging._create_file_handler()
    logger = logging.getLogger("file-rotation-test")
    original_handlers = logger.handlers[:]
    original_level = logger.level
    original_propagate = logger.propagate
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False

    try:
        for index in range(30):
            logger.info("entry=%s password=file-secret %s", index, "x" * 100)
        try:
            raise ValueError("api_key=traceback-secret")
        except ValueError:
            logger.exception("파일 예외")
    finally:
        handler.close()
        logger.handlers = original_handlers
        logger.setLevel(original_level)
        logger.propagate = original_propagate

    log_files = sorted(log_path.parent.glob("app.log*"))
    output = "".join(path.read_text(encoding="utf-8") for path in log_files)

    assert log_path.exists()
    assert len(log_files) == 5
    assert not (log_path.parent / "app.log.5").exists()
    assert "file-secret" not in output
    assert "traceback-secret" not in output
    assert "[REDACTED]" in output


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
