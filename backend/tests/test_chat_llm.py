import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.chats.enums import SenderRole
from app.chats.exceptions import ChatAIUnavailableError
from app.chats.llm import LLMService, _build_system_prompt, _format_chat_history
from app.chats.models.message import Message
from openai import APIConnectionError, APITimeoutError


class LLMServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_client = MagicMock()
        self.llm_service = LLMService(client=self.mock_client)
        self.philosopher = SimpleNamespace(
            philosopher_id=1,
            name="에라스무스",
            prompt="너는 르네상스 인문주의자 에라스무스다.",
        )

    def test_build_system_prompt_includes_common_and_specific(self) -> None:
        prompt = _build_system_prompt(self.philosopher)  # type: ignore[arg-type]
        self.assertIn("《철학자의 방》", prompt)
        self.assertIn("에라스무스", prompt)
        self.assertIn("너는 르네상스 인문주의자 에라스무스다.", prompt)

    def test_format_chat_history_maps_roles_correctly(self) -> None:
        messages = [
            Message(
                sender_role=SenderRole.USER,
                content="안녕하세요",
            ),
            Message(
                sender_role=SenderRole.PHILOSOPHER,
                content="반갑습니다.",
            ),
            Message(
                sender_role=SenderRole.SYSTEM,
                content="대화 상대가 변경되었습니다.",
            ),
        ]

        formatted = _format_chat_history(messages)
        self.assertEqual(len(formatted), 3)
        self.assertEqual(formatted[0], {"role": "user", "content": "안녕하세요"})
        self.assertEqual(formatted[1], {"role": "assistant", "content": "반갑습니다."})
        self.assertEqual(
            formatted[2],
            {"role": "system", "content": "[시스템 안내: 대화 상대가 변경되었습니다.]"},
        )

    def test_generate_chat_answer_success(self) -> None:
        mock_choice = MagicMock()
        mock_choice.message.content = " 삶의 본질에 대해 생각해봅시다. "
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.total_tokens = 42
        self.mock_client.chat.completions.create.return_value = mock_response

        answer, tokens = self.llm_service.generate_chat_answer(
            prompt="인생이란?",
            philosopher=self.philosopher,  # type: ignore[arg-type]
        )

        self.assertEqual(answer, "삶의 본질에 대해 생각해봅시다.")
        self.assertEqual(tokens, 42)

    def test_generate_chat_answer_raises_when_content_empty(self) -> None:
        mock_choice = MagicMock()
        mock_choice.message.content = "   "
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.total_tokens = 10
        self.mock_client.chat.completions.create.return_value = mock_response

        with self.assertRaises(ChatAIUnavailableError):
            self.llm_service.generate_chat_answer(
                prompt="질문",
                philosopher=self.philosopher,  # type: ignore[arg-type]
            )

    def test_generate_chat_answer_raises_when_choices_empty(self) -> None:
        mock_response = MagicMock()
        mock_response.choices = []
        self.mock_client.chat.completions.create.return_value = mock_response

        with self.assertRaises(ChatAIUnavailableError):
            self.llm_service.generate_chat_answer(
                prompt="질문",
                philosopher=self.philosopher,  # type: ignore[arg-type]
            )

    def test_generate_chat_answer_raises_when_api_fails(self) -> None:
        self.mock_client.chat.completions.create.side_effect = APITimeoutError(
            request=MagicMock()
        )

        with self.assertRaises(ChatAIUnavailableError):
            self.llm_service.generate_chat_answer(
                prompt="질문",
                philosopher=self.philosopher,  # type: ignore[arg-type]
            )

    def test_generate_chat_answer_raises_when_connection_fails(self) -> None:
        self.mock_client.chat.completions.create.side_effect = APIConnectionError(
            request=MagicMock()
        )

        with self.assertRaises(ChatAIUnavailableError):
            self.llm_service.generate_chat_answer(
                prompt="질문",
                philosopher=self.philosopher,  # type: ignore[arg-type]
            )

    def test_summarize_chat_title_success(self) -> None:
        mock_choice = MagicMock()
        mock_choice.message.content = ' "행복의 기준에 대한 성찰" '
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        self.mock_client.chat.completions.create.return_value = mock_response

        title = self.llm_service.summarize_chat_title("어떻게 살아야 행복할까요?")

        self.assertEqual(title, "행복의 기준에 대한 성찰")

    def test_summarize_chat_title_falls_back_when_choices_empty(self) -> None:
        mock_response = MagicMock()
        mock_response.choices = []
        self.mock_client.chat.completions.create.return_value = mock_response

        title = self.llm_service.summarize_chat_title("첫 번째 질문 내용입니다.")

        self.assertEqual(title, "첫 번째 질문 내용입니다.")

    def test_summarize_chat_title_falls_back_on_api_error(self) -> None:
        self.mock_client.chat.completions.create.side_effect = APITimeoutError(
            request=MagicMock()
        )

        title = self.llm_service.summarize_chat_title(
            "인생에서 가장 소중한 가치는 무엇일까에 대한 깊은 고민입니다"
        )

        self.assertEqual(
            title, "인생에서 가장 소중한 가치는 무엇일까에 대한 깊은 고민입니다"
        )
