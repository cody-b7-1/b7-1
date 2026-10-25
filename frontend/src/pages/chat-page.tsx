// 대화방 화면 (/chats/new: 새 대화, /chats/{chatId}: 기존 대화)

import { useState } from "react";
import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
  useOutletContext,
  useParams,
} from "react-router";

import { ChatHeader } from "@/components/chat-header";
import { ChatInput } from "@/components/chat-input";
import { ChatMessages } from "@/components/chat-messages";
import { ChatSidebar } from "@/components/chat-sidebar";
import { PhilosopherPickDialog } from "@/components/philosopher-pick-dialog";
import { buttonVariants } from "@/components/ui/button-variants";
import { useChat } from "@/hooks/use-chat";
import type { PhilosopherId, User } from "@/lib/api";

export function ChatPage() {
  const { user } = useOutletContext<{ user: User | null }>();
  const { chatId } = useParams<{ chatId?: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  // 홈에서 고른 철학자. 새로고침 등으로 없으면 목록의 첫 철학자로 시작
  const startPhilosopherId = (
    location.state as { philosopherId?: PhilosopherId } | null
  )?.philosopherId;
  const {
    philosophers,
    chats,
    hasMoreChats,
    loadingMoreChats,
    loadMoreChats,
    messages,
    hasMoreMessages,
    loadingMoreMessages,
    loadMoreMessages,
    removeChat,
    currentInfo,
    others,
    philosopherOf,
    setCurrent,
    loadError,
    loading,
    waiting,
    send,
  } = useChat(user, chatId, startPhilosopherId);
  // 철학자 선택 모달: 현재 대화에서 전환하거나, 새 대화를 시작
  const [dialog, setDialog] = useState<"switch" | "new" | null>(null);
  // 모바일 사이드바 열림 상태
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (!user) return <Navigate to="/login" replace />;

  return (
    <div
      data-chat
      className="flex min-h-0 flex-1 flex-col border-t md:flex-row"
    >
      <ChatSidebar
        chats={chats}
        activeChatId={chatId}
        hasMoreChats={hasMoreChats}
        loadingMoreChats={loadingMoreChats}
        onLoadMoreChats={loadMoreChats}
        onDeleteChat={removeChat}
        philosopherOf={philosopherOf}
        onNewChat={() => setDialog("new")}
        newChatDisabled={philosophers.length === 0}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="flex min-h-0 min-w-0 flex-1 flex-col">
        {loadError === "notFound" ? (
          <div className="m-auto flex flex-col items-center gap-4 px-6 py-20 text-center">
            <h1 className="text-2xl font-bold">대화를 찾을 수 없어요</h1>
            <p className="text-muted-foreground">
              삭제되었거나 주소가 잘못 입력되었을 수 있어요.
            </p>
            <Link
              to="/"
              className={buttonVariants({
                variant: "outline",
                className: "h-11 rounded-full px-6",
              })}
            >
              홈으로 돌아가기
            </Link>
          </div>
        ) : loadError === "failed" ? (
          <p role="alert" className="m-auto px-6 text-center text-destructive">
            대화를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.
          </p>
        ) : loading || !currentInfo ? (
          <p role="status" className="m-auto text-muted-foreground">
            대화를 불러오는 중이에요…
          </p>
        ) : (
          <>
            <h1 className="sr-only">{currentInfo.name}와 나누는 대화</h1>
            <ChatHeader
              philosopher={currentInfo}
              others={others}
              onSwitch={() => setDialog("switch")}
              switchDisabled={waiting || others.length === 0}
              onOpenSidebar={() => setSidebarOpen(true)}
            />
            <ChatMessages
              messages={messages}
              current={currentInfo}
              philosopherOf={philosopherOf}
              waiting={waiting}
              hasMoreMessages={hasMoreMessages}
              loadingMoreMessages={loadingMoreMessages}
              onLoadMoreMessages={loadMoreMessages}
            />
            <ChatInput
              key={chatId}
              philosopherName={currentInfo.name}
              waiting={waiting}
              onSend={send}
            />
          </>
        )}
      </main>

      <PhilosopherPickDialog
        mode={dialog}
        philosophers={dialog === "new" ? philosophers : others}
        onClose={() => setDialog(null)}
        onConfirm={(id) => {
          if (dialog === "new")
            navigate("/chats/new", { state: { philosopherId: id } });
          else setCurrent(id);
        }}
      />
    </div>
  );
}
