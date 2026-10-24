import os
import unittest
from types import SimpleNamespace

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.philosophers.exceptions import PhilosopherNotFoundError
from app.philosophers.models.philosopher import Philosopher
from app.philosophers.service import PhilosopherService


class FakeScalars:
    def __init__(self, items: list) -> None:
        self._items = items

    def all(self) -> list:
        return self._items


class FakeSession:
    """PhilosopherService가 사용하는 최소한의 세션 인터페이스를 모킹합니다."""

    def __init__(
        self, objects: dict | None = None, scalar_items: list | None = None
    ) -> None:
        self.objects = objects or {}
        self.scalar_items = scalar_items or []

    def get(self, model, key):
        return self.objects.get((model, key))

    def scalars(self, stmt):
        return FakeScalars(self.scalar_items)


def make_philosopher(
    philosopher_id: int,
    name: str,
    description: str = "설명입니다.",
    profile_image_url: str = "/images/profile.png",
    introduction: str = "소개 문구입니다.",
    icon_image_url: str = "/images/icon.png",
    avatar_color: str = "#C9C35A",
    inkColor: str = "#5A5A10",
    softColor: str = "#F3F2E1",
    is_active: bool = True,
):
    return SimpleNamespace(
        philosopher_id=philosopher_id,
        name=name,
        description=description,
        profile_image_url=profile_image_url,
        introduction=introduction,
        icon_image_url=icon_image_url,
        avatar_color=avatar_color,
        ink_color=inkColor,
        soft_color=softColor,
        is_active=is_active,
    )


class PhilosopherServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.p1 = make_philosopher(1, "에라스무스", is_active=True)
        self.p2 = make_philosopher(2, "쇼펜하우어", is_active=True)
        self.p3 = make_philosopher(3, "니체", is_active=False)

        self.db = FakeSession(
            objects={
                (Philosopher, 1): self.p1,
                (Philosopher, 2): self.p2,
                (Philosopher, 3): self.p3,
            },
            scalar_items=[self.p1, self.p2],  # is_active=True만 DB 쿼리로 조회된 상황
        )
        self.service = PhilosopherService(self.db)  # type: ignore[arg-type]

    def test_list_philosophers_returns_items(self) -> None:
        result = self.service.list_philosophers()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[0].name, "에라스무스")
        self.assertEqual(result[1].id, 2)
        self.assertEqual(result[1].name, "쇼펜하우어")

    def test_get_philosopher_success(self) -> None:
        result = self.service.get_philosopher(1)

        self.assertEqual(result.id, 1)
        self.assertEqual(result.name, "에라스무스")
        self.assertEqual(result.introduction, "소개 문구입니다.")
        self.assertEqual(result.avatar_color, "#C9C35A")

    def test_get_philosopher_raises_when_not_found(self) -> None:
        with self.assertRaises(PhilosopherNotFoundError):
            self.service.get_philosopher(999)

    def test_get_philosopher_raises_when_inactive(self) -> None:
        with self.assertRaises(PhilosopherNotFoundError):
            self.service.get_philosopher(3)


if __name__ == "__main__":
    unittest.main()
