import { memo, useRef, useState } from "react";
import { ArrowUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

const MAX_LENGTH = 1000;
// 이 길이부터 글자 수를 보여줌
const COUNTER_FROM = 800;

type Props = {
  philosopherName: string;
  waiting: boolean;
  /** 실패 시 보여줄 안내 문구를 돌려줌 */
  onSend: (prompt: string) => Promise<string | undefined>;
};

// 메시지 입력창 (Enter 전송, Shift+Enter 줄바꿈)
// 타이핑 시 발생하는 React 리렌더링을 0회로 만들기 위해 비제어 컴포넌트(useRef) 방식 적용
export const ChatInput = memo(function ChatInput({
  philosopherName,
  waiting,
  onSend,
}: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const counterRef = useRef<HTMLSpanElement>(null);
  const [error, setError] = useState("");

  const handleInput = () => {
    if (!textareaRef.current || !counterRef.current) return;
    const length = textareaRef.current.value.length;
    if (length >= COUNTER_FROM) {
      counterRef.current.textContent = `${length} / ${MAX_LENGTH}자`;
      counterRef.current.className = cn(
        "shrink-0",
        length >= MAX_LENGTH && "text-destructive",
      );
    } else {
      counterRef.current.textContent = "";
    }
    if (error) setError("");
  };

  async function submit() {
    const prompt = textareaRef.current?.value.trim() ?? "";
    if (!prompt) {
      setError("메시지를 입력해 주세요.");
      return;
    }
    if (waiting) return;

    setError("");
    if (textareaRef.current) textareaRef.current.value = "";
    if (counterRef.current) counterRef.current.textContent = "";

    const failure = await onSend(prompt);
    if (failure) {
      if (textareaRef.current) {
        textareaRef.current.value = prompt;
      }
      if (counterRef.current && prompt.length >= COUNTER_FROM) {
        counterRef.current.textContent = `${prompt.length} / ${MAX_LENGTH}자`;
      }
      setError(failure);
    }
  }

  return (
    <form
      className="bg-background"
      onSubmit={(e) => {
        e.preventDefault();
        void submit();
      }}
    >
      <div className="mx-auto flex max-w-3xl flex-col gap-1.5 px-4 pt-2 pb-3 sm:gap-2 sm:px-6 sm:pt-2 sm:pb-5">
        <label htmlFor="message" className="sr-only">
          {philosopherName}에게 메시지 보내기
        </label>
        <div className="flex items-end gap-2.5 rounded-[18px] border border-input bg-card py-1.5 pr-1.5 pl-3 focus-within:ring-[3px] focus-within:ring-ring/20 sm:py-2 sm:pr-2 sm:pl-4">
          <Textarea
            ref={textareaRef}
            id="message"
            rows={1}
            defaultValue=""
            maxLength={MAX_LENGTH}
            onInput={handleInput}
            onKeyDown={(e) => {
              if (
                e.key === "Enter" &&
                !e.shiftKey &&
                !e.nativeEvent.isComposing
              ) {
                e.preventDefault();
                void submit();
              }
            }}
            placeholder={`${philosopherName}에게 이어서 이야기해 보세요`}
            className="min-h-11 max-h-48 resize-none self-center border-0 bg-transparent px-0 py-2.5 text-sm shadow-none focus-visible:ring-0 sm:text-base dark:bg-transparent"
            aria-invalid={!!error || undefined}
            aria-describedby="message-hint"
          />
          <Button
            type="submit"
            size="icon"
            className="size-9 shrink-0 rounded-full sm:size-11"
            aria-label="보내기"
            disabled={waiting}
          >
            <ArrowUp className="size-4 sm:size-[18px]" />
          </Button>
        </div>
        <div className="flex justify-between gap-4 text-[11px] text-muted-foreground sm:text-xs">
          <span
            id="message-hint"
            role={error ? "alert" : undefined}
            className={cn("truncate", error && "text-destructive")}
          >
            {error ||
              "실제 철학자가 아닌 AI 캐릭터입니다. 응답에 오류가 있을 수 있습니다."}
          </span>
          <span ref={counterRef} className="shrink-0" />
        </div>
      </div>
    </form>
  );
});
