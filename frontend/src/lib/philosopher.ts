import type { PhilosopherDetailed } from "@/lib/api";

type NonNull<T> = { [K in keyof T]: NonNullable<T[K]> };
export type ResolvedPhilosopher = NonNull<PhilosopherDetailed>;

const DEFAULTS = {
  description: "",
  introduction: "",
  profileImageUrl: "/img/portrait/default.png",
  iconImageUrl: "/img/avatar/default.png",
  avatarColor: "#6b7280",
  inkColor: "#1f2937",
  softColor: "#f3f4f6",
} satisfies Partial<ResolvedPhilosopher>;

export const withDefaults = (p: PhilosopherDetailed): ResolvedPhilosopher => ({
  ...p,
  description: p.description ?? DEFAULTS.description,
  introduction: p.introduction ?? DEFAULTS.introduction,
  profileImageUrl: p.profileImageUrl ?? DEFAULTS.profileImageUrl,
  iconImageUrl: p.iconImageUrl ?? DEFAULTS.iconImageUrl,
  avatarColor: p.avatarColor ?? DEFAULTS.avatarColor,
  inkColor: p.inkColor ?? DEFAULTS.inkColor,
  softColor: p.softColor ?? DEFAULTS.softColor,
});

// 정보가 없는 철학자를 그릴 때 쓰는 기본 모습
export const placeholderPhilosopher = (
  id: PhilosopherDetailed["id"],
  name: string,
): ResolvedPhilosopher => ({ id, name, ...DEFAULTS });
