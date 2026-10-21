from datetime import datetime
from typing import Annotated

from pydantic import UUID4, Field, StringConstraints

from app.chats.enums import SenderRole
from app.core.schemas import CamelModel, CamelResponseModel

# --- 공통 재사용 필드 타입 정의 ---
ChatIdField = Annotated[
    UUID4,
    Field(
        description="채팅 ID",
        examples=["00000000-0000-4000-8000-000000000001"],
    ),
]

ChatTitleField = Annotated[
    str,
    Field(
        max_length=80,
        description="채팅 제목",
        examples=["진정한 행복이란 무엇인가요?"],
    ),
]

PhilosopherIdField = Annotated[
    int,
    Field(
        gt=0,
        description="철학자 ID",
        examples=[1],
    ),
]

PromptField = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=1000,
    ),
    Field(
        description="사용자 입력 프롬프트",
        examples=["진정한 행복이란 무엇인가요?"],
    ),
]


# --- 공통 메시지 아이템 ---
class MessageItem(CamelResponseModel):
    message_id: UUID4 = Field(
        description="메시지 ID",
        examples=["00000000-0000-4000-8000-000000000010"],
    )
    sender_role: SenderRole = Field(
        description="메시지 발신자 역할 (USER | PHILOSOPHER | SYSTEM)",
        examples=[SenderRole.PHILOSOPHER],
    )
    philosopher_id: int | None = Field(
        default=None,
        gt=0,
        description="메시지 발신 철학자 ID (PHILOSOPHER 역할일 때만 존재)",
        examples=[1],
    )
    content: str = Field(
        description="메시지 내용",
        examples=["행복은 덕에 따르는 영혼의 활동입니다."],
    )
    created_at: datetime = Field(
        description="메시지 생성 시각",
        examples=["2026-10-20T12:00:00Z"],
    )


# --- start_chat (POST /chats) ---
class StartChatRequest(CamelModel):
    prompt: PromptField
    philosopher_id: PhilosopherIdField


class StartChatResponse(CamelResponseModel):
    chat_id: ChatIdField
    chat_title: ChatTitleField
    messages: list[MessageItem] = Field(
        description="새로 생성된 첫 대화 메시지 목록 [사용자 질문, 철학자 답변]",
    )


# --- send_message (POST /chats/{chat_id}/messages) ---
class SendMessageRequest(CamelModel):
    prompt: PromptField
    philosopher_id: PhilosopherIdField


class SendMessageResponse(CamelResponseModel):
    messages: list[MessageItem] = Field(
        description="이번 턴에 새로 생성된 메시지 목록 (시간순)",
    )


# --- list_chats (GET /chats) ---
class ChatListItem(CamelResponseModel):
    chat_id: ChatIdField
    chat_title: ChatTitleField
    current_philosopher_id: PhilosopherIdField


class ChatListResponse(CamelResponseModel):
    items: list[ChatListItem] = Field(description="채팅방 목록")
    has_more: bool = Field(
        description="다음 데이터 존재 여부",
        examples=[True],
    )
    next_cursor: UUID4 | None = Field(
        default=None,
        description="다음 대화 목록을 조회할 때 cursor 파라미터로 넘길 채팅방 ID",
        examples=["00000000-0000-4000-8000-000000000001"],
    )


# --- get_chat (GET /chats/{chat_id}) ---
class GetChatResponse(CamelResponseModel):
    chat_id: ChatIdField
    chat_title: ChatTitleField
    current_philosopher_id: PhilosopherIdField
    messages: list[MessageItem] = Field(
        description="채팅 메시지 목록 (시간 오름차순)",
    )
    has_more: bool = Field(
        description="이전(더 오래된) 메시지 존재 여부",
        examples=[True],
    )
    next_cursor: UUID4 | None = Field(
        default=None,
        description="더 오래된 메시지를 조회할 때 cursor 파라미터로 넘길 메시지 ID",
        examples=["00000000-0000-4000-8000-000000000010"],
    )
    created_at: datetime = Field(
        description="채팅 생성 시각",
        examples=["2026-10-20T12:00:00Z"],
    )
    updated_at: datetime = Field(
        description="채팅 마지막 업데이트 시각",
        examples=["2026-10-20T12:05:00Z"],
    )
