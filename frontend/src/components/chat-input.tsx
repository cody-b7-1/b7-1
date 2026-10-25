import { useState } from "react";
import { ArrowUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

const MAX_LENGTH = 1000;

type Props = {
  philosopherName: string;
  waiting: boolean;
  /** 실패 시 보여줄 안내 문구를 돌려줌 */
  onSend: (prompt: string) => Promise<string | undefined>;
};

// 메시지 입력창 (Enter 전송, Shift+Enter 줄바꿈)
export function ChatInput({ philosopherName, waiting, onSend }: Props) {
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");

  async function submit() {
    const prompt = draft.trim();
    if (!prompt) {
      setError("메시지를 입력해 주세요.");
      return;
    }
    if (waiting) return;
    setError("");
    setDraft("");
    const failure = await onSend(prompt);
    if (failure) {
      setDraft(prompt);
      setError(failure);
    }
  }

  return (
    <form
      className="border-t bg-background"
      onSubmit={(e) => {
        e.preventDefault();
        void submit();
      }}
    >
      <div className="mx-auto flex max-w-3xl flex-col gap-2 px-6 pt-4 pb-5">
        <label htmlFor="message" className="sr-only">
          {philosopherName}에게 메시지 보내기
        </label>
        <div className="flex items-end gap-2.5 rounded-[18px] border border-input bg-card py-2 pr-2 pl-4 focus-within:ring-[3px] focus-within:ring-ring/20">
          <Textarea
            id="message"
            value={draft}
            maxLength={MAX_LENGTH}
            onChange={(e) => {
              setDraft(e.target.value);
              if (error) setError("");
            }}
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
            className="min-h-12 resize-none border-0 bg-transparent px-0 shadow-none focus-visible:ring-0 dark:bg-transparent"
            aria-invalid={!!error || undefined}
            aria-describedby="message-hint"
          />
          <Button
            type="submit"
            size="icon"
            className="size-11 shrink-0 rounded-full"
            aria-label="보내기"
            disabled={waiting}
          >
            <ArrowUp className="size-[18px]" />
          </Button>
        </div>
        <div className="flex justify-between gap-4 text-xs text-muted-foreground">
          <span
            id="message-hint"
            role={error ? "alert" : undefined}
            className={cn(error && "text-destructive")}
          >
            {error ||
              "실제 철학자가 아닌, 철학 사상에 기반한 AI 캐릭터입니다. 응답에는 오류가 있을 수 있습니다."}
          </span>
          <span className="shrink-0">
            {draft.length} / {MAX_LENGTH}자
          </span>
        </div>
      </div>
    </form>
  );
}
