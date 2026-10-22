import logging
import re
import sys

from app.core.config import settings

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_LOG_LEVELS = {
    "local": logging.DEBUG,
    "test": logging.WARNING,
    "production": logging.INFO,
}
_HANDLER_MARKER = "_philo_log_handler"
_SENSITIVE_KEY = (
    r"password(?:[_\s-]?hash)?|access[_\s-]?token|refresh[_\s-]?token|"
    r"email[_\s-]?(?:verification[_\s-]?)?token|verification[_\s-]?token|"
    r"jwt|secret[_\s-]?key|api[_\s-]?key|token(?:[_\s-]?hash)?"
)
_REDACTION_PATTERN = re.compile(
    rf"(?:"
    rf"(?P<quoted_prefix>['\"]?(?:authorization|cookie|set-cookie|{_SENSITIVE_KEY})"
    rf"['\"]?\s*[:=](?>\s*))(?P<quote>['\"])(?!\[REDACTED\](?P=quote))"
    rf"(?P<quoted_value>(?:\\[\s\S]|(?!(?P=quote))[^\\])*)(?P=quote)"
    rf"|(?P<unclosed_prefix>['\"]?(?:authorization|cookie|set-cookie|{_SENSITIVE_KEY})"
    rf"['\"]?\s*[:=](?>\s*))(?P<unclosed_quote>['\"])(?!\[REDACTED\]\Z)"
    rf"(?P<unclosed_value>(?:\\[\s\S]|(?!(?P=unclosed_quote))[^\\])*)\Z"
    rf"|(?P<header_prefix>\b(?:authorization|cookie|set-cookie)\b\s*[:=](?>\s*))"
    rf"(?!['\"])(?!\[REDACTED\](?=$|[,\r\n}}\]]))"
    rf"(?P<header_value>[^,\r\n}}]+)"
    rf"|(?P<value_prefix>\b(?:{_SENSITIVE_KEY})\b\s*[:=](?>\s*))"
    rf"(?!['\"])(?!\[REDACTED\](?=$|[\s,;}}\]]))(?P<value>[^\s,;}}]+)"
    rf"|(?P<bearer_prefix>\bBearer(?>\s+))"
    rf"(?!['\"])(?!\[REDACTED\](?=$|[\s,;}}\]]))(?P<bearer_value>[^\s,;}}]+)"
    rf")",
    re.IGNORECASE,
)


def _redact(value: object) -> str:
    def replace(match: re.Match[str]) -> str:
        if match.group("quoted_prefix") is not None:
            quote = match.group("quote")
            return f"{match.group('quoted_prefix')}{quote}[REDACTED]{quote}"
        if match.group("unclosed_prefix") is not None:
            return (
                f"{match.group('unclosed_prefix')}"
                f"{match.group('unclosed_quote')}[REDACTED]"
            )

        prefix = next(
            match.group(name)
            for name in ("header_prefix", "value_prefix", "bearer_prefix")
            if match.group(name) is not None
        )
        return f"{prefix}[REDACTED]"

    return _REDACTION_PATTERN.sub(replace, str(value))


class RedactingFormatter(logging.Formatter):
    """예외와 스택 정보를 포함한 최종 로그 문자열도 마스킹한다."""

    def __init__(
        self, *args: object, base_formatter: logging.Formatter | None = None, **kwargs: object
    ) -> None:
        super().__init__(*args, **kwargs)
        self.base_formatter = base_formatter

    def format(self, record: logging.LogRecord) -> str:
        if self.base_formatter is not None:
            return _redact(self.base_formatter.format(record))
        return _redact(super().format(record))


def _create_handler() -> logging.Handler:
    formatter = RedactingFormatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    setattr(console_handler, _HANDLER_MARKER, True)
    return console_handler


def setup_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(_LOG_LEVELS[settings.app_env])

    managed_handlers = [
        handler
        for handler in root_logger.handlers
        if getattr(handler, _HANDLER_MARKER, False)
    ]
    for handler in root_logger.handlers:
        if handler not in managed_handlers and not isinstance(
            handler.formatter, RedactingFormatter
        ):
            handler.setFormatter(RedactingFormatter(base_formatter=handler.formatter))

    if not managed_handlers:
        root_logger.addHandler(_create_handler())

    # Uvicorn 로그를 루트 Handler로 전달해 Access Log는 유지하고 콘솔 중복은 막는다.
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
