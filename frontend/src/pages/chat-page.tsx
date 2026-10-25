// 대화방 화면 (/chats/new: 새 대화, /chats/{chatId}: 기존 대화)

import { useEffect, useRef, useState } from "react";
import { ArrowUp, Plus } from "lucide-react";
import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
  useOutletContext,
  useParams,
} from "react-router";

import { PhilosopherAvatar } from "@/components/philosopher-avatar";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import {
  ApiError,
  getChat,
  getChatList,
  getPhilosopherList,
  sendMessage,
  startChat,
  type ChatSummary,
  type Message,
  type PhilosopherId,
  type User,
} from "@/lib/api";
import { withDefaults, type ResolvedPhilosopher } from "@/lib/philosopher";
import { cn } from "@/lib/utils";

const MAX_LENGTH = 1000;

// 전송 실패 시 상태 코드별 안내 문구 (401은 로그인 화면으로 보냄)
const SEND_ERRORS: Record<number, string> = {
  404: "대화방 또는 철학자를 찾을 수 없어요.",
  409: "이전 질문의 답변을 만드는 중이에요. 잠시 후 다시 보내 주세요.",
  503: "철학자와의 연결이 원활하지 않아요. 잠시 후 다시 시도해 주세요.",
};

const isUnauthorized = (e: unknown) =>
  e instanceof ApiError && e.status === 401;

// 목록에 없는(비활성화된) 철학자의 메시지도 그릴 수 있도록 기본값으로 채움
const unknownPhilosopher = (id: PhilosopherId) =>
  withDefaults({
    id,
    name: "알 수 없는 철학자",
    description: null,
    profileImageUrl: null,
    iconImageUrl: null,
    introduction: null,
    avatarColor: null,
    inkColor: null,
    softColor: null,
  });

