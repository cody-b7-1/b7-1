import { useParams } from "react-router";

// 철학자 봇과 대화하는 화면
export function ChatPage() {
  const { philosopherId } = useParams();
  return <main>채팅 (철학자 {philosopherId})</main>;
}
