import type { ResolvedPhilosopher } from "@/lib/philosopher";
import { cn } from "@/lib/utils";

// 연한 바탕(softColor) + 철학자 색 원(avatarColor) + 잉크 초상(profileImageUrl).
// 메인 카드와 '자세히 보기' 모달이 같이 씁니다.
export function PhilosopherPortrait({
  philosopher,
  className,
}: {
  philosopher: ResolvedPhilosopher;
  className?: string;
}) {
  const { name, profileImageUrl, softColor, avatarColor } = philosopher;
  return (
    <div
      className={cn(
        "relative aspect-square overflow-hidden rounded-xl",
        className,
      )}
      style={{ backgroundColor: softColor }}
    >
      <div
        className="absolute top-[47%] left-1/2 aspect-square w-[68%] -translate-1/2 rounded-full"
        style={{ backgroundColor: avatarColor }}
      />
      <img
        src={profileImageUrl}
        alt={`${name} 초상`}
        className="absolute bottom-0 left-[6%] w-[88%]"
      />
    </div>
  );
}
