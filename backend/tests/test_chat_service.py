import os
import unittest
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy.exc import OperationalError

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

import app.db.model_registry  # noqa: F401  (모든 ORM 매퍼 등록)
from app.chats.enums import SenderRole
from app.chats.exceptions import (
    ChatAIUnavailableError,
    ChatBusyError,
    ChatNotFoundError,
    PhilosopherNotFoundError,
)
from app.chats.models.chat import Chat
from app.chats.models.message import Message
from app.chats.schemas import SendMessageRequest, StartChatRequest
from app.chats.service import ChatService
from app.db.mixins import utc_now
from app.philosophers.models.philosopher import Philosopher


class FakeScalars:
    def __init__(self, items: list) -> None:
        self._items = items

    def all(self) -> list:
        return self._items


class FakeLLMService:
    def __init__(
        self,
        answer: str = "철학자의 답변입니다.",
        token_count: int | None = 15,
        fail: bool = False,
    ) -> None:
        self.answer = answer
        self.token_count = token_count
        self.fail = fail
        self.last_prompt: str | None = None
        self.last_history: list | None = None

    def generate_chat_answer(
        self, prompt: str, philosopher, history=None
    ) -> tuple[str, int | None]:
        if self.fail:
            raise ChatAIUnavailableError()
        self.last_prompt = prompt
        self.last_history = list(history) if history else None
        return f"{philosopher.name}: {self.answer}", self.token_count

    def summarize_chat_title(self, prompt: str) -> str:
        return prompt.strip()[:40]


class FakeSession:
    """ChatService가 사용하는 최소한의 세션 인터페이스만 흉내 냅니다."""

    def __init__(self, objects: dict | None = None) -> None:
        self.objects = objects or {}
        self.added: list = []
        self.commit_calls = 0
        self.refresh_error: Exception | None = None
        self.locked: list = []

    def get(self, model, key):
        return self.objects.get((model, key))

    def add_all(self, items) -> None:
        self.added.extend(items)

    def refresh(self, instance, with_for_update=None) -> None:
        if self.refresh_error is not None:
            raise self.refresh_error
        if with_for_update:
            self.locked.append(instance)

    def commit(self) -> None:
        self.commit_calls += 1

    def scalars(self, stmt):
        return FakeScalars([])


def make_philosopher(
    philosopher_id: int,
    name: str,
    prompt: str = "",
    is_active: bool = True,
):
    return SimpleNamespace(
        philosopher_id=philosopher_id,
        name=name,
        prompt=prompt,
        is_active=is_active,
    )


def make_chat(user_id, philosopher_id: int, deleted: bool = False) -> Chat:
    now = utc_now()
    return Chat(
        chat_id=uuid4(),
        user_id=user_id,
        current_philosopher_id=philosopher_id,
        title="제목",
        created_at=now,
        updated_at=now,
        deleted_at=now if deleted else None,
    )


class ChatServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.user_id = uuid4()
        self.erasmus = make_philosopher(1, "에라스무스")
        self.nietzsche = make_philosopher(3, "니체")
        self.db = FakeSession(
            {
                (Philosopher, 1): self.erasmus,
                (Philosopher, 3): self.nietzsche,
                (Philosopher, 4): make_philosopher(4, "비활성", is_active=False),
            }
        )
        self.llm = FakeLLMService()
        self.service = ChatService(self.db, llm=self.llm)  # type: ignore[arg-type]

    def _register_chat(self, chat: Chat) -> None:
        self.db.objects[(Chat, chat.chat_id)] = chat

    def test_start_chat_creates_chat_with_user_and_philosopher_messages(self) -> None:
        request = StartChatRequest(prompt="질문 내용", philosopher_id=1)

        response = self.service.start_chat(request, user_id=self.user_id)

        self.db.get(Chat, response.chat_id)
        self.assertEqual(len(response.messages), 2)
        self.assertEqual(
            [m.sender_role for m in response.messages],
            [SenderRole.USER, SenderRole.PHILOSOPHER],
        )
        self.assertEqual(self.db.commit_calls, 1)
        self.assertLess(
            response.messages[0].created_at, response.messages[1].created_at
        )
        # 생성된 assistant 메시지 모델에 token_count 기록 확인
        added_assistant = next(
            item
            for item in self.db.added
            if isinstance(item, Message) and item.sender_role == SenderRole.PHILOSOPHER
        )
        self.assertEqual(added_assistant.token_count, 15)

    def test_start_chat_rejects_inactive_or_missing_philosopher(self) -> None:
        for philosopher_id in (4, 999):
            with (
                self.subTest(philosopher_id=philosopher_id),
                self.assertRaises(PhilosopherNotFoundError),
            ):
                request = StartChatRequest(prompt="질문", philosopher_id=philosopher_id)
                self.service.start_chat(request, user_id=self.user_id)

        self.assertEqual(self.db.commit_calls, 0)

    def test_start_chat_raises_ai_unavailable_when_llm_fails(self) -> None:
        self.llm.fail = True
        request = StartChatRequest(prompt="질문", philosopher_id=1)

        with self.assertRaises(ChatAIUnavailableError):
            self.service.start_chat(request, user_id=self.user_id)

        self.assertEqual(self.db.commit_calls, 0)

    def test_send_message_with_same_philosopher_adds_two_messages(self) -> None:
        chat = make_chat(self.user_id, philosopher_id=1)
        self._register_chat(chat)
        request = SendMessageRequest(prompt="질문", philosopher_id=1)

        response = self.service.send_message(chat.chat_id, request, self.user_id)

        self.assertEqual(
            [m.sender_role for m in response.messages],
            [SenderRole.USER, SenderRole.PHILOSOPHER],
        )
        self.assertEqual(self.db.commit_calls, 1)
        added_assistant = next(
            item
            for item in self.db.added
            if isinstance(item, Message) and item.sender_role == SenderRole.PHILOSOPHER
        )
        self.assertEqual(added_assistant.token_count, 15)

    def test_send_message_with_new_philosopher_adds_system_message_first(self) -> None:
        chat = make_chat(self.user_id, philosopher_id=1)
        self._register_chat(chat)
        request = SendMessageRequest(prompt="새 질문", philosopher_id=3)

        response = self.service.send_message(chat.chat_id, request, self.user_id)

        self.assertEqual(
            [m.sender_role for m in response.messages],
            [SenderRole.SYSTEM, SenderRole.USER, SenderRole.PHILOSOPHER],
        )
        self.assertEqual(response.messages[0].philosopher_id, 3)
        self.assertIn("니체", response.messages[0].content)
        self.assertEqual(chat.current_philosopher_id, 3)
        created = [m.created_at for m in response.messages]
        self.assertEqual(created, sorted(created))
        self.assertEqual(len(set(created)), 3)

    def test_send_message_raises_ai_unavailable_when_llm_fails(self) -> None:
        chat = make_chat(self.user_id, philosopher_id=1)
        self._register_chat(chat)
        self.llm.fail = True
        request = SendMessageRequest(prompt="질문", philosopher_id=3)

        with self.assertRaises(ChatAIUnavailableError):
            self.service.send_message(chat.chat_id, request, self.user_id)

        self.assertEqual(self.db.commit_calls, 0)
        # 실패 시 철학자 변경도 커밋되지 않아야 함
        self.assertEqual(chat.current_philosopher_id, 1)

    def test_chat_access_is_hidden_for_other_users_and_deleted_chats(self) -> None:
        other_users_chat = make_chat(uuid4(), philosopher_id=1)
        deleted_chat = make_chat(self.user_id, philosopher_id=1, deleted=True)
        self._register_chat(other_users_chat)
        self._register_chat(deleted_chat)
        request = SendMessageRequest(prompt="침입", philosopher_id=1)

        for chat_id in (other_users_chat.chat_id, deleted_chat.chat_id, uuid4()):
            with (
                self.subTest(chat_id=chat_id),
                self.assertRaises(ChatNotFoundError),
            ):
                self.service.send_message(chat_id, request, self.user_id)

    def test_delete_chat_marks_chat_as_soft_deleted(self) -> None:
        chat = make_chat(self.user_id, philosopher_id=1)
        self._register_chat(chat)

        self.service.delete_chat(chat.chat_id, self.user_id)

        self.assertIsNotNone(chat.deleted_at)
        self.assertEqual(self.db.commit_calls, 1)

    def test_send_message_locks_chat_before_processing(self) -> None:
        chat = make_chat(self.user_id, philosopher_id=1)
        self._register_chat(chat)
        request = SendMessageRequest(prompt="질문", philosopher_id=1)

        self.service.send_message(chat.chat_id, request, self.user_id)

        self.assertIn(chat, self.db.locked)

    def test_send_message_and_delete_fail_fast_when_chat_is_busy(self) -> None:
        cases = [
            (
                "send_message",
                lambda c: self.service.send_message(
                    c.chat_id,
                    SendMessageRequest(prompt="질문", philosopher_id=1),
                    self.user_id,
                ),
            ),
            (
                "delete_chat",
                lambda c: self.service.delete_chat(c.chat_id, self.user_id),
            ),
        ]
        for name, action in cases:
            with self.subTest(operation=name):
                chat = make_chat(self.user_id, philosopher_id=1)
                self._register_chat(chat)
                self.db.refresh_error = OperationalError(
                    "SELECT ... FOR UPDATE NOWAIT",
                    {},
                    Exception(1205, "Lock wait timeout exceeded"),
                )
                with self.assertRaises(ChatBusyError):
                    action(chat)

    def test_unrelated_database_errors_are_not_reported_as_busy(self) -> None:
        chat = make_chat(self.user_id, philosopher_id=1)
        self._register_chat(chat)
        self.db.refresh_error = OperationalError(
            "SELECT ...", {}, Exception(2013, "Lost connection to server")
        )
        request = SendMessageRequest(prompt="질문", philosopher_id=1)

        with self.assertRaises(OperationalError):
            self.service.send_message(chat.chat_id, request, self.user_id)

    def test_other_users_chat_is_rejected_before_locking(self) -> None:
        other_users_chat = make_chat(uuid4(), philosopher_id=1)
        self._register_chat(other_users_chat)
        request = SendMessageRequest(prompt="침입", philosopher_id=1)

        with self.assertRaises(ChatNotFoundError):
            self.service.send_message(other_users_chat.chat_id, request, self.user_id)

        self.assertEqual(self.db.locked, [])

    def test_get_chat_returns_chat_response_with_timestamps(self) -> None:
        chat = make_chat(self.user_id, philosopher_id=1)
        self._register_chat(chat)

        response = self.service.get_chat(chat.chat_id, self.user_id)

        self.assertEqual(response.chat_id, chat.chat_id)
        self.assertEqual(response.chat_title, chat.title)
        self.assertEqual(response.current_philosopher_id, chat.current_philosopher_id)
        self.assertEqual(response.created_at, chat.created_at)
        self.assertEqual(response.updated_at, chat.updated_at)
        self.assertFalse(response.has_more)
        self.assertIsNone(response.next_cursor)


if __name__ == "__main__":
    unittest.main()
