import { PhilosopherAvatar } from "@/components/philosopher-avatar";
import { Button } from "@/components/ui/button";
import type { ResolvedPhilosopher } from "@/lib/philosopher";
import { cn } from "@/lib/utils";

type Props = {
  philosopher: ResolvedPhilosopher;
  others: ResolvedPhilosopher[];
  onSwitch: () => void;
  switchDisabled: boolean;
};

// 현재 철학자 + 전환 버튼
export function ChatHeader({
  philosopher,
  others,
  onSwitch,
  switchDisabled,
}: Props) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-b bg-card px-6 py-3.5 md:px-8">
      <div className="flex items-center gap-3">
        <PhilosopherAvatar
          philosopher={philosopher}
          className="size-12"
          decorative
        />
        <div>
          <p
            className="text-lg font-bold"
            style={{ color: philosopher.inkColor }}
          >
            {philosopher.name}
          </p>
          <p className="max-w-md truncate text-[13px] text-muted-foreground">
            {philosopher.introduction}
          </p>
        </div>
      </div>
      <Button
        variant="outline"
        className="h-11 rounded-full pl-2.5 font-medium"
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
                "size-[26px] border-2 border-card",
                i > 0 && "-ml-2",
              )}
            />
          ))}
        </span>
        다른 철학자와 이어가기
      </Button>
    </div>
  );
}
