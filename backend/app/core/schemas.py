from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """코드는 snake_case, API JSON은 camelCase로 변환하는 공통 베이스 (요청 모델용)."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class CamelResponseModel(CamelModel):
    """ORM 객체로부터 변환(from_attributes=True)을 지원하는 응답 전용 베이스."""

    model_config = ConfigDict(
        from_attributes=True,
    )