export function ChatPage() {
  const { user } = useOutletContext<{ user: User | null }>();
  const { chatId } = useParams<{ chatId?: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  // 홈에서 고른 철학자. 새로고침 등으로 없으면 목록의 첫 철학자로 시작
  const startPhilosopherId = (
    location.state as { philosopherId?: PhilosopherId } | null
  )?.philosopherId;

  const [philosophers, setPhilosophers] = useState<ResolvedPhilosopher[]>([]);
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [current, setCurrent] = useState(startPhilosopherId);
  // 화면에 보이는 messages가 어느 대화의 것인지. chatId와 다르면 불러오는 중
  const [loadedChatId, setLoadedChatId] = useState<string>();
  const [loadError, setLoadError] = useState<"" | "notFound" | "failed">("");
  const [draft, setDraft] = useState("");
  const [waiting, setWaiting] = useState(false);
  const [error, setError] = useState("");
  const [switchOpen, setSwitchOpen] = useState(false);
  const [picked, setPicked] = useState<PhilosopherId | null>(null);
  // 응답을 기다리는 사이 다른 대화로 옮겼는지 확인하는 용도
  const chatIdRef = useRef(chatId);
  const endRef = useRef<HTMLDivElement>(null);

  const philosopherOf = (id: PhilosopherId | null) =>
    philosophers.find((p) => p.id === id) ?? unknownPhilosopher(id ?? 0);
  const currentInfo =
    philosophers.find((p) => p.id === current) ?? philosophers[0];
  const others = philosophers.filter((p) => p.id !== currentInfo?.id);

  const loadChats = () =>
    getChatList()
      .then((page) => setChats(page.items))
      .catch((e) => console.error("대화 목록 조회 중 오류 발생:", e));

  useEffect(() => {
    if (!user) return;
    getPhilosopherList()
      .then((list) => setPhilosophers(list.map(withDefaults)))
      .catch(() => setLoadError("failed"));
    void loadChats();
  }, [user]);

  useEffect(() => {
    chatIdRef.current = chatId;
    setError("");
    setLoadError("");
    if (!user) return;
    if (!chatId) {
      setMessages([]);
      setCurrent(startPhilosopherId);
      return;
    }
    let ignore = false;
    getChat(chatId)
      .then((chat) => {
        if (ignore) return;
        setMessages(chat.messages);
        setCurrent(chat.currentPhilosopherId);
        setLoadedChatId(chatId);
      })
      .catch((e) => {
        if (ignore) return;
        if (isUnauthorized(e)) return navigate("/login");
        // 잘못된 형식의 ID는 백엔드가 422로 응답하므로 없는 대화와 같게 처리
        const notFound =
          e instanceof ApiError && (e.status === 404 || e.status === 422);
        setLoadError(notFound ? "notFound" : "failed");
      });
    return () => {
      ignore = true;
    };
  }, [chatId, startPhilosopherId, user, navigate]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [messages, waiting]);

  if (!user) return <Navigate to="/login" replace />;

  async function send() {
    const prompt = draft.trim();
    if (!prompt) {
      setError("메시지를 입력해 주세요.");
      return;
    }
    if (waiting || !currentInfo) return;
    const body = { philosopherId: currentInfo.id, prompt };
    const sentFrom = chatId;
    // 응답이 오기 전까지 사용자 메시지를 먼저 보여줌
    const pending: Message = {
      messageId: "pending",
      senderRole: "USER",
      philosopherId: null,
      content: prompt,
      createdAt: new Date().toISOString(),
    };
    setError("");
    setDraft("");
    setMessages((m) => [...m, pending]);
    setWaiting(true);
    try {
      if (sentFrom) {
        const res = await sendMessage(sentFrom, body);
        if (chatIdRef.current !== sentFrom) return;
        setMessages((m) => [
          ...m.filter((x) => x !== pending),
          ...res.messages,
        ]);
      } else {
        const res = await startChat(body);
        if (chatIdRef.current !== sentFrom) return;
        setMessages(res.messages);
        setLoadedChatId(res.chatId);
        navigate(`/chats/${res.chatId}`, { replace: true });
      }
      void loadChats();
    } catch (e) {
      if (isUnauthorized(e)) return navigate("/login");
      if (chatIdRef.current !== sentFrom) return;
      setMessages((m) => m.filter((x) => x !== pending));
      setDraft(prompt);
      setError(
        (e instanceof ApiError && SEND_ERRORS[e.status]) ||
          "메시지를 보내지 못했어요. 잠시 후 다시 시도해 주세요.",
      );
    } finally {
      setWaiting(false);
    }
  }

  function confirmSwitch() {
    if (!picked) return;
    setCurrent(picked);
    setSwitchOpen(false);
    setPicked(null);
  }

  return (
    <div className="flex flex-1 flex-col border-t md:flex-row">
      {/* 지난 대화 목록 */}
      <aside className="flex flex-col gap-1.5 border-b bg-card px-4 py-5 md:w-72 md:border-r md:border-b-0">
        <Link
          to="/"
          className={buttonVariants({
            className: "mb-3 h-11 rounded-xl text-[15px] font-semibold",
          })}
        >
          <Plus /> 새 대화
        </Link>
        <p className="px-2 py-1 text-xs font-semibold text-muted-foreground">
          지난 대화
        </p>
        {chats.map((c) => {
          const active = c.chatId === chatId;
          const info = philosopherOf(c.currentPhilosopherId);
          return (
            <Link
              key={c.chatId}
              to={`/chats/${c.chatId}`}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-2.5 rounded-lg px-2 py-2.5 text-left hover:bg-muted",
                active && "bg-muted",
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
                <span className="text-xs text-muted-foreground">
                  {info.name}
                </span>
              </span>
            </Link>
          );
        })}
      </aside>

      <main className="flex min-w-0 flex-1 flex-col">
        {loadError === "notFound" ? (
          <div className="m-auto flex flex-col items-center gap-4 px-6 py-20 text-center">
            <h1 className="text-2xl font-bold">대화를 찾을 수 없어요</h1>
            <p className="text-muted-foreground">
              삭제되었거나 주소가 잘못 입력되었을 수 있어요.
            </p>
            <Link
              to="/"
              className={buttonVariants({
                variant: "outline",
                className: "h-11 rounded-full px-6",
              })}
            >
              홈으로 돌아가기
            </Link>
          </div>
        ) : loadError === "failed" ? (
          <p role="alert" className="m-auto px-6 text-center text-destructive">
            대화를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.
          </p>
        ) : !currentInfo || (chatId && loadedChatId !== chatId) ? (
          <p role="status" className="m-auto text-muted-foreground">
            대화를 불러오는 중이에요…
          </p>
        ) : (
          <>
            <h1 className="sr-only">{currentInfo.name}와 나누는 대화</h1>
            {/* 현재 철학자 + 전환 버튼 */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b bg-card px-6 py-3.5 md:px-8">
              <div className="flex items-center gap-3">
                <PhilosopherAvatar
                  philosopher={currentInfo}
                  className="size-12"
                  decorative
                />
                <div>
                  <p
                    className="text-lg font-bold"
                    style={{ color: currentInfo.inkColor }}
                  >
                    {currentInfo.name}
                  </p>
                  <p className="max-w-md truncate text-[13px] text-muted-foreground">
                    {currentInfo.introduction}
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                className="h-11 rounded-full border-foreground pl-2.5 font-semibold"
                onClick={() => setSwitchOpen(true)}
                disabled={waiting || others.length === 0}
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

            {/* 대화 내역 */}
            <div
              className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-5 px-6 py-8"
              aria-live="polite"
            >
              {messages.length === 0 && (
                <p className="m-auto text-center text-muted-foreground">
                  {currentInfo.name}에게 지금의 고민을 들려주세요.
                </p>
              )}
              {messages.map((m, i) => {
                if (m.senderRole === "USER")
                  return (
                    <div key={m.messageId} className="flex justify-end">
                      <p className="max-w-[520px] rounded-[18px] rounded-br-sm bg-primary px-[18px] py-3.5 text-[15px] leading-relaxed whitespace-pre-wrap text-primary-foreground">
                        {m.content}
                      </p>
                    </div>
                  );
                if (m.senderRole === "SYSTEM") {
                  // SYSTEM 메시지엔 철학자 ID가 없어서 뒤따르는 철학자 답변에서 찾음
                  const next = messages
                    .slice(i)
                    .find((x) => x.senderRole === "PHILOSOPHER");
                  return (
                    <div
                      key={m.messageId}
                      className="my-1 flex items-center gap-3"
                    >
                      <div className="h-px flex-1 bg-border" />
                      <span className="flex items-center gap-2 rounded-full border bg-card py-1.5 pr-3.5 pl-1.5 text-[13px] text-muted-foreground">
                        {next && (
                          <PhilosopherAvatar
                            philosopher={philosopherOf(next.philosopherId)}
                            className="size-[22px]"
                            decorative
                          />
                        )}
                        {next
                          ? `${philosopherOf(next.philosopherId).name}가 같은 고민을 이어서 들어요`
                          : m.content}
                      </span>
                      <div className="h-px flex-1 bg-border" />
                    </div>
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
              {waiting && (
                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                  <PhilosopherAvatar philosopher={currentInfo} decorative />
                  생각을 정리하고 있어요…
                </div>
              )}
            </div>

            {/* 입력창 */}
            <form
              className="sticky bottom-0 border-t bg-background"
              onSubmit={(e) => {
                e.preventDefault();
                void send();
              }}
            >
              <div className="mx-auto flex max-w-3xl flex-col gap-2 px-6 pt-4 pb-5">
                <label htmlFor="message" className="sr-only">
                  {currentInfo.name}에게 메시지 보내기
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
                        void send();
                      }
                    }}
                    placeholder={`${currentInfo.name}에게 이어서 이야기해 보세요`}
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
            {/* 입력창에 가려지지 않도록 입력창 아래를 기준으로 스크롤 */}
            <div ref={endRef} />
          </>
        )}
      </main>

      {/* 철학자 전환 창 */}
      <Dialog open={switchOpen} onOpenChange={setSwitchOpen}>
        <DialogContent className="bg-card sm:max-w-md">
          <DialogHeader>
            <DialogTitle>누구와 이어서 이야기할까요?</DialogTitle>
            <DialogDescription>
              지금까지의 대화는 그대로 남고, 다음 메시지부터 새 철학자가 같은
              고민에 이어서 답해요.
            </DialogDescription>
          </DialogHeader>
          <div
            className="flex flex-col gap-2"
            role="radiogroup"
            aria-label="철학자 선택"
          >
            {others.map((p) => (
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
              onClick={confirmSwitch}
            >
              이 철학자와 이어가기
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
