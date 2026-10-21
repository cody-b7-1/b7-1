from uuid import UUID, uuid4

from fastapi import HTTPException, status
from pydantic import UUID4
from sqlalchemy import select

from app.chats.enums import SenderRole
from app.chats.models.chat import Chat
from app.chats.models.message import Message
from app.chats.schemas import (
    ChatListItem,
    ChatListResponse,
    GetChatResponse,
    MessageItem,
    StartChatRequest,
    StartChatResponse,
)
from app.db.session import DBSession
from app.philosophers.models.philosopher import Philosopher

# todo : 이후에 수정될 예정


class ChatService:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    def start_chat(
        self,
        request: StartChatRequest,
        user_id: UUID | None = None,
    ) -> StartChatResponse:
        # 1. 대화할 철학자 조회 및 활성화 여부 확인
        philosopher = self.db.get(Philosopher, request.philosopher_id)
        if philosopher is None or not philosopher.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 철학자를 찾을 수 없습니다.",
            )

        # 2. 채팅방(Chat) 생성 (제목은 프롬프트 앞부분 최대 80자로 임시 설정하거나 LLM으로 요약)
        chat_title = request.prompt[:80]
        chat = Chat(
            chat_id=uuid4(),
            user_id=user_id
            or UUID(
                "00000000-0000-4000-8000-000000000001"
            ),  # TODO: 인증(Auth) 연동 후 실제 로그인 유저의 user_id 사용
            current_philosopher_id=philosopher.philosopher_id,
            title=chat_title,
        )
        # self.db.add(chat)

        # 3. 사용자 첫 질문 메시지 저장
        user_message = Message(
            message_id=uuid4(),
            chat_id=chat.chat_id,
            philosopher_id=None,
            sender_role=SenderRole.USER,
            content=request.prompt,
        )

        # 4. 철학자(AI) 첫 답변 생성 및 메시지 저장 (TODO: LLM API 호출로 교체)
        answer = f"{philosopher.name}의 답변입니다."
        assistant_message = Message(
            message_id=uuid4(),
            chat_id=chat.chat_id,
            philosopher_id=philosopher.philosopher_id,
            sender_role=SenderRole.PHILOSOPHER,
            content=answer,
            is_success=True,
        )

        # self.db.add_all([user_message, assistant_message])
        # self.db.commit()
        _ = (user_message, assistant_message)

        # 5. 응답 스키마 반환
        return StartChatResponse(
            chat_id=chat.chat_id,
            chat_title=chat.title,
            answer=answer,
            philosopher_id=philosopher.philosopher_id,
        )

    def list_chats(
        self,
        limit: int = 20,
        cursor: UUID4 | None = None,
        user_id: UUID4 | None = None,
    ) -> ChatListResponse:
        target_user_id = user_id or UUID(
            "00000000-0000-4000-8000-000000000001"
        )  # TODO: 인증(Auth) 연동 후 실제 로그인 유저의 user_id 사용

        stmt = select(Chat).where(
            Chat.user_id == target_user_id,
            Chat.deleted_at.is_(None),
        )

        if cursor is not None:
            cursor_chat = self.db.get(Chat, cursor)
            if cursor_chat is None or cursor_chat.deleted_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="기준 채팅방을 찾을 수 없습니다.",
                )
            stmt = stmt.where(
                (Chat.updated_at < cursor_chat.updated_at)
                | (
                    (Chat.updated_at == cursor_chat.updated_at)
                    & (Chat.chat_id < cursor_chat.chat_id)
                )
            )

        rows = self.db.scalars(
            stmt.order_by(
                Chat.updated_at.desc(), Chat.chat_id.desc()
            ).limit(limit + 1)
        ).all()
        has_more = len(rows) > limit
        paged_chats = rows[:limit]
        next_cursor = paged_chats[-1].chat_id if has_more else None

        return ChatListResponse(
            items=[
                ChatListItem(
                    chat_id=chat.chat_id,
                    chat_title=chat.title,
                    current_philosopher_id=chat.current_philosopher_id,
                )
                for chat in paged_chats
            ],
            has_more=has_more,
            next_cursor=next_cursor,
        )

    def delete_chat(self, chat_id: UUID4) -> None:
        pass

    def get_chat(
        self,
        chat_id: UUID4,
        limit: int = 30,
        cursor: UUID4 | None = None,
    ) -> GetChatResponse:
        chat = self.db.get(Chat, chat_id)
        if chat is None or chat.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 채팅방을 찾을 수 없습니다.",
            )

        stmt = select(Message).where(Message.chat_id == chat_id)

        # cursor가 있으면 해당 메시지의 생성 시각 이전 데이터만 필터링
        if cursor is not None:
            cursor_msg = self.db.get(Message, cursor)
            if cursor_msg is None or cursor_msg.chat_id != chat_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="기준 메시지를 찾을 수 없습니다.",
                )
            stmt = stmt.where(
                (Message.created_at < cursor_msg.created_at)
                | (
                    (Message.created_at == cursor_msg.created_at)
                    & (Message.message_id < cursor_msg.message_id)
                )
            )

        # 최신순으로 limit + 1개를 가져와 다음 페이지(has_more) 여부 판단
        rows = self.db.scalars(
            stmt.order_by(Message.created_at.desc(), Message.message_id.desc()).limit(
                limit + 1
            )
        ).all()
        has_more = len(rows) > limit
        paged_messages = rows[:limit]
        next_cursor = paged_messages[-1].message_id if has_more else None

        return GetChatResponse(
            chat_id=chat.chat_id,
            chat_title=chat.title,
            current_philosopher_id=chat.current_philosopher_id,
            messages=[
                MessageItem(
                    message_id=m.message_id,
                    sender_role=m.sender_role,
                    philosopher_id=m.philosopher_id,
                    content=m.content,
                    created_at=m.created_at,
                )
                for m in reversed(paged_messages)
            ],
            has_more=has_more,
            next_cursor=next_cursor,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
        )
