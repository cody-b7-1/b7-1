// 대화방 데이터: 철학자·대화 목록, 현재 대화의 메시지 불러오기와 메시지 전송, 삭제 및 페이징

import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";

import {
  ApiError,
  deleteChat as apiDeleteChat,
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

type CursorPageState<T> = {
  items: T[];
  hasMore: boolean;
  nextCursor: string | null;
  loadingMore: boolean;
};

const emptyPageState = <T,>(): CursorPageState<T> => ({
  items: [],
  hasMore: false,
  nextCursor: null,
  loadingMore: false,
});

export function useChat(
  user: User | null,
  chatId: string | undefined,
  startPhilosopherId: PhilosopherId | undefined,
) {
  const navigate = useNavigate();
  const [philosophers, setPhilosophers] = useState<ResolvedPhilosopher[]>([]);
  const [chatPage, setChatPage] = useState<CursorPageState<ChatSummary>>(
    emptyPageState,
  );
  const [messagePage, setMessagePage] = useState<CursorPageState<Message>>(
    emptyPageState,
  );

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
      setMessagePage(emptyPageState());
      setCurrent(startPhilosopherId);
    } else {
      setMessagePage((prev) => ({
        ...prev,
        hasMore: false,
        nextCursor: null,
        loadingMore: false,
      }));
    }
  }

  const philosopherOf = useCallback(
    (id: PhilosopherId | null) =>
      philosophers.find((p) => p.id === id) ??
      // 목록에 없는(비활성화된) 철학자의 메시지도 그릴 수 있도록 기본값으로 채움
      placeholderPhilosopher(id ?? 0, "알 수 없는 철학자"),
    [philosophers],
  );
  const currentInfo =
    philosophers.find((p) => p.id === current) ?? philosophers[0];
  const others = philosophers.filter((p) => p.id !== currentInfo?.id);

  const loadChats = useCallback(
    () =>
      getChatList()
        .then((page) => {
          setChatPage({
            items: page.items,
            hasMore: page.hasMore,
            nextCursor: page.nextCursor,
            loadingMore: false,
          });
        })
        .catch((e) => {
          if (isUnauthorized(e)) {
            void navigate("/login");
            return;
          }
          console.error("대화 목록 조회 중 오류 발생:", e);
        }),
    [navigate],
  );

  const {
    hasMore: hasMoreChats,
    nextCursor: nextChatCursor,
    loadingMore: loadingMoreChats,
  } = chatPage;

  const loadMoreChats = useCallback(async () => {
    if (!hasMoreChats || !nextChatCursor || loadingMoreChats) return;
    setChatPage((prev) => ({ ...prev, loadingMore: true }));
    try {
      const page = await getChatList({ cursor: nextChatCursor });
      setChatPage((prev) => ({
        items: [...prev.items, ...page.items],
        hasMore: page.hasMore,
        nextCursor: page.nextCursor,
        loadingMore: false,
      }));
    } catch (e) {
      if (isUnauthorized(e)) {
        void navigate("/login");
        return;
      }
      console.error("이전 대화 목록 추가 조회 중 오류 발생:", e);
      setChatPage((prev) => ({ ...prev, loadingMore: false }));
    }
  }, [hasMoreChats, nextChatCursor, loadingMoreChats, navigate]);

  useEffect(() => {
    if (!user) return;
    getPhilosopherList()
      .then((list) => setPhilosophers(list.map(withDefaults)))
      .catch(() => setLoadError("failed"));
    void loadChats();
  }, [user, loadChats]);

  useEffect(() => {
    chatIdRef.current = chatId;
    if (!user || !chatId) return;
    let ignore = false;
    getChat(chatId)
      .then((chat) => {
        if (ignore) return;
        setMessagePage({
          items: chat.messages,
          hasMore: chat.hasMore,
          nextCursor: chat.nextCursor,
          loadingMore: false,
        });
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

  const {
    hasMore: hasMoreMessages,
    nextCursor: nextMessageCursor,
    loadingMore: loadingMoreMessages,
  } = messagePage;

  const loadMoreMessages = useCallback(async () => {
    if (!chatId || !hasMoreMessages || !nextMessageCursor || loadingMoreMessages)
      return;
    setMessagePage((prev) => ({ ...prev, loadingMore: true }));
    try {
      const chat = await getChat(chatId, { cursor: nextMessageCursor });
      if (chatIdRef.current !== chatId) return;
      // 이전 메시지를 앞쪽에 추가 (시간 오름차순 유지)
      setMessagePage((prev) => ({
        items: [...chat.messages, ...prev.items],
        hasMore: chat.hasMore,
        nextCursor: chat.nextCursor,
        loadingMore: false,
      }));
    } catch (e) {
      if (isUnauthorized(e)) {
        void navigate("/login");
        return;
      }
      console.error("이전 메시지 추가 조회 중 오류 발생:", e);
      setMessagePage((prev) => ({ ...prev, loadingMore: false }));
    }
  }, [chatId, hasMoreMessages, nextMessageCursor, loadingMoreMessages, navigate]);

  const removeChat = useCallback(
    async (targetChatId: string) => {
      try {
        await apiDeleteChat(targetChatId);
        setChatPage((prev) => ({
          ...prev,
          items: prev.items.filter((c) => c.chatId !== targetChatId),
        }));
        // 현재 열려있는 대화를 삭제한 경우 새 대화(/chats/new) 페이지로 이동
        if (chatId === targetChatId) {
          navigate("/chats/new", { replace: true });
        }
      } catch (e) {
        if (isUnauthorized(e)) {
          void navigate("/login");
          return;
        }
        console.error("대화 삭제 중 오류 발생:", e);
        alert("대화를 삭제하지 못했습니다. 잠시 후 다시 시도해 주세요.");
      }
    },
    [chatId, navigate],
  );

  // 실패하면 입력창에 보여줄 안내 문구를 돌려줌
  const send = useCallback(
    async (prompt: string): Promise<string | undefined> => {
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
      setMessagePage((prev) => ({
        ...prev,
        items: [...prev.items, pending],
      }));
      setWaiting(true);
      try {
        if (sentFrom) {
          const res = await sendMessage(sentFrom, body);
          if (chatIdRef.current !== sentFrom) return;
          setMessagePage((prev) => ({
            ...prev,
            items: [
              ...prev.items.filter((x) => x !== pending),
              ...res.messages,
            ],
          }));
        } else {
          const res = await startChat(body);
          if (chatIdRef.current !== sentFrom) return;
          setMessagePage({
            items: res.messages,
            hasMore: false,
            nextCursor: null,
            loadingMore: false,
          });
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
        setMessagePage((prev) => ({
          ...prev,
          items: prev.items.filter((x) => x !== pending),
        }));
        return (
          (e instanceof ApiError && SEND_ERRORS[e.status]) ||
          "메시지를 보내지 못했어요. 잠시 후 다시 시도해 주세요."
        );
      } finally {
        setWaiting(false);
      }
    },
    [waiting, currentInfo, chatId, navigate, loadChats],
  );

  return {
    philosophers,
    chats: chatPage.items,
    hasMoreChats,
    loadingMoreChats,
    loadMoreChats,
    messages: messagePage.items,
    hasMoreMessages,
    loadingMoreMessages,
    loadMoreMessages,
    removeChat,
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
