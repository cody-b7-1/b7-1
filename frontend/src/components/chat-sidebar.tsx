import { useState } from "react";
import { Loader2, Plus, Trash2, X } from "lucide-react";
import { Link } from "react-router";

import { PhilosopherAvatar } from "@/components/philosopher-avatar";
import { Button } from "@/components/ui/button";
import type { ChatSummary, PhilosopherId } from "@/lib/api";
import type { ResolvedPhilosopher } from "@/lib/philosopher";
import { cn } from "@/lib/utils";

type Props = {
  chats: ChatSummary[];
  activeChatId?: string;
  hasMoreChats?: boolean;
  loadingMoreChats?: boolean;
  onLoadMoreChats?: () => void;
  onDeleteChat?: (chatId: string) => Promise<void> | void;
  philosopherOf: (id: PhilosopherId | null) => ResolvedPhilosopher;
  onNewChat: () => void;
  newChatDisabled: boolean;
  isOpen?: boolean;
  onClose?: () => void;
};

// 새 대화 버튼 + 지난 대화 목록 (대화 삭제 및 무한 스크롤 더보기 지원)
export function ChatSidebar({
  chats,
  activeChatId,
  hasMoreChats = false,
  loadingMoreChats = false,
  onLoadMoreChats,
  onDeleteChat,
  philosopherOf,
  onNewChat,
  newChatDisabled,
  isOpen = false,
  onClose,
}: Props) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (e: React.MouseEvent, chatId: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("이 대화를 삭제할까요? 삭제된 대화는 복구할 수 없어요.")) {
      return;
    }
    setDeletingId(chatId);
    try {
      await onDeleteChat?.(chatId);
    } finally {
      setDeletingId((prev) => (prev === chatId ? null : prev));
    }
  };

  const content = (
    <div className="flex h-full flex-col gap-1.5 overflow-y-auto px-4 py-5">
      <div className="mb-2 flex items-center justify-between md:hidden">
        <span className="text-sm font-semibold">대화 목록</span>
        <Button
          variant="ghost"
          size="icon"
          className="size-8"
          onClick={onClose}
          aria-label="닫기"
        >
          <X className="size-4" />
        </Button>
      </div>

      <Button
        className="mb-3 h-11 rounded-xl text-[15px] font-semibold"
        onClick={() => {
          onNewChat();
          onClose?.();
        }}
        disabled={newChatDisabled}
      >
        <Plus className="mr-1.5 size-4" /> 새 대화
      </Button>
      <p className="px-2 py-1 text-xs font-semibold text-muted-foreground">
        지난 대화
      </p>
      {chats.length === 0 ? (
        <p className="px-2 py-3 text-xs text-muted-foreground">
          아직 나눈 대화가 없어요.
        </p>
      ) : (
        <div className="flex flex-col gap-1">
          {chats.map((c) => {
            const active = c.chatId === activeChatId;
            const info = philosopherOf(c.currentPhilosopherId);
            return (
              <div
                key={c.chatId}
                className={cn(
                  "group relative flex items-center rounded-lg hover:bg-muted",
                  active && "bg-muted",
                )}
              >
                <Link
                  to={`/chats/${c.chatId}`}
                  aria-current={active ? "page" : undefined}
                  onClick={onClose}
                  className="flex min-w-0 flex-1 items-center gap-2.5 py-2.5 pr-8 pl-2.5 text-left"
                >
                  <PhilosopherAvatar
                    philosopher={info}
                    className="size-7 shrink-0"
                    decorative
                  />
                  <span className="flex min-w-0 flex-col">
                    <span
                      className={cn(
                        "truncate text-sm",
                        active ? "font-semibold" : "font-medium",
                      )}
                    >
                      {c.chatTitle}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {info.name}
                    </span>
                  </span>
                </Link>

                {/* 삭제 버튼: 모바일에선 기본 노출, 데스크톱(md)에선 호버/활성 시 표시 */}
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn(
                    "absolute right-1 size-7 rounded-md text-muted-foreground opacity-70 transition-opacity hover:bg-destructive/10 hover:text-destructive md:opacity-0 md:group-hover:opacity-100",
                    active && "opacity-90 md:opacity-80",
                    deletingId === c.chatId && "opacity-100 md:opacity-100",
                  )}
                  onClick={(e) => void handleDelete(e, c.chatId)}
                  disabled={deletingId === c.chatId}
                  aria-label="대화 삭제"
                >
                  {deletingId === c.chatId ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : (
                    <Trash2 className="size-3.5" />
                  )}
                </Button>
              </div>
            );
          })}

          {/* 대화방 목록 추가 불러오기 버튼 */}
          {hasMoreChats && (
            <Button
              variant="ghost"
              size="sm"
              className="mt-1 h-8 w-full text-xs text-muted-foreground"
              onClick={onLoadMoreChats}
              disabled={loadingMoreChats}
            >
              {loadingMoreChats ? (
                <>
                  <Loader2 className="mr-1.5 size-3 animate-spin" />
                  불러오는 중…
                </>
              ) : (
                "이전 대화 더보기"
              )}
            </Button>
          )}
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* 데스크톱 사이드바 (md 이상) */}
      <aside className="hidden w-72 shrink-0 border-r bg-card md:block">
        {content}
      </aside>

      {/* 모바일 슬라이드 드로어 (md 미만) */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="fixed inset-0 bg-black/50 transition-opacity"
            onClick={onClose}
            aria-hidden="true"
          />
          <aside className="relative z-10 flex h-full w-4/5 max-w-xs flex-col border-r bg-card shadow-xl">
            {content}
          </aside>
        </div>
      )}
    </>
  );
}
