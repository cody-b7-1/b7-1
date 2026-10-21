from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select

from app.chats.enums import SenderRole
from app.chats.exceptions import (
    ChatAIUnavailableError,
    ChatNotFoundError,
    CursorMessageNotFoundError,
    PhilosopherNotFoundError,
)
from app.chats.models.chat import Chat
from app.chats.models.message import Message
from app.chats.schemas import (
    ChatListItem,
    ChatListResponse,
    GetChatResponse,
    MessageItem,
    SendMessageRequest,
    SendMessageResponse,
    StartChatRequest,
    StartChatResponse,
)
from app.db.mixins import utc_now
from app.db.session import DBSession
from app.philosophers.models.philosopher import Philosopher


class ChatService:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    def _get_owned_chat(self, chat_id: UUID, user_id: UUID) -> Chat:
        chat = self.db.get(Chat, chat_id)
        if chat is None or chat.deleted_at is not None or chat.user_id != user_id:
            raise ChatNotFoundError()
        return chat

    def _get_active_philosopher(self, philosopher_id: int) -> Philosopher:
        philosopher = self.db.get(Philosopher, philosopher_id)
        if philosopher is None or not philosopher.is_active:
            raise PhilosopherNotFoundError()
        return philosopher

    def _create_dialogue_turn(
        self,
        chat_id: UUID,
        prompt: str,
        philosopher: Philosopher,
        base_time: datetime | None = None,
    ) -> tuple[Message, Message]:
        # 1. 철학자 AI 답변 생성 (TODO: 실제 LLM API 호출로 교체, 실패 시 503 에러 발생으로 DB 롤백 보호)
        try:
            # answer = self._call_llm(prompt, philosopher)
            answer = f"{philosopher.name}의 답변입니다."
        except Exception as exc:
            raise ChatAIUnavailableError() from exc

        now = base_time or utc_now()

        # 2. 사용자 질문 메시지 생성
        user_message = Message(
            message_id=uuid4(),
            chat_id=chat_id,
            philosopher_id=None,
            sender_role=SenderRole.USER,
            content=prompt,
            created_at=now,
        )

        # 3. 철학자 답변 메시지 생성 (성공한 완전한 답변만 생성, 사용자 질문보다 1초 후 시각으로 순서 보장)
        assistant_message = Message(
            message_id=uuid4(),
            chat_id=chat_id,
            philosopher_id=philosopher.philosopher_id,
            sender_role=SenderRole.PHILOSOPHER,
            content=answer,
            is_success=True,
            created_at=now + timedelta(seconds=1),
        )

        return user_message, assistant_message

    # POST /chats
    def start_chat(
        self,
        request: StartChatRequest,
        user_id: UUID,
    ) -> StartChatResponse:
        # 1. 대화할 철학자 조회 및 활성화 여부 확인
        philosopher = self._get_active_philosopher(request.philosopher_id)

        now = utc_now()

        # 2. 채팅방(Chat) 생성 (프롬프트 앞부분 최대 80자, 추후 LLM 요약으로 고도화)
        chat_title = request.prompt[:80]
        chat = Chat(
            chat_id=uuid4(),
            user_id=user_id,
            current_philosopher_id=philosopher.philosopher_id,
            title=chat_title,
            created_at=now,
            updated_at=now,
        )

        # 3. 사용자 질문 및 철학자 답변 메시지 생성 (한 턴)
        user_message, assistant_message = self._create_dialogue_turn(
            chat_id=chat.chat_id,
            prompt=request.prompt,
            philosopher=philosopher,
            base_time=now,
        )

        # 4. DB 저장 (원자적 커밋)
        self.db.add_all([chat, user_message, assistant_message])
        self.db.commit()

        # 5. 응답 스키마 반환
        return StartChatResponse(
            chat_id=chat.chat_id,
            chat_title=chat.title,
            messages=[
                MessageItem.model_validate(m) for m in (user_message, assistant_message)
            ],
        )

    # GET /chats
    def list_chats(
        self,
        user_id: UUID,
        limit: int = 20,
        cursor: UUID | None = None,
    ) -> ChatListResponse:
        stmt = select(Chat).where(
            Chat.user_id == user_id,
            Chat.deleted_at.is_(None),
        )

        if cursor is not None:
            cursor_chat = self._get_owned_chat(cursor, user_id)
            stmt = stmt.where(
                (Chat.updated_at < cursor_chat.updated_at)
                | (
                    (Chat.updated_at == cursor_chat.updated_at)
                    & (Chat.chat_id < cursor_chat.chat_id)
                )
            )

        rows = self.db.scalars(
            stmt.order_by(Chat.updated_at.desc(), Chat.chat_id.desc()).limit(limit + 1)
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

    # POST /chats/{chat_id}/messages
    def send_message(
        self,
        chat_id: UUID,
        request: SendMessageRequest,
        user_id: UUID,
    ) -> SendMessageResponse:
        # 1. 채팅방 조회 및 소유권 확인
        chat = self._get_owned_chat(chat_id, user_id)

        # 2. 대화할 철학자 조회 및 활성화 여부 확인
        philosopher = self._get_active_philosopher(request.philosopher_id)

        now = utc_now()
        new_messages: list[Message] = []

        # 3. 철학자가 변경된 경우에만 시스템 메시지 추가 및 시각 갱신
        if chat.current_philosopher_id != philosopher.philosopher_id:
            system_message = Message(
                message_id=uuid4(),
                chat_id=chat.chat_id,
                philosopher_id=None,
                sender_role=SenderRole.SYSTEM,
                content=f"대화 상대가 {philosopher.name}(으)로 변경되었습니다.",
                created_at=now,
            )
            chat.current_philosopher_id = philosopher.philosopher_id
            new_messages.append(system_message)
            now += timedelta(seconds=1)

        # 4. 사용자 질문 및 철학자 답변 메시지 생성 (실패 시 여기서 503 발생 -> 메모리/DB 변경 없이 안전하게 중단)
        user_message, assistant_message = self._create_dialogue_turn(
            chat_id=chat.chat_id,
            prompt=request.prompt,
            philosopher=philosopher,
            base_time=now,
        )

        # 5. 시간 순서대로 메시지 배치 ([SYSTEM, USER, PHILOSOPHER])
        new_messages.extend([user_message, assistant_message])

        # 6. 채팅방 최신 활동 시각(updated_at) 갱신
        chat.updated_at = assistant_message.created_at

        # 7. DB 저장 (원자적 커밋)
        self.db.add_all([chat, *new_messages])
        self.db.commit()

        # 8. 응답 스키마 반환
        return SendMessageResponse(
            messages=[MessageItem.model_validate(m) for m in new_messages],
        )

    # DELETE /chats/{chat_id}
    def delete_chat(
        self,
        chat_id: UUID,
        user_id: UUID,
    ) -> None:
        chat = self._get_owned_chat(chat_id, user_id)
        chat.deleted_at = utc_now()
        self.db.commit()

    # GET /chats/{chat_id}
    def get_chat(
        self,
        chat_id: UUID,
        user_id: UUID,
        limit: int = 30,
        cursor: UUID | None = None,
    ) -> GetChatResponse:
        chat = self._get_owned_chat(chat_id, user_id)

        stmt = select(Message).where(Message.chat_id == chat_id)

        # cursor가 있으면 해당 메시지의 생성 시각 이전 데이터만 필터링
        if cursor is not None:
            cursor_msg = self.db.get(Message, cursor)
            if cursor_msg is None or cursor_msg.chat_id != chat_id:
                raise CursorMessageNotFoundError()
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
            messages=[MessageItem.model_validate(m) for m in reversed(paged_messages)],
            has_more=has_more,
            next_cursor=next_cursor,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
        )
