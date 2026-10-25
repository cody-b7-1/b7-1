// 대화방 데이터: 철학자·대화 목록, 현재 대화의 메시지 불러오기와 메시지 전송

import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";

import {
  ApiError,
  getChat,
  getChatList,
  getPhilosopherList,
  sendMessage,
  startChat,
  type ChatSummary,
  type Message,
  type PhilosopherId,
  type User,
} from "@/lib/api";
import {
  placeholderPhilosopher,
  withDefaults,
  type ResolvedPhilosopher,
} from "@/lib/philosopher";

// 전송 실패 시 상태 코드별 안내 문구 (401은 로그인 화면으로 보냄)
const SEND_ERRORS: Record<number, string> = {
  404: "대화방 또는 철학자를 찾을 수 없어요.",
  409: "이전 질문의 답변을 만드는 중이에요. 잠시 후 다시 보내 주세요.",
  503: "철학자와의 연결이 원활하지 않아요. 잠시 후 다시 시도해 주세요.",
};

const isUnauthorized = (e: unknown) =>
  e instanceof ApiError && e.status === 401;

export function useChat(
  user: User | null,
  chatId: string | undefined,
  startPhilosopherId: PhilosopherId | undefined,
) {
  const navigate = useNavigate();
  const [philosophers, setPhilosophers] = useState<ResolvedPhilosopher[]>([]);
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [current, setCurrent] = useState(startPhilosopherId);
  // 화면에 보이는 messages가 어느 대화의 것인지. chatId와 다르면 불러오는 중
  const [loadedChatId, setLoadedChatId] = useState<string>();
  const [loadError, setLoadError] = useState<"" | "notFound" | "failed">("");
  const [waiting, setWaiting] = useState(false);
  // 응답을 기다리는 사이 다른 대화로 옮겼는지 확인하는 용도
  const chatIdRef = useRef(chatId);

  // 대화가 바뀌면 이전 대화의 화면 상태를 렌더링 중에 바로 초기화
  const [shownFor, setShownFor] = useState({ chatId, startPhilosopherId });
  if (
    shownFor.chatId !== chatId ||
    shownFor.startPhilosopherId !== startPhilosopherId
  ) {
    setShownFor({ chatId, startPhilosopherId });
    setLoadError("");
    if (!chatId) {
      setMessages([]);
      setCurrent(startPhilosopherId);
    }
  }

  const philosopherOf = (id: PhilosopherId | null) =>
    philosophers.find((p) => p.id === id) ??
    // 목록에 없는(비활성화된) 철학자의 메시지도 그릴 수 있도록 기본값으로 채움
    placeholderPhilosopher(id ?? 0, "알 수 없는 철학자");
  const currentInfo =
    philosophers.find((p) => p.id === current) ?? philosophers[0];
  const others = philosophers.filter((p) => p.id !== currentInfo?.id);
  const loadChats = () =>
    getChatList()
      .then((page) => setChats(page.items))
      .catch((e) => console.error("대화 목록 조회 중 오류 발생:", e));

  useEffect(() => {
    if (!user) return;
    getPhilosopherList()
      .then((list) => setPhilosophers(list.map(withDefaults)))
      .catch(() => setLoadError("failed"));
    void loadChats();
  }, [user]);

  useEffect(() => {
    chatIdRef.current = chatId;
    if (!user || !chatId) return;
    let ignore = false;
    getChat(chatId)
      .then((chat) => {
        if (ignore) return;
        setMessages(chat.messages);
        setCurrent(chat.currentPhilosopherId);
        setLoadedChatId(chatId);
      })
      .catch((e) => {
        if (ignore) return;
        if (isUnauthorized(e)) return navigate("/login");
        // 잘못된 형식의 ID는 백엔드가 422로 응답하므로 없는 대화와 같게 처리
        const notFound =
          e instanceof ApiError && (e.status === 404 || e.status === 422);
        setLoadError(notFound ? "notFound" : "failed");
      });
    return () => {
      ignore = true;
    };
  }, [chatId, user, navigate]);

  // 실패하면 입력창에 보여줄 안내 문구를 돌려줌
  async function send(prompt: string): Promise<string | undefined> {
    if (waiting || !currentInfo) return;
    const body = { philosopherId: currentInfo.id, prompt };
    const sentFrom = chatId;
    // 응답이 오기 전까지 사용자 메시지를 먼저 보여줌
    const pending: Message = {
      messageId: "pending",
      senderRole: "USER",
      philosopherId: null,
      content: prompt,
      createdAt: new Date().toISOString(),
    };
    setMessages((m) => [...m, pending]);
    setWaiting(true);
    try {
      if (sentFrom) {
        const res = await sendMessage(sentFrom, body);
        if (chatIdRef.current !== sentFrom) return;
        setMessages((m) => [
          ...m.filter((x) => x !== pending),
          ...res.messages,
        ]);
      } else {
        const res = await startChat(body);
        if (chatIdRef.current !== sentFrom) return;
        setMessages(res.messages);
        setLoadedChatId(res.chatId);
        navigate(`/chats/${res.chatId}`, { replace: true });
      }
      void loadChats();
    } catch (e) {
      if (isUnauthorized(e)) {
        void navigate("/login");
        return;
      }
      if (chatIdRef.current !== sentFrom) return;
      setMessages((m) => m.filter((x) => x !== pending));
      return (
        (e instanceof ApiError && SEND_ERRORS[e.status]) ||
        "메시지를 보내지 못했어요. 잠시 후 다시 시도해 주세요."
      );
    } finally {
      setWaiting(false);
    }
  }

  return {
    philosophers,
    chats,
    messages,
    currentInfo,
    others,
    philosopherOf,
    setCurrent,
    loadError,
    loading: !currentInfo || (!!chatId && loadedChatId !== chatId),
    waiting,
    send,
  };
}
