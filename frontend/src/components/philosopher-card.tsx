import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ResolvedPhilosopher } from "@/lib/philosopher";

type Props = {
  philosopher: ResolvedPhilosopher;
  onViewDetails: () => void;
  onStartChat: () => void;
};

export function PhilosopherCard({ philosopher, onViewDetails, onStartChat }: Props) {
  return (
    <Card className="gap-0 rounded-2xl p-3 shadow-none">
      <button
        type="button"
        onClick={onViewDetails}
        className="group rounded-xl focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
        aria-label={`${philosopher.name} 자세히 보기`}
      >
        <div
          className="relative aspect-square overflow-hidden rounded-xl transition-transform duration-300 group-hover:scale-[1.02]"
          style={{ backgroundColor: philosopher.softColor }}
        >
          <div
            className="absolute top-[47%] left-1/2 aspect-square w-[68%] -translate-1/2 rounded-full"
            style={{ backgroundColor: philosopher.avatarColor }}
            aria-hidden="true"
          />
          <img
            src={philosopher.profileImageUrl}
            alt={`${philosopher.name} 초상`}
            className="absolute bottom-0 left-[6%] w-[88%]"
            onError={(event) => {
              event.currentTarget.hidden = true;
            }}
          />
        </div>
      </button>

      <CardHeader className="gap-2 px-3 pt-5">
        <CardTitle
          className="flex items-center gap-2 text-[22px] font-bold tracking-tight"
          style={{ color: philosopher.inkColor }}
        >
          <span
            className="size-2.5 rounded-full"
            style={{ backgroundColor: philosopher.avatarColor }}
            aria-hidden
          />
          {philosopher.name}
        </CardTitle>
      </CardHeader>

      <CardContent className="flex flex-1 flex-col gap-2 px-3 pt-2">
        <CardDescription className="line-clamp-3 text-[15px] leading-relaxed font-medium text-foreground/80">
          {philosopher.introduction || philosopher.description}
        </CardDescription>
      </CardContent>

      <CardFooter className="flex gap-2 px-3 pt-6 pb-3">
        <Button
          variant="outline"
          className="h-12 flex-1 rounded-xl text-[15px] font-semibold"
          onClick={onViewDetails}
        >
          자세히 보기
        </Button>
        <Button
          className="h-12 flex-1 justify-between rounded-xl px-4 text-[15px] font-semibold"
          onClick={onStartChat}
        >
          대화하기
          <ArrowRight className="size-[18px]" />
        </Button>
      </CardFooter>
    </Card>
  );
}
