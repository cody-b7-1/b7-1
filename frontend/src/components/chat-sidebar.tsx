import { Plus } from "lucide-react";
import { Link } from "react-router";

import { PhilosopherAvatar } from "@/components/philosopher-avatar";
import { Button } from "@/components/ui/button";
import type { ChatSummary, PhilosopherId } from "@/lib/api";
import type { ResolvedPhilosopher } from "@/lib/philosopher";
import { cn } from "@/lib/utils";

type Props = {
  chats: ChatSummary[];
  activeChatId?: string;
  philosopherOf: (id: PhilosopherId | null) => ResolvedPhilosopher;
  onNewChat: () => void;
  newChatDisabled: boolean;
};

// 새 대화 버튼 + 지난 대화 목록
export function ChatSidebar({
  chats,
  activeChatId,
  philosopherOf,
  onNewChat,
  newChatDisabled,
}: Props) {
  return (
    <aside className="flex max-h-48 shrink-0 flex-col gap-1.5 overflow-y-auto border-b bg-card px-4 py-5 md:max-h-none md:w-72 md:border-r md:border-b-0">
      <Button
        className="mb-3 h-11 rounded-xl text-[15px] font-semibold"
        onClick={onNewChat}
        disabled={newChatDisabled}
      >
        <Plus /> 새 대화
      </Button>
      <p className="px-2 py-1 text-xs font-semibold text-muted-foreground">
        지난 대화
      </p>
      {chats.map((c) => {
        const active = c.chatId === activeChatId;
        const info = philosopherOf(c.currentPhilosopherId);
        return (
          <Link
            key={c.chatId}
            to={`/chats/${c.chatId}`}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex items-center gap-2.5 rounded-lg px-2 py-2.5 text-left hover:bg-muted",
              active && "bg-foreground/8 hover:bg-foreground/8",
            )}
          >
            <PhilosopherAvatar
              philosopher={info}
              className="size-7"
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
              <span className="text-xs text-muted-foreground">{info.name}</span>
            </span>
          </Link>
        );
      })}
    </aside>
  );
}
