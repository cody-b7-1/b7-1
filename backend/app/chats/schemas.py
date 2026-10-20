from datetime import datetime
from typing import Annotated, Literal

from pydantic import UUID4, Field

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


# --- start_chat (POST /chats) ---
class StartChatRequest(CamelModel):
    prompt: str = Field(
        min_length=1,
        max_length=1000,
        description="채팅 시작 프롬프트",
        examples=["진정한 행복이란 무엇인가요?"],
    )
    philosopher_id: PhilosopherIdField


class StartChatResponse(CamelResponseModel):
    chat_id: ChatIdField
    chat_title: ChatTitleField
    answer: str = Field(
        description="채팅 시작 답변",
        examples=["행복은 덕에 따르는 영혼의 활동입니다."],
    )
    philosopher_id: PhilosopherIdField


# --- send_message (POST /chats/{chat_id}/messages) ---
class SendMessageRequest(CamelModel):
    prompt: str = Field(
        min_length=1,
        max_length=1000,
        description="사용자 메시지 내용",
        examples=["그렇다면 덕은 어떻게 기를 수 있나요?"],
    )
    philosopher_id: PhilosopherIdField


class SendMessageResponse(CamelResponseModel):
    chat_id: ChatIdField
    answer: str = Field(
        description="철학자 답변",
        examples=["지성적 덕은 가르침을 통해, 도덕적 덕은 습관을 통해 길러집니다."],
    )
    philosopher_id: PhilosopherIdField


# --- list_chats (GET /chats) ---
class ChatListItem(CamelResponseModel):
    chat_id: ChatIdField
    chat_title: ChatTitleField
    current_philosopher_id: PhilosopherIdField


# --- get_chat (GET /chats/{chat_id}) ---
class MessageItem(CamelResponseModel):
    message_id: UUID4 = Field(
        description="메시지 ID",
        examples=["00000000-0000-4000-8000-000000000010"],
    )
    sender_role: Literal["USER", "PHILOSOPHER"] = Field(
        description="메시지 발신자 역할 (USER | PHILOSOPHER)",
        examples=["PHILOSOPHER"],
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


class GetChatResponse(CamelResponseModel):
    chat_id: ChatIdField
    chat_title: ChatTitleField
    current_philosopher_id: PhilosopherIdField
    messages: list[MessageItem] = Field(
        description="채팅 메시지 목록",
    )
    created_at: datetime = Field(
        description="채팅 생성 시각",
        examples=["2026-10-20T12:00:00Z"],
    )
    updated_at: datetime = Field(
        description="채팅 마지막 업데이트 시각",
        examples=["2026-10-20T12:05:00Z"],
    )
