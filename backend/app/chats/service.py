from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.chats.enums import SenderRole
from app.chats.exceptions import (
    ChatBusyError,
    ChatNotFoundError,
    CursorMessageNotFoundError,
    PhilosopherNotFoundError,
)
from app.chats.llm import LLMService, llm_service
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

# MariaDB(1205: 잠금 대기 초과, NOWAIT 시 즉시 반환), MySQL 8(3572: NOWAIT 잠금 실패)
LOCK_NOT_AVAILABLE_ERROR_CODES = frozenset({1205, 3572})


def _is_lock_not_available(error: OperationalError) -> bool:
    args = getattr(error.orig, "args", ())
    return bool(args) and args[0] in LOCK_NOT_AVAILABLE_ERROR_CODES


class ChatService:
    def __init__(
        self,
        db: DBSession,
        llm: LLMService = llm_service,
    ) -> None:
        self.db = db
        self.llm = llm

    def _lock_chat(self, chat: Chat) -> None:
        """채팅방 행을 NOWAIT로 잠가 같은 방의 동시 처리를 막는다.

        이미 다른 요청이 잠갔다면 기다리지 않고 ChatBusyError(409)를 발생시킨다.
        잠금은 commit 또는 롤백(세션 종료) 시 자동으로 해제된다.
        """
        try:
            self.db.refresh(chat, with_for_update={"nowait": True})
        except OperationalError as exc:
            if _is_lock_not_available(exc):
                raise ChatBusyError() from exc
            raise  # 잠금 실패가 아닌 다른 DB 오류는 그대로 상위로 전달

    def _get_owned_chat(
        self, chat_id: UUID, user_id: UUID, *, lock: bool = False
    ) -> Chat:
        chat = self.db.get(Chat, chat_id)
        if chat is None or chat.deleted_at is not None or chat.user_id != user_id:
            raise ChatNotFoundError()

        # 소유권을 먼저 확인한 뒤에 잠가서, 타인의 요청이 남의 채팅방 잠금에 영향을 주지 않게 한다.
        if lock:
            self._lock_chat(chat)
            if chat.deleted_at is not None:
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
        history: Sequence[Message] | None = None,
        base_time: datetime | None = None,
    ) -> tuple[Message, Message]:
        # 1. 사용자 질문 시각 기록
        user_created_at = base_time or utc_now()

        # 2. 철학자 AI 답변 생성 (실제 LLM 호출, 실패 시 ChatAIUnavailableError 발생으로 DB 롤백 보호)
        answer, token_count = self.llm.generate_chat_answer(
            prompt=prompt,
            philosopher=philosopher,
            history=history,
        )

        # 3. 답변 생성 완료 시각 기록 (실제 완료 시각 반영, 테스트 등 초고속 환경에서 질문 시각 이후로 순서 보장)
        completed_at = utc_now()
        assistant_created_at = max(completed_at, user_created_at + timedelta(seconds=1))

        # 4. 사용자 질문 메시지 생성
        user_message = Message(
            message_id=uuid4(),
            chat_id=chat_id,
            philosopher_id=None,
            sender_role=SenderRole.USER,
            content=prompt,
            created_at=user_created_at,
        )

        # 5. 철학자 답변 메시지 생성
        assistant_message = Message(
            message_id=uuid4(),
            chat_id=chat_id,
            philosopher_id=philosopher.philosopher_id,
            sender_role=SenderRole.PHILOSOPHER,
            content=answer,
            token_count=token_count,
            is_success=True,
            created_at=assistant_created_at,
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
        chat_id = uuid4()

        # 2. 사용자 질문 및 철학자 답변 메시지 생성 (핵심 LLM 호출)
        #    답변 생성이 실패(503)하면 제목 요약 호출 없이 즉시 실패 처리하여 리소스 및 대기시간을 절약한다.
        user_message, assistant_message = self._create_dialogue_turn(
            chat_id=chat_id,
            prompt=request.prompt,
            philosopher=philosopher,
            history=None,
            base_time=now,
        )

        # 3. 답변 생성 성공 후 첫 질문을 바탕으로 대화방 제목 AI 요약 (실패 시 질문 앞부분으로 fallback)
        chat_title = self.llm.summarize_chat_title(request.prompt)

        # 4. 채팅방 엔티티 생성 (최신 활동 시각은 답변 메시지 생성 시각으로 동기화)
        chat = Chat(
            chat_id=chat_id,
            user_id=user_id,
            current_philosopher_id=philosopher.philosopher_id,
            title=chat_title,
            created_at=now,
            updated_at=assistant_message.created_at,
        )

        # 5. DB 저장 (원자적 커밋)
        self.db.add_all([chat, user_message, assistant_message])
        self.db.commit()

        # 6. 응답 스키마 반환
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
        # 1. 채팅방 조회, 소유권 확인 및 잠금 (같은 방의 동시 전송은 409)
        chat = self._get_owned_chat(chat_id, user_id, lock=True)

        # 2. 대화할 철학자 조회 및 활성화 여부 확인
        philosopher = self._get_active_philosopher(request.philosopher_id)

        # 3. LLM에게 전달할 이전 대화 기록 조회 (시간 오름차순, 최근 최대 20개 문맥)
        existing_messages = self.db.scalars(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc(), Message.message_id.desc())
            .limit(20)
        ).all()
        history = list(reversed(existing_messages))

        now = utc_now()
        new_messages: list[Message] = []

        # 4. 사용자 질문 및 철학자 답변 메시지 생성 (실패 시 503 발생 -> 객체 상태 변경 없음)
        philosopher_changed = chat.current_philosopher_id != philosopher.philosopher_id
        turn_base_time = now + timedelta(seconds=1) if philosopher_changed else now

        user_message, assistant_message = self._create_dialogue_turn(
            chat_id=chat.chat_id,
            prompt=request.prompt,
            philosopher=philosopher,
            history=history,
            base_time=turn_base_time,
        )

        # 5. 철학자가 변경된 경우 시스템 메시지 생성 및 대화방의 현재 철학자 변경
        if philosopher_changed:
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

        # 6. 메시지 순서: [SYSTEM, USER, PHILOSOPHER] 또는 [USER, PHILOSOPHER]
        new_messages.extend([user_message, assistant_message])

        # 7. 채팅방 최신 활동 시각(updated_at) 갱신
        chat.updated_at = assistant_message.created_at

        # 8. DB 저장 (원자적 커밋)
        self.db.add_all([chat, *new_messages])
        self.db.commit()

        # 9. 응답 스키마 반환
        return SendMessageResponse(
            messages=[MessageItem.model_validate(m) for m in new_messages],
        )

    # DELETE /chats/{chat_id}
    def delete_chat(
        self,
        chat_id: UUID,
        user_id: UUID,
    ) -> None:
        chat = self._get_owned_chat(chat_id, user_id, lock=True)
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

        if cursor is not None:
            cursor_message = self.db.get(Message, cursor)
            if cursor_message is None or cursor_message.chat_id != chat_id:
                raise CursorMessageNotFoundError()
            stmt = stmt.where(
                (Message.created_at < cursor_message.created_at)
                | (
                    (Message.created_at == cursor_message.created_at)
                    & (Message.message_id < cursor_message.message_id)
                )
            )

        rows = self.db.scalars(
            stmt.order_by(Message.created_at.desc(), Message.message_id.desc()).limit(
                limit + 1
            )
        ).all()
        has_more = len(rows) > limit
        paged_messages = rows[:limit]
        next_cursor = paged_messages[-1].message_id if has_more else None

        chronological_messages = list(reversed(paged_messages))

        return GetChatResponse(
            chat_id=chat.chat_id,
            chat_title=chat.title,
            current_philosopher_id=chat.current_philosopher_id,
            messages=[
                MessageItem.model_validate(message)
                for message in chronological_messages
            ],
            has_more=has_more,
            next_cursor=next_cursor,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
        )


def get_chat_service(db: DBSession) -> ChatService:
    return ChatService(db=db, llm=llm_service)


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
