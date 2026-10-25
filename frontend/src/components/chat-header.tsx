import { Menu } from "lucide-react";

import { PhilosopherAvatar } from "@/components/philosopher-avatar";
import { Button } from "@/components/ui/button";
import type { ResolvedPhilosopher } from "@/lib/philosopher";
import { cn } from "@/lib/utils";

type Props = {
  philosopher: ResolvedPhilosopher;
  others: ResolvedPhilosopher[];
  onSwitch: () => void;
  switchDisabled: boolean;
  onOpenSidebar?: () => void;
};

// 현재 철학자 + 전환 버튼 (모바일에서는 메뉴 버튼 및 컴팩트 레이아웃)
export function ChatHeader({
  philosopher,
  others,
  onSwitch,
  switchDisabled,
  onOpenSidebar,
}: Props) {
  return (
    <div className="flex items-center justify-between gap-2 border-b bg-card px-4 py-3 md:px-8 md:py-3.5">
      <div className="flex min-w-0 items-center gap-2.5 sm:gap-3">
        {/* 모바일 대화 목록(사이드바) 열기 버튼 */}
        <Button
          variant="ghost"
          size="icon"
          className="size-9 shrink-0 md:hidden"
          onClick={onOpenSidebar}
          aria-label="대화 목록 열기"
        >
          <Menu className="size-5" />
        </Button>

        <PhilosopherAvatar
          philosopher={philosopher}
          className="size-9 shrink-0 sm:size-11"
          decorative
        />
        <div className="min-w-0">
          <p
            className="truncate text-base font-bold sm:text-lg"
            style={{ color: philosopher.inkColor }}
          >
            {philosopher.name}
          </p>
          <p className="hidden max-w-md truncate text-[13px] text-muted-foreground sm:block">
            {philosopher.introduction}
          </p>
        </div>
      </div>

      <Button
        variant="outline"
        className="h-9 shrink-0 rounded-full border-foreground px-3 text-xs font-semibold sm:h-11 sm:pl-2.5 sm:text-sm"
        onClick={onSwitch}
        disabled={switchDisabled}
      >
        <span className="flex">
          {others.map((p, i) => (
            <PhilosopherAvatar
              key={p.id}
              philosopher={p}
              decorative
              className={cn(
                "size-5 border-2 border-card sm:size-[26px]",
                i > 0 && "-ml-1.5 sm:-ml-2",
              )}
            />
          ))}
        </span>
        <span className="ml-1 sm:ml-1.5">
          <span className="hidden sm:inline">다른 철학자와 </span>이어가기
        </span>
      </Button>
    </div>
  );
}
