import { ArrowRight } from "lucide-react";

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
import type { ResolvedPhilosopher } from "@/lib/philosopher";

type Props = {
  /** 열 철학자. null이면 모달이 닫혀 있음 */
  philosopher: ResolvedPhilosopher | null;
  onClose: () => void;
  onStartChat: (philosopher: ResolvedPhilosopher) => void;
};

// 메인 카드의 '자세히 보기'를 누르면 뜨는 철학자 상세 모달.
// 모달은 하나만 두고, 누른 철학자에 따라 내용만 바뀝니다.
// 백엔드에서 받는 칸(name, profileImageUrl, IconImageUrl, introduction, description, palette)만 쓰고,
// 철학자별 문구나 색은 프론트에 적어두지 않습니다.
export function PhilosopherDetailDialog({
  philosopher,
  onClose,
  onStartChat,
}: Props) {
  return (
    <Dialog
      open={philosopher !== null}
      onOpenChange={(open) => !open && onClose()}
    >
      <DialogContent className="max-h-[92svh] gap-0 overflow-hidden overflow-y-auto border-0 bg-card p-0 sm:max-w-4xl sm:rounded-3xl">
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
