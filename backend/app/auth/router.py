from datetime import timedelta
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Response,
    status,
)

from app.auth.dependencies import (
    CurrentUser,
    get_optional_refresh_token,
    get_required_refresh_token,
)
from app.auth.email import deliver_email_verification_email
from app.auth.schemas import (
    CurrentUserResponse,
    EmailSendRequest,
    EmailVerifyRequest,
    LoginRequest,
    SignUpRequest,
    SignUpResponse,
)
from app.auth.security import RefreshTokenPayload
from app.auth.service import (
    EmailAlreadyRegisteredError,
    EmailNotFoundError,
    EmailNotVerifiedError,
    InvalidEmailVerificationTokenError,
    InvalidRefreshTokenError,
    PasswordMismatchError,
    create_email_verification,
    create_user,
    login_user,
    revoke_refresh_token,
    rotate_refresh_token,
    verify_email_verification_token,
)
from app.core.config import settings
from app.db.session import DBSession

router = APIRouter(prefix="/auth", tags=["인증"])


def _set_token_cookies(
    response: Response, access_token: str, refresh_token: str
) -> None:
    access_token_max_age = int(
        timedelta(days=settings.jwt_access_token_expire_days).total_seconds()
    )
    refresh_token_max_age = int(
        timedelta(days=settings.jwt_refresh_token_expire_days).total_seconds()
    )
    response.set_cookie(
        key="accessToken",
        value=access_token,
        max_age=access_token_max_age,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api",
    )
    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        max_age=refresh_token_max_age,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api/auth",
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="내 정보 조회",
    description="액세스 토큰으로 인증된 사용자의 이메일 주소와 닉네임을 반환합니다.",
    responses={
        status.HTTP_200_OK: {
            "description": "현재 로그인한 사용자 정보를 반환합니다.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "액세스 토큰이 누락되었거나 유효하지 않거나 만료되었습니다.",
        },
    },
)
def get_me(
    current_user: CurrentUser,
) -> CurrentUserResponse:
    return CurrentUserResponse(
        email=current_user.email,
        nickname=current_user.nickname,
    )


@router.post(
    "/sign-up",
    status_code=status.HTTP_201_CREATED,
    response_model=SignUpResponse,
    summary="회원가입",
    description=(
        "이메일 주소와 비밀번호로 계정을 생성하고 생성된 사용자의 이메일 주소와 "
        "닉네임을 반환합니다. 인증 메일은 응답 후 백그라운드에서 전송하며, SMTP "
        "전송 실패는 로그로 기록되고 이미 생성된 회원가입 응답에는 영향을 주지 않습니다."
    ),
    responses={
        status.HTTP_201_CREATED: {
            "description": (
                "회원가입에 성공하여 생성된 사용자 정보를 반환하고 인증 메일 전송을 "
                "예약했습니다. 이후 SMTP 전송 실패 여부와 관계없이 이 응답을 유지합니다."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "description": "삭제되지 않은 계정에 이미 등록된 이메일 주소입니다.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": (
                "필수 요청 값이 없거나 이메일 형식 또는 필드 값이 올바르지 않습니다. "
                "첫 오류 요약은 detail에, 모든 오류는 errors 배열에 반환합니다."
            ),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "회원가입 처리 중 서버 오류가 발생했습니다.",
        },
    },
)
def sign_up(
    request: SignUpRequest,
    background_tasks: BackgroundTasks,
    db: DBSession,
) -> SignUpResponse:
    try:
        user = create_user(db, request)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 등록된 이메일 주소입니다.",
        ) from None

    return SignUpResponse(email=user.email, nickname=user.nickname)


@router.post(
    "/login",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
    summary="로그인",
    description=(
        "이메일 주소와 비밀번호로 로그인하고, HTTP 전용(HttpOnly) accessToken 및 "
        "refreshToken 쿠키를 설정합니다. 응답 본문은 반환하지 않습니다."
    ),
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "로그인에 성공했습니다. accessToken 및 refreshToken 쿠키를 설정합니다.",
            "headers": {
                "Set-Cookie": {
                    "description": (
                        "accessToken 쿠키는 HTTP 전용(HttpOnly), 보안(Secure), SameSite=Lax, "
                        "Path=/api 속성을, refreshToken 쿠키는 같은 속성과 Path=/api/auth "
                        "속성을 가집니다. 각 쿠키는 "
                        "별도의 Set-Cookie 헤더로 반환합니다."
                    ),
                    "schema": {"type": "string"},
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "이메일 주소 또는 비밀번호가 일치하지 않습니다.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "이메일 인증이 완료되지 않은 계정입니다.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "요청 값이 올바르지 않거나 누락되었습니다.",
        },
    },
)
def login(
    request: LoginRequest,
    response: Response,
    db: DBSession,
) -> None:
    try:
        access_token, refresh_token = login_user(db, request)
    except (EmailNotFoundError, PasswordMismatchError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 주소 또는 비밀번호가 일치하지 않습니다.",  # 어떤 내용이 틀렸는지 명확히 알려주지 않음
        ) from None
    except EmailNotVerifiedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이메일 인증이 완료되지 않은 계정입니다.",
        ) from None

    _set_token_cookies(response, access_token, refresh_token)


