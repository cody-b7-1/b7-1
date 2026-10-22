import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import type { ResolvedPhilosopher } from "@/lib/philosopher";
import { cn } from "@/lib/utils";

type Props = {
  philosopher: ResolvedPhilosopher;
  className?: string;
  /** 장식용이면 true (옆에 이름이 이미 있을 때) */
  decorative?: boolean;
};

// shadcn/ui Avatar에 철학자 색(avatarColor) 바탕과 캐릭터 얼굴(IconImageUrl)을 얹은 컴포넌트
export function PhilosopherAvatar({
  philosopher,
  className,
  decorative = false,
}: Props) {
  const { name, iconImageUrl, avatarColor } = philosopher;
  return (
    <Avatar
      className={cn("size-10", className)}
      style={{ backgroundColor: avatarColor }}
    >
      <AvatarImage
        src={iconImageUrl}
        alt={decorative ? "" : name}
        className="translate-y-[8%] scale-[0.86] object-contain"
      />
      <AvatarFallback
        className="bg-transparent text-sm font-semibold text-white"
        aria-hidden={decorative || undefined}
      >
        {name.slice(0, 1)}
      </AvatarFallback>
    </Avatar>
  );
}
