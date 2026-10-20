from uuid import UUID, uuid4

from fastapi import HTTPException, status
from pydantic import UUID4
from sqlalchemy import select

from app.chats.models.chat import Chat
from app.chats.models.message import Message
from app.chats.schemas import (
    ChatListItem,
    ChatListResponse,
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
            sender_role="USER",
            content=request.prompt,
        )

        # 4. 철학자(AI) 첫 답변 생성 및 메시지 저장 (TODO: LLM API 호출로 교체)
        answer = f"{philosopher.name}의 답변입니다."
        assistant_message = Message(
            message_id=uuid4(),
            chat_id=chat.chat_id,
            philosopher_id=philosopher.philosopher_id,
            sender_role="PHILOSOPHER",
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
        offset: int = 0,
        user_id: UUID4 | None = None,
    ) -> ChatListResponse:
        target_user_id = user_id or UUID(
            "00000000-0000-4000-8000-000000000001"
        )  # TODO: 인증(Auth) 연동 후 실제 로그인 유저의 user_id 사용

        stmt = (
            select(Chat)
            .where(Chat.user_id == target_user_id, Chat.deleted_at.is_(None))
            .order_by(Chat.updated_at.desc())
        )
        all_chats = self.db.scalars(stmt).all()
        total = len(all_chats)
        paged_chats = all_chats[offset : offset + limit]

        return ChatListResponse(
            items=[
                ChatListItem(
                    chat_id=chat.chat_id,
                    chat_title=chat.title,
                    current_philosopher_id=chat.current_philosopher_id,
                )
                for chat in paged_chats
            ],
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + len(paged_chats) < total,
        )

    def delete_chat(self, chat_id: UUID4) -> None:
        pass

    # def get_chat(self, chat_id: UUID4) -> GetChatResponse:
    #     pass
