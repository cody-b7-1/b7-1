from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from pydantic import UUID4

from app.chats.schemas import (
    ChatListResponse,
    GetChatResponse,
    SendMessageRequest,
    SendMessageResponse,
    StartChatRequest,
    StartChatResponse,
)
from app.chats.service import ChatService

router = APIRouter(prefix="/chats", tags=["채팅"])

ChatServiceDep = Annotated[ChatService, Depends(ChatService)]
ChatIdPath = Annotated[
    UUID4,
    Path(
        description="채팅 ID",
        examples=["00000000-0000-4000-8000-000000000001"],
    ),
]


@router.post(
    "",
    response_model=StartChatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="새 채팅 시작",
    description="선택한 철학자에게 첫 질문을 보내 새로운 채팅방을 생성합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "요청한 철학자를 찾을 수 없거나 비활성화 상태입니다.",
        },
    },
)
def start_chat(
    request: StartChatRequest,
    chat_service: ChatServiceDep,
) -> StartChatResponse:
    return chat_service.start_chat(request)


@router.post(
    "/{chat_id}/messages",
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="채팅 메시지 전송",
    description="기존 채팅방에 사용자 메시지를 보내고 철학자의 답변을 받습니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "채팅방을 찾을 수 없거나, 요청한 철학자를 찾을 수 없습니다.",
        },
    },
)
def send_message(
    chat_id: ChatIdPath,
    request: SendMessageRequest,
    chat_service: ChatServiceDep,
) -> SendMessageResponse:
    pass


@router.get(
    "",
    response_model=ChatListResponse,
    status_code=status.HTTP_200_OK,
    summary="채팅 목록 조회",
    description=(
        "사용자의 채팅방 목록을 최신순으로 조회합니다. "
        "cursor 쿼리 파라미터로 무한 스크롤 페이징을 처리합니다."
    ),
)
def list_chats(
    chat_service: ChatServiceDep,
    limit: Annotated[
        int, Query(ge=1, le=100, description="한 번에 조회할 채팅방 수")
    ] = 20,
    cursor: Annotated[
        UUID4 | None,
        Query(description="다음 대화 목록을 조회하기 위한 커서 (채팅방 ID)"),
    ] = None,
) -> ChatListResponse:
    return chat_service.list_chats(limit=limit, cursor=cursor)


@router.delete(
    "/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="채팅방 삭제",
    description="지정한 채팅방을 삭제합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "해당 채팅방을 찾을 수 없습니다.",
        },
    },
)
def delete_chat(chat_id: ChatIdPath, chat_service: ChatServiceDep) -> None:
    return chat_service.delete_chat(chat_id)


@router.get(
    "/{chat_id}",
    response_model=GetChatResponse,
    status_code=status.HTTP_200_OK,
    summary="채팅 상세 조회",
    description=(
        "채팅방 정보와 메시지 내역을 조회합니다. 기본적으로 최신 메시지 limit개를 "
        "시간 오름차순으로 반환하며, cursor에 이전 메시지 ID를 전달하면 "
        "해당 메시지보다 이전(더 오래된) 메시지를 페이징 조회합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "해당 채팅방 또는 기준 메시지를 찾을 수 없습니다.",
        },
    },
)
def get_chat(
    chat_id: ChatIdPath,
    chat_service: ChatServiceDep,
    limit: Annotated[
        int, Query(ge=1, le=100, description="한 번에 조회할 메시지 수")
    ] = 30,
    cursor: Annotated[
        UUID4 | None,
        Query(
            description="이 메시지 ID보다 이전(더 오래된) 메시지를 조회하기 위한 커서"
        ),
    ] = None,
) -> GetChatResponse:
    return chat_service.get_chat(chat_id, limit=limit, cursor=cursor)
