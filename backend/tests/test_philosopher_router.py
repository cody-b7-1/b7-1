import os
import unittest
from unittest.mock import Mock

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.philosophers.router import (
    get_philosopher,
    list_philosopher_summaries,
    list_philosophers,
)
from app.philosophers.schemas import (
    PhilosopherDetailResponse,
    PhilosopherSummaryResponse,
)


class PhilosopherRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.detail_item = PhilosopherDetailResponse(
            id=1,
            name="소크라테스",
            description="고대 그리스의 철학자",
            profile_image_url="/images/profile.png",
            introduction="너 자신을 알라",
            icon_image_url="/images/icon.png",
            avatar_color="#E2E8F0",
            ink_color="#1E293B",
            soft_color="#F8FAFC",
        )
        self.summary_item = PhilosopherSummaryResponse(
            id=1,
            name="소크라테스",
            introduction="너 자신을 알라",
            icon_image_url="/images/icon.png",
            avatar_color="#E2E8F0",
        )

    def test_list_philosophers_calls_service(self) -> None:
        service = Mock()
        service.list_philosophers.return_value = [self.detail_item]

        result = list_philosophers(service=service)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[0].description, "고대 그리스의 철학자")
        self.assertEqual(result[0].ink_color, "#1E293B")
        service.list_philosophers.assert_called_once()

    def test_list_philosopher_summaries_calls_service(self) -> None:
        service = Mock()
        service.list_philosopher_summaries.return_value = [self.summary_item]

        result = list_philosopher_summaries(service=service)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[0].name, "소크라테스")
        self.assertEqual(result[0].introduction, "너 자신을 알라")
        self.assertEqual(result[0].icon_image_url, "/images/icon.png")
        self.assertEqual(result[0].avatar_color, "#E2E8F0")
        service.list_philosopher_summaries.assert_called_once()

    def test_get_philosopher_calls_service(self) -> None:
        service = Mock()
        service.get_philosopher.return_value = self.detail_item

        result = get_philosopher(philosopher_id=1, service=service)

        self.assertEqual(result.id, 1)
        self.assertEqual(result.name, "소크라테스")
        service.get_philosopher.assert_called_once_with(1)

    def test_detail_response_serializes_to_camel_case(self) -> None:
        serialized = self.detail_item.model_dump(by_alias=True)

        self.assertEqual(
            serialized,
            {
                "id": 1,
                "name": "소크라테스",
                "description": "고대 그리스의 철학자",
                "profileImageUrl": "/images/profile.png",
                "introduction": "너 자신을 알라",
                "iconImageUrl": "/images/icon.png",
                "avatarColor": "#E2E8F0",
                "inkColor": "#1E293B",
                "softColor": "#F8FAFC",
            },
        )

    def test_summary_response_serializes_to_camel_case(self) -> None:
        serialized = self.summary_item.model_dump(by_alias=True)

        self.assertEqual(
            serialized,
            {
                "id": 1,
                "name": "소크라테스",
                "introduction": "너 자신을 알라",
                "iconImageUrl": "/images/icon.png",
                "avatarColor": "#E2E8F0",
            },
        )


if __name__ == "__main__":
    unittest.main()
