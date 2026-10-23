import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";

import { PhilosopherAvatar } from "@/components/philosopher-avatar";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { getPhilosopher, type PhilosopherId } from "@/lib/api";
import { withDefaults, type ResolvedPhilosopher } from "@/lib/philosopher";

type Props = {
  philosopherId: PhilosopherId;
  initialPhilosopher?: ResolvedPhilosopher;
  onUpdate?: (updated: ResolvedPhilosopher) => void;
  onClose: () => void;
  onStartChat: (philosopher: ResolvedPhilosopher) => void;
};

export function PhilosopherDetailDialog({
  philosopherId,
  initialPhilosopher,
  onUpdate,
  onClose,
  onStartChat,
}: Props) {
  const [philosopher, setPhilosopher] = useState<ResolvedPhilosopher | null>(
    initialPhilosopher ?? null,
  );
  const [loading, setLoading] = useState(!initialPhilosopher);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    const { signal } = controller;

    setError("");

    async function loadPhilosopher() {
      try {
        const detail = await getPhilosopher(philosopherId, signal);
        if (!signal.aborted) {
          const fresh = withDefaults(detail);
          setPhilosopher(fresh);
          onUpdate?.(fresh);
        }
      } catch {
        if (!signal.aborted) {
          setError("철학자 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.");
          setPhilosopher(null);
        }
      } finally {
        if (!signal.aborted) setLoading(false);
      }
    }

    void loadPhilosopher();
    return () => controller.abort();
  }, [philosopherId, onUpdate]);

  return (
    <Dialog
      open
      onOpenChange={(open) => !open && onClose()}
    >
      <DialogContent animate={false} aria-busy={loading} className="max-h-[92svh] gap-0 overflow-hidden overflow-y-auto border-0 bg-card p-0 sm:max-w-4xl sm:rounded-3xl">
        {loading && (
          <div className="space-y-6 p-8" role="status">
            <DialogTitle>철학자 정보를 불러오는 중입니다.</DialogTitle>
            <div className="grid gap-6 md:grid-cols-2" aria-hidden="true">
              <Skeleton className="aspect-square w-full rounded-xl" />
              <div className="space-y-4">
                <Skeleton className="h-8 w-1/2" />
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-3/4" />
              </div>
            </div>
          </div>
        )}
        {error && (
          <div className="space-y-5 p-8">
            <DialogTitle>철학자 정보를 불러오지 못했습니다.</DialogTitle>
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          </div>
        )}
        {philosopher && (
          <div className="grid md:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
            {/* 왼쪽: 철학자 색으로 물든 패널 + 큰 초상 */}
            <div
              className="relative flex aspect-5/4 items-end justify-center overflow-hidden md:aspect-auto md:min-h-130"
              style={{ backgroundColor: philosopher.softColor }}
            >
              {/* 큰 원 */}
              <div
                className="absolute top-[46%] left-1/2 aspect-square w-[56%] -translate-1/2 rounded-full md:top-[44%] md:w-[78%]"
                style={{ backgroundColor: philosopher.avatarColor }}
                aria-hidden
              />
              {/* 바닥 쪽 은은한 띠: 초상 아래가 비어 보이지 않게 */}
              <div
                className="absolute inset-x-0 bottom-0 h-1/3 opacity-25"
                style={{
                  backgroundImage: `linear-gradient(to top, ${philosopher.avatarColor}, transparent)`,
                }}
                aria-hidden
              />
              <img
                src={philosopher.profileImageUrl}
                alt={`${philosopher.name} 초상`}
                className="relative w-[64%] max-w-95 md:w-[86%]"
                onError={(event) => {
                  event.currentTarget.hidden = true;
                }}
              />
            </div>

            {/* 오른쪽: 이름 · 소개 · 설명 */}
            <div className="flex flex-col px-7 pt-8 pb-7 md:px-10 md:pt-11 md:pb-9">
              <DialogHeader className="gap-0 text-left">
                <div className="flex items-center gap-3">
                  <PhilosopherAvatar
                    philosopher={philosopher}
                    className="size-11"
                    decorative
                  />
                  <DialogTitle
                    className="text-[30px] leading-none font-bold tracking-tight"
                    style={{ color: philosopher.inkColor }}
                  >
                    {philosopher.name}
                  </DialogTitle>
                </div>

                {/* introduction: 큰 인용문처럼 */}
                <div className="relative mt-8 pl-6">
                  <span
                    className="absolute top-0 left-0 h-full w-1 rounded-full"
                    style={{ backgroundColor: philosopher.avatarColor }}
                    aria-hidden
                  />
                  <DialogDescription className="text-[21px] leading-snug font-semibold tracking-tight text-foreground">
                    {philosopher.introduction}
                  </DialogDescription>
                </div>
              </DialogHeader>

              {/* description */}
              <div className="mt-8 flex-1">
                <p
                  className="mb-3 text-[12px] font-semibold tracking-[0.08em]"
                  style={{ color: philosopher.inkColor }}
                >
                  어떤 철학자인가요
                </p>
                <p className="text-[15.5px] leading-[1.85] text-[#3f454c]">
                  {philosopher.description}
                </p>
              </div>

              <DialogFooter className="mt-9">
                <Button
                  className="h-13 w-full justify-between rounded-2xl px-6 text-[16px] font-semibold"
                  onClick={() => onStartChat(philosopher)}
                >
                  {philosopher.name}와 대화 시작하기
                  <ArrowRight className="size-5" />
                </Button>
              </DialogFooter>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