@router.post(
    "/email/send",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=None,
    response_class=Response,
    summary="이메일 인증 링크 발송",
    description=(
        "이메일 인증 링크 발송 요청을 접수합니다. 계정 존재 여부나 기존 인증 여부와 관계없이 "
        "동일한 응답을 반환합니다. 메일은 응답 후 백그라운드에서 전송하며, SMTP 전송 "
        "실패는 로그로 기록되고 접수 응답에는 영향을 주지 않습니다."
    ),
    responses={
        status.HTTP_202_ACCEPTED: {
            "description": (
                "이메일 인증 링크 발송 요청을 접수했습니다. 이후 SMTP 전송 실패 여부와 "
                "관계없이 이 응답을 유지합니다."
            ),
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "이메일이 누락되었거나 형식이 올바르지 않습니다.",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "이메일 인증 링크 발송 요청 한도를 초과했습니다.",
        },
    },
)
def send_email_verification_link(
    request: EmailSendRequest, background_tasks: BackgroundTasks, db: DBSession
) -> None:

    result = create_email_verification(db, str(request.email))

    if result is None:
        return

    email, token = result

    background_tasks.add_task(
        deliver_email_verification_email,
        email,
        token,
    )


@router.post(
    "/email/verify",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
    summary="이메일 인증 토큰 검증",
    description=(
        "프런트엔드가 인증 링크에 포함된 토큰을 요청 본문으로 전송하면 해당 토큰을 "
        "검증합니다. 인증 성공 시 해당 사용자의 이메일 인증 토큰을 모두 무효화하여 "
        "재사용할 수 없게 합니다."
    ),
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": (
                "이메일 인증에 성공했으며 해당 사용자의 모든 이메일 인증 토큰을 "
                "무효화했습니다."
            ),
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "토큰이 올바르지 않거나 만료·사용·무효화되었습니다.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "토큰이 누락되었거나 타입이 올바르지 않습니다.",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "이메일 인증 요청 한도를 초과했습니다.",
        },
    },
)
def verify_email_link_token(request: EmailVerifyRequest, db: DBSession) -> None:
    """Consume an email verification token and mark the account as verified."""
    try:
        # 토큰 검증
        verify_email_verification_token(db, request.token)
    except InvalidEmailVerificationTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="토큰이 올바르지 않거나 만료·사용·무효화되었습니다.",
        ) from None


@router.post(
    "/refresh",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
    summary="액세스 토큰 갱신",
    description=(
        "HTTP 전용(HttpOnly) refreshToken 쿠키로 accessToken과 refreshToken을 갱신합니다. "
        "갱신된 토큰은 쿠키로 설정하며 응답 본문은 반환하지 않습니다. 이 엔드포인트는 액세스 "
        "토큰이 필요하지 않으며, refreshToken 쿠키가 없거나 만료·위조된 경우 401을 "
        "반환합니다. 서로 다른 origin인 경우 프런트엔드 요청에는 credentials: 'include'가 "
        "필요합니다."
    ),
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "accessToken 및 refreshToken 갱신에 성공했습니다.",
            "headers": {
                "Set-Cookie": {
                    "description": (
                        "accessToken 쿠키는 HTTP 전용(HttpOnly), 보안(Secure), SameSite=Lax, "
                        "Path=/api 속성을, refreshToken 쿠키는 같은 속성과 Path=/api/auth "
                        "속성을 가집니다. 각 쿠키는 "
                        "별도의 Set-Cookie 헤더로 반환합니다."
                    ),
                    "schema": {"type": "string"},
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "리프레시 토큰이 누락·만료·위조·무효화되었거나 재사용되었습니다.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": (
                "계정을 사용할 수 없거나 CSRF 또는 Origin 검증에 실패한 경우의 "
                "응답입니다. 현재는 구현되지 않았습니다."
            ),
        },
    },
)
def refresh_access_token(
    response: Response,
    db: DBSession,
    refresh_token: Annotated[
        tuple[RefreshTokenPayload, str], Depends(get_required_refresh_token)
    ],
) -> None:
    payload, original_token = refresh_token
    try:
        access_token, new_refresh_token = rotate_refresh_token(
            db, payload, original_token
        )
    except InvalidRefreshTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않거나 이미 사용된 리프레시 토큰입니다.",
        ) from None

    _set_token_cookies(response, access_token, new_refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
    summary="로그아웃",
    description=(
        "accessToken 및 refreshToken 쿠키를 모두 만료 처리합니다. 쿠키가 없거나 만료되어도 "
        "204를 반환하며, 서로 다른 origin인 경우 프런트엔드 요청에는 credentials: 'include'가 필요합니다. "
        "refreshToken이 있으면 서버에서도 무효화합니다. "
        "403 Origin/CSRF 검증과 429 요청 횟수 제한은 아직 구현되지 않았습니다."
    ),
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "이미 로그아웃된 경우를 포함해 로그아웃에 성공했습니다.",
            "headers": {
                "Set-Cookie": {
                    "description": (
                        "accessToken(Path=/api) 및 refreshToken(Path=/api/auth) HTTP 전용 "
                        "쿠키를 각각 별도의 Set-Cookie 헤더로 만료 처리합니다."
                    ),
                    "schema": {"type": "string"},
                }
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Origin 또는 CSRF 검증에 실패했습니다.",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "로그아웃 요청 한도를 초과했습니다.",
        },
    },
)
def logout(
    response: Response,
    db: DBSession,
    refresh_token: Annotated[
        tuple[RefreshTokenPayload, str] | None,
        Depends(get_optional_refresh_token),
    ],
) -> None:
    # Origin/CSRF 검증(403)과 요청 횟수 제한(429)은 아직 구현되지 않았습니다.

    # refresh 토큰 삭제
    if refresh_token is not None:
        _, original_token = refresh_token
        revoke_refresh_token(db, original_token)

    # 쿠키 삭제
    response.delete_cookie(key="accessToken", path="/api", secure=True, httponly=True)
    response.delete_cookie(
        key="refreshToken", path="/api/auth", secure=True, httponly=True
    )
