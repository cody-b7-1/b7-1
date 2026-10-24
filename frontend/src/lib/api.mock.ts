import {
  ApiError,
  type ChatDetailed,
  type ChatSummary,
  type CursorPage,
  type Message,
  type MessageBody,
  type PhilosopherDetailed,
  type PhilosopherSummary,
  type SendMessageResponse,
  type StartChatResponse,
  type User,
} from "./api";

const user: User = { email: "test@test.com", nickname: "tester" };

const philosophers: PhilosopherDetailed[] = [
  {
    id: 1,
    name: "에라스무스",
    description:
      "르네상스 시대의 인문주의자 에라스무스는 『우신예찬』에서 풍자로 허영과 권위를 비틀었어요. 이 방에서는 체면, 비교, 관습처럼 너무 당연해서 의심하지 않던 기준을 재치 있는 질문으로 다시 살펴봐요. 웃음의 대상은 내가 아니라 그 기준이에요. 남에게 잘 보이려 애쓰느라 마음이 복잡할 때 만나보세요.",
    profileImageUrl: "/img/portrait/erasmus.png",
    iconImageUrl: "/img/avatar/erasmus.png",
    introduction: "풍자와 재치로 우리가 당연하게 여긴 관습과 기준을 돌아봐요.",
    avatarColor: "#C9C35A",
    inkColor: "#5A5A10",
    softColor: "#F3F2E1",
  },
  {
    id: 2,
    name: "쇼펜하우어",
    description:
      "19세기 독일 철학자 쇼펜하우어는 끝없는 욕망이 괴로움을 만든다고 보았고, 연민과 예술적 관조에서 평온의 길을 찾았어요. 이 방에서는 일어난 일과 그 일에 걸었던 기대를 나누어 보며, 무엇이 나를 계속 괴롭히는지 차분하게 살펴봐요. 인정과 비교에 지쳤을 때 만나보세요.",
    profileImageUrl: "/img/portrait/schopenhauer.png",
    iconImageUrl: "/img/avatar/schopenhauer.png",
    introduction: "욕망과 기대가 만드는 부담을 차분하게 나눠 살펴봐요.",
    avatarColor: "#A68BA3",
    inkColor: "#614661",
    softColor: "#F2EDF1",
  },
  {
    id: 3,
    name: "니체",
    description:
      "19세기 독일 철학자 니체는 당연하게 받아들인 가치를 의심하고, 스스로 가치를 세우며 삶을 긍정하자고 말했어요. 이 방에서는 내가 따르는 성공의 기준이 어디서 왔는지 묻고, 정말 원하는 삶과 오늘 해볼 수 있는 작은 선택을 함께 찾아요. 갈림길에서 망설여질 때 만나보세요.",
    profileImageUrl: "/img/portrait/nietzsche.png",
    iconImageUrl: "/img/avatar/nietzsche.png",
    introduction: "남에게서 물려받은 기준과 내가 선택한 가치를 구분해봐요.",
    avatarColor: "#5468E8",
    inkColor: "#2C40C2",
    softColor: "#ECEEFC",
  },
  {
    id: 4,
    name: "에픽테토스",
    description:
      "로마 제국 시대의 스토아 철학자 에픽테토스는 우리가 다스릴 수 있는 것은 일 자체가 아니라 그 일에 대한 판단과 선택이라고 가르쳤어요. 이 방에서는 걱정을 내가 정할 수 있는 것과 없는 것으로 나누고, 오늘 할 수 있는 행동 하나를 찾아요. 결과가 두려워 시작하지 못할 때 만나보세요.",
    profileImageUrl: "/img/portrait/epictetus.png",
    iconImageUrl: "/img/avatar/epictetus.png",
    introduction: "통제할 수 있는 것과 없는 것을 나누고 오늘의 행동을 찾아요.",
    avatarColor: "#5FAE9C",
    inkColor: "#1E6152",
    softColor: "#E8F3F0",
  },
];

const philosopherSummaries: PhilosopherSummary[] = philosophers.map(
  ({ id, name, introduction, iconImageUrl, avatarColor }) => ({
    id,
    name,
    introduction,
    iconImageUrl,
    avatarColor,
  }),
);

// ---- chat (메모리에만 저장, 새로고침하면 초기화) ----
type MockChat = ChatSummary & {
  messages: Message[];
  createdAt: string;
  updatedAt: string;
};

// 최신순
const chats: MockChat[] = [];

const findChat = (chatId: string) => {
  const chat = chats.find((c) => c.chatId === chatId);
  if (!chat) throw new ApiError(404, null);
  return chat;
};

const newMessage = (
  senderRole: Message["senderRole"],
  content: string,
  philosopherId: number | null = null,
): Message => ({
  messageId: crypto.randomUUID(),
  senderRole,
  philosopherId,
  content,
  createdAt: new Date().toISOString(),
});

