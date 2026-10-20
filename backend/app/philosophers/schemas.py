from pydantic import Field

from app.core.schemas import CamelResponseModel


class PhilosopherListItem(CamelResponseModel):
    id: int = Field(
        alias="philosopher_id",
        serialization_alias="id",
        description="철학자 ID",
        examples=[1],
    )
    name: str = Field(
        description="철학자 이름",
        examples=["소크라테스"],
    )
    description: str | None = Field(
        default=None,
        description="철학자 설명",
        examples=["고대 그리스의 철학자로 질문을 통해 지혜를 탐구했습니다."],
    )
    profile_image_url: str | None = Field(
        default=None,
        description="프로필 이미지 URL",
        examples=["/images/philosophers/1/profile.png"],
    )


class PhilosopherDetailResponse(PhilosopherListItem):
    introduction: str | None = Field(
        default=None,
        description="철학자 소개 문구",
        examples=["너 자신을 알라"],
    )
    icon_image_url: str | None = Field(
        default=None,
        description="아이콘 URL",
        examples=["/images/philosophers/1/icon.png"],
    )
    avatar_color: str | None = Field(
        default=None,
        description="아바타 배경 색상",
        examples=["#E2E8F0"],
    )
    ink_color: str | None = Field(
        default=None,
        description="글자 색상",
        examples=["#1E293B"],
    )
    soft_color: str | None = Field(
        default=None,
        description="배경 색상",
        examples=["#F8FAFC"],
    )
