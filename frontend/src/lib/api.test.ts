import { afterEach, expect, test, vi } from "vitest";
import {
  ApiError,
  deleteChat,
  getChat,
  getChatList,
  getMe,
  getPhilosopher,
  getPhilosopherList,
  login,
  logout,
  sendMessage,
  signUp,
  startChat,
} from "./api";

afterEach(() => vi.unstubAllGlobals());

// body가 undefined면 빈 응답
function mockFetch(status: number, body?: unknown, headers?: HeadersInit) {
  const fetch = vi.fn().mockResolvedValue(
    new Response(body === undefined ? null : JSON.stringify(body), { status, headers }),
  );
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

const cookie = { "Set-Cookie": "access_token=abc; HttpOnly; Path=/" };

// 쿠키 인증이 동작하려면 모든 요청에 credentials: "include"가 있어야 함
const sent = (fetch: ReturnType<typeof mockFetch>) => {
  const [url, init] = fetch.mock.calls[0];
  expect(init.credentials).toBe("include");
  return { url, method: init.method, body: init.body && JSON.parse(init.body) };
};

test("signUp: 201 + Set-Cookie면 User 반환", async () => {
  const user = { email: "a@b.c", nickname: "nick" };
  const fetch = mockFetch(201, user, cookie);
  const body = { ...user, password: "pw" };

  expect(await signUp(body)).toEqual(user);
  expect(sent(fetch)).toEqual({ url: "/api/auth/sign-up", method: "POST", body });
});

test("login: 204 + Set-Cookie면 null", async () => {
  const fetch = mockFetch(204, undefined, cookie);

  expect(await login({ email: "a@b.c", password: "pw" })).toBeNull();
  expect(sent(fetch)).toEqual({
    url: "/api/auth/login",
    method: "POST",
    body: { email: "a@b.c", password: "pw" },
  });
});

test("login: 401이면 에러 body를 담은 ApiError", async () => {
  mockFetch(401, { detail: "invalid credentials" });

  // mock Response body는 한 번만 읽을 수 있어서 요청은 한 번만 보내고 promise를 재사용
  const req = login({ email: "a@b.c", password: "wrong" });
  await expect(req).rejects.toBeInstanceOf(ApiError);
  await expect(req).rejects.toMatchObject({ status: 401, body: { detail: "invalid credentials" } });
});

test("logout: 204 + 쿠키 만료 Set-Cookie면 null", async () => {
  const fetch = mockFetch(204, undefined, { "Set-Cookie": "access_token=; Max-Age=0; Path=/" });

  expect(await logout()).toBeNull();
  expect(sent(fetch)).toMatchObject({ url: "/api/auth/logout", method: "POST" });
});

test("getMe: 200이면 User 반환", async () => {
  const fetch = mockFetch(200, { email: "a@b.c", nickname: "nick" });

  expect(await getMe()).toEqual({ email: "a@b.c", nickname: "nick" });
  expect(sent(fetch)).toMatchObject({ url: "/api/auth/me", method: undefined });
});

test("getMe: 401이면 ApiError (로그아웃 상태)", async () => {
  mockFetch(401);

  await expect(getMe()).rejects.toMatchObject({ status: 401 });
});

const philosopher = {
  id: 1,
  name: "소크라테스",
  description: "desc",
  profileImageUrl: "/p.png",
};

test("getPhilosopherList: 200이면 PhilosopherBrief[] 반환", async () => {
  const fetch = mockFetch(200, [philosopher]);

  expect(await getPhilosopherList()).toEqual([philosopher]);
  expect(sent(fetch)).toMatchObject({ url: "/api/philosophers", method: undefined });
});

test("getPhilosopher: 200이면 PhilosopherDetailed 반환", async () => {
  const detailed = {
    ...philosopher,
    iconImageUrl: "/i.png",
    introduction: "intro",
    avatarColor: "#000",
    inkColor: "#111",
    softColor: "#222",
  };
  const fetch = mockFetch(200, detailed);

  expect(await getPhilosopher(1)).toEqual(detailed);
  expect(sent(fetch)).toMatchObject({ url: "/api/philosophers/1", method: undefined });
});

test("getPhilosopher: 404면 ApiError", async () => {
  mockFetch(404, { detail: "not found" });

  await expect(getPhilosopher(999)).rejects.toMatchObject({ status: 404 });
});

test("JSON이 아닌 응답이면 원문 text를 body로 담은 ApiError", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("Bad Gateway", { status: 502 })));

  await expect(getMe()).rejects.toMatchObject({ status: 502, body: "Bad Gateway" });
});

