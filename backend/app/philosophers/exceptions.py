"""철학자 도메인 전용 예외 클래스 정의."""

from fastapi import status


class PhilosopherDomainError(Exception):
    """철학자 도메인 예외의 기본 클래스."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: str = "철학자 요청을 처리할 수 없습니다."

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class PhilosopherNotFoundError(PhilosopherDomainError):
    """요청한 철학자가 없거나 비활성화 상태일 때 발생한다."""

    status_code: int = status.HTTP_404_NOT_FOUND
    detail: str = "해당 철학자를 찾을 수 없습니다."
