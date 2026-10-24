import { Link } from "react-router";
import { Check } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function VerifyEmailSuccessCard() {
  return (
    <Card className="rounded-2xl p-4 text-center shadow-none sm:p-6">
      <CardHeader className="flex flex-col items-center gap-4">
        <div className="flex size-14 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400">
          <Check className="size-6 stroke-[2.5]" />
        </div>
        <div className="flex flex-col gap-2">
          <CardTitle className="text-2xl font-bold tracking-tight">
            이메일 인증을 마쳤어요
          </CardTitle>
          <CardDescription className="text-[15px] leading-relaxed break-keep text-muted-foreground">
            이제 로그인하고 네 철학자와 대화를 시작할 수 있어요.
          </CardDescription>
        </div>
      </CardHeader>

      <CardContent className="mt-2 flex flex-col gap-3">
        <Link
          to="/login"
          className={buttonVariants({
            className:
              "h-12 w-full rounded-xl text-[15px] font-semibold text-primary-foreground",
          })}
        >
          로그인하러 가기
        </Link>
      </CardContent>
    </Card>
  );
}