const answerOf = (philosopherId: number, prompt: string) => {
  const philosopher = philosophers.find((p) => p.id === philosopherId);
  if (!philosopher) throw new ApiError(404, null);
  return newMessage(
    "PHILOSOPHER",
    `(${philosopher.name}) "${prompt}"에 대한 mock 답변입니다.`,
    philosopherId,
  );
};

const startChat = ({ prompt, philosopherId }: MessageBody): StartChatResponse => {
  const messages = [newMessage("USER", prompt), answerOf(philosopherId, prompt)];
  const now = new Date().toISOString();
  const chat: MockChat = {
    chatId: crypto.randomUUID(),
    chatTitle: prompt.slice(0, 30),
    currentPhilosopherId: philosopherId,
    messages,
    createdAt: now,
    updatedAt: now,
  };
  chats.unshift(chat);
  return { chatId: chat.chatId, chatTitle: chat.chatTitle, messages };
};

const sendMessage = (chatId: string, { prompt, philosopherId }: MessageBody): SendMessageResponse => {
  const chat = findChat(chatId);
  const messages = [newMessage("USER", prompt)];
  if (philosopherId !== chat.currentPhilosopherId) {
    messages.push(newMessage("SYSTEM", "철학자를 변경하였습니다."));
  }
  messages.push(answerOf(philosopherId, prompt));

  chat.messages.push(...messages);
  chat.currentPhilosopherId = philosopherId;
  chat.updatedAt = new Date().toISOString();
  chats.unshift(...chats.splice(chats.indexOf(chat), 1));
  return { messages };
};

const getChatList = (limit: number, cursor: string | null): CursorPage<ChatSummary> => {
  const start = cursor ? chats.findIndex((c) => c.chatId === cursor) + 1 : 0;
  const page = chats.slice(start, start + limit);
  const hasMore = start + limit < chats.length;
  return {
    items: page.map(({ chatId, chatTitle, currentPhilosopherId }) => ({
      chatId,
      chatTitle,
      currentPhilosopherId,
    })),
    hasMore,
    nextCursor: hasMore ? page[page.length - 1].chatId : null,
  };
};

// cursor 메시지보다 오래된 메시지 중 최신 limit개를 시간 오름차순으로
const getChat = (chatId: string, limit: number, cursor: string | null): ChatDetailed => {
  const { messages, ...chat } = findChat(chatId);
  const end = cursor ? messages.findIndex((m) => m.messageId === cursor) : messages.length;
  if (end < 0) throw new ApiError(404, null);
  const start = Math.max(0, end - limit);
  const hasMore = start > 0;
  return {
    ...chat,
    messages: messages.slice(start, end),
    hasMore,
    nextCursor: hasMore ? messages[start].messageId : null,
  };
};

// undefined를 반환하면 실제 요청으로 넘어감
export function getMockResponse(method: string, path: string, body?: unknown): unknown {
  const { pathname, searchParams } = new URL(path, "http://mock");
  const limit = searchParams.get("limit");
  const cursor = searchParams.get("cursor");

  if (method === "POST" && pathname === "/auth/sign-up") return user;
  if (method === "POST" && pathname === "/auth/login") return null;
  if (method === "POST" && pathname === "/auth/logout") return null;
  if (method === "POST" && pathname === "/auth/refresh") return null;
  if (method === "GET" && pathname === "/auth/me") return user;

  if (method === "GET" && pathname === "/philosophers") return philosophers;
  if (method === "GET" && pathname === "/philosophers/summaries") {
    return philosopherSummaries;
  }

  const matchedIds = pathname.match(/^\/philosophers\/(\d+)$/);
  if (method === "GET" && matchedIds) {
    const philosopherDetailed = philosophers.find(
      (p) => p.id === Number(matchedIds[1]),
    );
    if (!philosopherDetailed) throw new ApiError(404, null);
    return philosopherDetailed;
  }

  if (method === "POST" && pathname === "/chats") return startChat(body as MessageBody);
  if (method === "GET" && pathname === "/chats") return getChatList(Number(limit ?? 20), cursor);

  const matchedMessages = pathname.match(/^\/chats\/([^/]+)\/messages$/);
  if (method === "POST" && matchedMessages) {
    return sendMessage(matchedMessages[1], body as MessageBody);
  }

  const matchedChatId = pathname.match(/^\/chats\/([^/]+)$/);
  if (matchedChatId) {
    const chatId = matchedChatId[1];
    if (method === "GET") return getChat(chatId, Number(limit ?? 30), cursor);
    if (method === "DELETE") {
      chats.splice(chats.indexOf(findChat(chatId)), 1);
      return null;
    }
  }
}
