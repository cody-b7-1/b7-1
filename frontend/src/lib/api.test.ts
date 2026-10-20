import { afterEach, expect, test, vi } from "vitest";
import { ApiError, getMe, getPhilosopher, getPhilosopherList, login, logout, signUp } from "./api";

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

  expect(await login("a@b.c", "pw")).toBeNull();
  expect(sent(fetch)).toEqual({
    url: "/api/auth/login",
    method: "POST",
    body: { email: "a@b.c", password: "pw" },
  });
});

test("login: 401이면 에러 body를 담은 ApiError", async () => {
  mockFetch(401, { detail: "invalid credentials" });

  const err = await login("a@b.c", "wrong").catch((e) => e);
  expect(err).toBeInstanceOf(ApiError);
  expect(err).toMatchObject({ status: 401, body: { detail: "invalid credentials" } });
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
