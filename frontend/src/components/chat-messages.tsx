import { Fragment, useEffect, useRef } from "react";

import { PhilosopherAvatar } from "@/components/philosopher-avatar";
import type { Message, PhilosopherId } from "@/lib/api";
import type { ResolvedPhilosopher } from "@/lib/philosopher";

type Props = {
  messages: Message[];
  current: ResolvedPhilosopher;
  philosopherOf: (id: PhilosopherId | null) => ResolvedPhilosopher;
  waiting: boolean;
};

function SwitchDivider({
  philosopher,
  fallback = "",
}: {
  philosopher: ResolvedPhilosopher | undefined;
  fallback?: string;
}) {
  return (
    <div className="my-1 flex items-center gap-3">
      <div className="h-px flex-1 bg-border" />
      <span className="flex items-center gap-2 rounded-full border bg-card py-1.5 pr-3.5 pl-1.5 text-[13px] text-muted-foreground">
        {philosopher && (
          <PhilosopherAvatar
            philosopher={philosopher}
            className="size-[22px]"
            decorative
          />
        )}
        {philosopher
          ? `${philosopher.name}가 같은 고민을 이어서 들어요`
          : fallback}
      </span>
      <div className="h-px flex-1 bg-border" />
    </div>
  );
}

// 대화 내역 (철학자 전환 구분선, 응답 대기 표시 포함)
export function ChatMessages({
  messages,
  current,
  philosopherOf,
  waiting,
}: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [messages, waiting]);

  // 전환 직후 서버의 SYSTEM 메시지가 오기 전에도 구분선을 미리 보여줌
  const lastPhilosopherId = messages.findLast(
    (m) => m.senderRole === "PHILOSOPHER",
  )?.philosopherId;
  const pendingSwitch =
    lastPhilosopherId != null && lastPhilosopherId !== current.id;

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
      <div
        className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-5 px-6 py-8"
        aria-live="polite"
      >
        {messages.length === 0 && (
          <p className="m-auto text-center text-muted-foreground">
            {current.name}에게 지금의 고민을 들려주세요.
          </p>
        )}
        {messages.map((m, i) => {
          if (m.senderRole === "USER")
            return (
              <Fragment key={m.messageId}>
                {/* 응답 대기 중엔 서버가 SYSTEM 메시지를 둘 자리(사용자 메시지 앞)에 표시 */}
                {pendingSwitch && m.messageId === "pending" && (
                  <SwitchDivider philosopher={current} />
                )}
                <div className="flex justify-end">
                  <p className="max-w-[520px] rounded-[18px] rounded-br-sm bg-primary px-[18px] py-3.5 text-[15px] leading-relaxed whitespace-pre-wrap text-primary-foreground">
                    {m.content}
                  </p>
                </div>
              </Fragment>
            );
          if (m.senderRole === "SYSTEM") {
            // SYSTEM 메시지엔 철학자 ID가 없어서 뒤따르는 철학자 답변에서 찾음
            const next = messages
              .slice(i)
              .find((x) => x.senderRole === "PHILOSOPHER");
            return (
              <SwitchDivider
                key={m.messageId}
                philosopher={next && philosopherOf(next.philosopherId)}
                fallback={m.content}
              />
            );
          }
          const info = philosopherOf(m.philosopherId);
          return (
            <div key={m.messageId} className="flex items-start gap-3">
              <PhilosopherAvatar philosopher={info} decorative />
              <div className="max-w-[560px]">
                <p
                  className="mb-1.5 text-[13px] font-bold"
                  style={{ color: info.inkColor }}
                >
                  {info.name}
                </p>
                <p className="rounded-[18px] rounded-tl-sm border bg-card px-[18px] py-3.5 text-[15px] leading-relaxed whitespace-pre-wrap">
                  {m.content}
                </p>
              </div>
            </div>
          );
        })}
        {pendingSwitch && !waiting && <SwitchDivider philosopher={current} />}
        {waiting && (
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <PhilosopherAvatar philosopher={current} decorative />
            생각을 정리하고 있어요…
          </div>
        )}
      </div>
      <div ref={endRef} />
    </div>
  );
}
