import { useState } from "react";

import { PhilosopherAvatar } from "@/components/philosopher-avatar";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { PhilosopherId } from "@/lib/api";
import type { ResolvedPhilosopher } from "@/lib/philosopher";
import { cn } from "@/lib/utils";

type Props = {
  /** switch: 현재 대화에서 전환, new: 새 대화 시작, null: 닫힘 */
  mode: "switch" | "new" | null;
  philosophers: ResolvedPhilosopher[];
  onClose: () => void;
  onConfirm: (id: PhilosopherId) => void;
};

// 철학자 선택 모달
export function PhilosopherPickDialog({
  mode,
  philosophers,
  onClose,
  onConfirm,
}: Props) {
  const [picked, setPicked] = useState<PhilosopherId | null>(null);

  const close = () => {
    setPicked(null);
    onClose();
  };

  return (
    <Dialog open={mode !== null} onOpenChange={(open) => !open && close()}>
      <DialogContent className="bg-card sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {mode === "new"
              ? "누구와 새 대화를 시작할까요?"
              : "누구와 이어서 이야기할까요?"}
          </DialogTitle>
          <DialogDescription>
            {mode === "new"
              ? "고른 철학자와 새로운 고민을 처음부터 나눠요."
              : "지금까지의 대화는 그대로 남고, 다음 메시지부터 새 철학자가 같은 고민에 이어서 답해요."}
          </DialogDescription>
        </DialogHeader>
        <div
          className="flex flex-col gap-2"
          role="radiogroup"
          aria-label="철학자 선택"
        >
          {philosophers.map((p) => (
            <button
              key={p.id}
              type="button"
              role="radio"
              aria-checked={picked === p.id}
              onClick={() => setPicked(p.id)}
              className={cn(
                "flex items-center gap-3 rounded-xl border p-3 text-left transition-colors hover:bg-muted",
                picked === p.id && "border-2 border-foreground",
              )}
            >
              <PhilosopherAvatar
                philosopher={p}
                className="size-11"
                decorative
              />
              <span className="flex flex-col">
                <span className="font-semibold" style={{ color: p.inkColor }}>
                  {p.name}
                </span>
                <span className="text-[13px] text-muted-foreground">
                  {p.introduction}
                </span>
              </span>
            </button>
          ))}
        </div>
        <DialogFooter>
          <Button
            className="h-11 w-full rounded-xl"
            disabled={!picked}
            onClick={() => {
              if (!picked) return;
              onConfirm(picked);
              close();
            }}
          >
            {mode === "new" ? "이 철학자와 시작하기" : "이 철학자와 이어가기"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
