"""Chat domain specific exceptions, messages, and labels."""

from fastapi import status

CHAT_REQUIRED_FIELD_MESSAGES: dict[str, str] = {
    "prompt": "질문 내용은 필수 입력값입니다.",
    "philosopher_id": "철학자 ID는 필수 입력값입니다.",
    "philosopherId": "철학자 ID는 필수 입력값입니다.",
}

CHAT_FIELD_LABELS: dict[str, tuple[str, str]] = {
    "prompt": ("질문 내용", "은"),
    "philosopher_id": ("철학자 ID", "는"),
    "philosopherId": ("철학자 ID", "는"),
    "limit": ("조회 건수", "는"),
    "chat_id": ("채팅방 ID", "는"),
    "chatId": ("채팅방 ID", "는"),
    "cursor": ("커서", "는"),
}


class ChatDomainError(Exception):
    """Base exception for chat domain errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: str = "채팅 요청을 처리할 수 없습니다."

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class ChatNotFoundError(ChatDomainError):
    """Raised when a chat does not exist, is soft-deleted, or is not owned by the user."""

    status_code: int = status.HTTP_404_NOT_FOUND
    detail: str = "해당 채팅방을 찾을 수 없습니다."


class PhilosopherNotFoundError(ChatDomainError):
    """Raised when the requested philosopher does not exist or is inactive."""

    status_code: int = status.HTTP_404_NOT_FOUND
    detail: str = "해당 철학자를 찾을 수 없습니다."


class CursorMessageNotFoundError(ChatDomainError):
    """Raised when the pagination cursor message does not exist or belongs to another chat."""

    status_code: int = status.HTTP_404_NOT_FOUND
    detail: str = "기준 메시지를 찾을 수 없습니다."


class ChatAIUnavailableError(ChatDomainError):
    """Raised when the philosopher AI (LLM) service fails or times out."""

    status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE
    detail: str = (
        "철학자 AI와의 연결이 일시적으로 원활하지 않습니다. 잠시 후 다시 시도해주세요."
    )
