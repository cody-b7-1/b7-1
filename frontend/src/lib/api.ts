const BASE = import.meta.env.VITE_API_URL ?? "/api";

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
  const resp = await fetch(BASE + path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    credentials: "include",
  });
  const text = await resp.text();
  const body = text ? JSON.parse(text) : null;
  if (!resp.ok) throw new ApiError(resp.status, body);
  return body as T;
}

// ---- auth ----
export type SignUpBody = {
  email: string;
  password: string;
  nickname: string;
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

export const login = (email: string, password: string) =>
  request<null>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

export const logout = () => request<null>("/auth/logout", { method: "POST" });

export const getMe = () => request<User>("/auth/me");

// ---- philosopher ----
export type PhilosopherBrief = {
  id: number;
  name: string;
  description: string;
  profileImageUrl: string;
};

export type PhilosopherDetailed = PhilosopherBrief & {
  iconImageUrl: string;
  introduction: string;
  avatarColor: string;
  inkColor: string;
  softColor: string;
};

export const getPhilosopherList = () =>
  request<PhilosopherBrief[]>("/philosophers");

export const getPhilosopher = (id: number) =>
  request<PhilosopherDetailed>(`/philosophers/${id}`);
