"""채팅 도메인 전용 예외, 필수값 메시지, 필드 라벨."""

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
    """채팅 도메인 예외의 기본 클래스."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: str = "채팅 요청을 처리할 수 없습니다."

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class ChatNotFoundError(ChatDomainError):
    """채팅방이 없거나, 삭제되었거나, 요청한 사용자의 소유가 아닐 때 발생한다."""

    status_code: int = status.HTTP_404_NOT_FOUND
    detail: str = "해당 채팅방을 찾을 수 없습니다."


class PhilosopherNotFoundError(ChatDomainError):
    """요청한 철학자가 없거나 비활성 상태일 때 발생한다."""

    status_code: int = status.HTTP_404_NOT_FOUND
    detail: str = "해당 철학자를 찾을 수 없습니다."


class CursorMessageNotFoundError(ChatDomainError):
    """페이지네이션 기준(cursor) 메시지가 없거나 다른 채팅방의 메시지일 때 발생한다."""

    status_code: int = status.HTTP_404_NOT_FOUND
    detail: str = "기준 메시지를 찾을 수 없습니다."


class ChatBusyError(ChatDomainError):
    """같은 채팅방을 다른 요청이 이미 처리 중일 때 발생한다."""

    status_code: int = status.HTTP_409_CONFLICT
    detail: str = (
        "이전 질문에 대한 답변을 생성하는 중입니다. 잠시 후 다시 시도해주세요."
    )


class ChatAIUnavailableError(ChatDomainError):
    """철학자 AI(LLM) 호출이 실패하거나 시간 초과되었을 때 발생한다."""

    status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE
    detail: str = (
        "철학자 AI와의 연결이 일시적으로 원활하지 않습니다. 잠시 후 다시 시도해주세요."
    )
