import { useParams } from "react-router";

// 백엔드 API 명세에 따른 대화방 화면 (GET /chats/{chatId})
export function ChatPage() {
  const { chatId } = useParams<{ chatId: string }>();
  return <main className="flex-1 p-6">채팅방 (대화 ID: {chatId})</main>;
}