test("성공 응답인데 JSON이 아니면 text를 반환하지 않고 ApiError", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>", { status: 200 })));

  await expect(getMe()).rejects.toMatchObject({ status: 200, body: "<html>" });
});

const message = {
  messageId: "m1",
  senderRole: "USER",
  philosopherId: null,
  content: "안녕",
  createdAt: "2026-01-01T00:00:00Z",
};

const messageBody = { philosopherId: 1, prompt: "안녕" };

test("startChat: 201이면 StartChatResponse 반환", async () => {
  const resp = { chatId: "c1", chatTitle: "title", currentPhilosopherId: 1, messages: [message] };
  const fetch = mockFetch(201, resp);

  expect(await startChat(messageBody)).toEqual(resp);
  expect(sent(fetch)).toEqual({ url: "/api/chats", method: "POST", body: messageBody });
});

test("getChatList: 인자 없으면 query string 없이 요청", async () => {
  const page = {
    items: [{ chatId: "c1", chatTitle: "title", currentPhilosopherId: 1 }],
    hasMore: false,
    nextCursor: null,
  };
  const fetch = mockFetch(200, page);

  expect(await getChatList()).toEqual(page);
  expect(sent(fetch)).toMatchObject({ url: "/api/chats", method: undefined });
});

test("getChatList: limit, cursor를 query string으로 전달", async () => {
  const fetch = mockFetch(200, { items: [], hasMore: false, nextCursor: null });

  await getChatList({ limit: 10, cursor: "abc" });
  expect(sent(fetch).url).toBe("/api/chats?limit=10&cursor=abc");
});

test("getChatList: cursor가 null이면 query string에서 생략", async () => {
  const fetch = mockFetch(200, { items: [], hasMore: false, nextCursor: null });

  await getChatList({ limit: 10, cursor: null });
  expect(sent(fetch).url).toBe("/api/chats?limit=10");
});

test("sendMessage: 201이면 SendMessageResponse 반환", async () => {
  const resp = { messages: [message, { ...message, messageId: "m2", senderRole: "PHILOSOPHER", philosopherId: 1 }] };
  const fetch = mockFetch(201, resp);

  expect(await sendMessage("c1", messageBody)).toEqual(resp);
  expect(sent(fetch)).toEqual({ url: "/api/chats/c1/messages", method: "POST", body: messageBody });
});

test("deleteChat: 204면 null", async () => {
  const fetch = mockFetch(204);

  expect(await deleteChat("c1")).toBeNull();
  expect(sent(fetch)).toMatchObject({ url: "/api/chats/c1", method: "DELETE" });
});

test("getChat: 200이면 ChatDetailed 반환, cursor는 query string으로 전달", async () => {
  const detailed = {
    chatId: "c1",
    chatTitle: "title",
    currentPhilosopherId: 1,
    messages: [message],
    hasMore: true,
    nextCursor: "next",
    createdAt: "2026-01-01T00:00:00Z",
    updatedAt: "2026-01-01T00:00:00Z",
  };
  const fetch = mockFetch(200, detailed);

  expect(await getChat("c1", { cursor: "abc" })).toEqual(detailed);
  expect(sent(fetch)).toMatchObject({ url: "/api/chats/c1?cursor=abc", method: undefined });
});

test("getChat: 404면 ApiError", async () => {
  mockFetch(404, { detail: "not found" });

  await expect(getChat("nope")).rejects.toMatchObject({ status: 404 });
});
