const BASE = (import.meta.env.VITE_API_URL ?? "/api").replace(/\/+$/, "");
export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(`API ${status}`);
    this.status = status;
    this.body = body;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  init?.signal?.throwIfAborted();
  if (import.meta.env.VITE_MOCK === "true") {
    const { getMockResponse } = await import("./api.mock");
    init?.signal?.throwIfAborted();
    const mockResponse = getMockResponse(
      init?.method ?? "GET",
      path,
      typeof init?.body === "string" ? JSON.parse(init.body) : undefined,
    );
    if (mockResponse !== undefined) return mockResponse as T;
  }
  const resp = await fetch(BASE + path, {
    ...init,
    headers: init?.body
      ? { "Content-Type": "application/json", ...init.headers }
      : init?.headers,
    credentials: "include",
  });
  const text = await resp.text();
  let body: unknown = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      // 성공인데 JSON 아님 = 서버 버그. text를 T로 반환하지 않도록 에러로 보냄
      if (resp.ok) throw new ApiError(resp.status, text);
      body = text; // 프록시 502 HTML 등 JSON이 아닌 에러 응답
    }
  }
  if (!resp.ok) throw new ApiError(resp.status, body);
  return body as T;
}

const toQuery = (
  params: Record<string, string | number | null | undefined>,
) => {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v != null) qs.set(k, String(v));
  }
  const s = qs.toString();
  return s ? `?${s}` : "";
};

// ---- cursor types ----
export type CursorPage<T> = {
  items: T[];
  hasMore: boolean;
  nextCursor: string | null;
};

export type CursorParams = {
  limit?: number;
  cursor?: string | null;
};

// ---- auth ----
export type SignUpBody = {
  email: string;
  password: string;
  nickname: string;
};

export type LoginBody = {
  email: string;
  password: string;
};

export type User = {
  email: string;
  nickname: string;
};

export const signUp = (body: SignUpBody) =>
  request<User>("/auth/sign-up", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const login = (body: LoginBody) =>
  request<null>("/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const logout = () => request<null>("/auth/logout", { method: "POST" });

export const getMe = () => request<User>("/auth/me");

// ---- philosopher ----
export type PhilosopherId = number;

export type PhilosopherDetailed = {
  id: PhilosopherId;
  name: string;
  description: string | null;
  profileImageUrl: string | null;
  iconImageUrl: string | null;
  introduction: string | null;
  avatarColor: string | null;
  inkColor: string | null;
  softColor: string | null;
};

export type PhilosopherSummary = Pick<
  PhilosopherDetailed,
  "name" | "introduction" | "iconImageUrl" | "avatarColor"
>;

export const getPhilosopherList = (signal?: AbortSignal) =>
  request<PhilosopherDetailed[]>("/philosophers", { signal });

export const getPhilosopher = (id: PhilosopherId, signal?: AbortSignal) =>
  request<PhilosopherDetailed>(`/philosophers/${id}`, { signal });

export const getPhilosopherSummaries = (signal?: AbortSignal) =>
  request<PhilosopherSummary[]>("/philosophers/summaries", { signal });

// ---- chat ----
export type ChatId = string;

export type MessageBody = {
  philosopherId: PhilosopherId;
  prompt: string;
};

export type SenderRole = "USER" | "PHILOSOPHER" | "SYSTEM";

export type Message = {
  messageId: string;
  senderRole: SenderRole;
  philosopherId: number | null;
  content: string;
  createdAt: string;
};

export type StartChatResponse = {
  chatId: ChatId;
  chatTitle: string;
  messages: Message[];
};

export type SendMessageResponse = {
  messages: Message[];
};

export type ChatSummary = {
  chatId: ChatId;
  chatTitle: string;
  currentPhilosopherId: number;
};

export type ChatDetailed = {
  chatId: ChatId;
  chatTitle: string;
  currentPhilosopherId: number;
  messages: Message[];
  hasMore: boolean;
  nextCursor: string | null;
  createdAt: string;
  updatedAt: string;
};

export const startChat = (message: MessageBody) =>
  request<StartChatResponse>("/chats", {
    method: "POST",
    body: JSON.stringify(message),
  });

export const getChatList = ({ limit, cursor }: CursorParams = {}) =>
  request<CursorPage<ChatSummary>>(`/chats${toQuery({ limit, cursor })}`);

export const sendMessage = (chatId: ChatId, message: MessageBody) =>
  request<SendMessageResponse>(`/chats/${chatId}/messages`, {
    method: "POST",
    body: JSON.stringify(message),
  });

export const deleteChat = (chatId: ChatId) =>
  request<null>(`/chats/${chatId}`, { method: "DELETE" });

export const getChat = (chatId: ChatId, { limit, cursor }: CursorParams = {}) =>
  request<ChatDetailed>(`/chats/${chatId}${toQuery({ limit, cursor })}`);
