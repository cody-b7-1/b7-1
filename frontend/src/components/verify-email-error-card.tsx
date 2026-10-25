import { useState } from "react";
import { Link, useLocation } from "react-router";
import { AlertCircle } from "lucide-react";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button-variants";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, sendVerificationEmail } from "@/lib/api";

const emailSchema = z
  .string()
  .trim()
  .min(1, "이메일을 입력해 주세요.")
  .pipe(z.email("올바른 이메일 형식을 입력해 주세요."));

type VerifyEmailLocationState = {
  email?: string;
};

interface VerifyEmailErrorCardProps {
  isRateLimited?: boolean;
}

function toResendErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) return "등록된 사용자를 찾을 수 없습니다.";
    if (error.status === 409) return "이미 이메일 인증이 완료된 계정입니다. 로그인해 주세요.";
    if (error.status === 429) return "인증 메일 요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.";
    if (error.status === 503) return "이메일 발송 서비스가 일시적으로 원활하지 않습니다.";
    if (typeof error.body === "object" && error.body && "detail" in error.body) {
      return String((error.body as { detail: unknown }).detail);
    }
  }
  return "인증 메일 전송 중 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.";
}

export function VerifyEmailErrorCard({ isRateLimited = false }: VerifyEmailErrorCardProps) {
  const location = useLocation();
  const defaultEmail = (location.state as VerifyEmailLocationState | null)?.email ?? "";

  const [showResendInput, setShowResendInput] = useState(() => Boolean(defaultEmail));
  const [resendError, setResendError] = useState<string | null>(null);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [isResending, setIsResending] = useState(false);

  const validateEmailField = (value: string) => {
    const result = emailSchema.safeParse(value);
    setResendError(result.success ? null : (result.error.issues[0]?.message ?? null));
  };

  const handleResendSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    setResendError(null);
    setResendSuccess(false);

    const formData = new FormData(e.currentTarget);
    const emailResult = emailSchema.safeParse(String(formData.get("email") ?? ""));
    if (!emailResult.success) {
      setResendError(
        emailResult.error.issues[0]?.message ?? "올바른 이메일을 입력해 주세요."
      );
      return;
    }

    setIsResending(true);

    try {
      await sendVerificationEmail({ email: emailResult.data });
      setResendSuccess(true);
    } catch (error) {
      setResendError(toResendErrorMessage(error));
    } finally {
      setIsResending(false);
    }
  };

  return (
    <Card className="rounded-2xl p-4 text-center shadow-none sm:p-6">
      <CardHeader className="flex flex-col items-center gap-4">
        <div className="flex size-14 items-center justify-center rounded-full bg-rose-50 text-rose-500 dark:bg-rose-950/40 dark:text-rose-400">
          <AlertCircle className="size-6 stroke-[2.2]" />
        </div>
        <div className="flex flex-col gap-2">
          <CardTitle className="text-2xl font-bold tracking-tight">
            {isRateLimited ? "인증 요청이 너무 많아요" : "인증 링크를 확인할 수 없어요"}
          </CardTitle>
          <CardDescription className="text-[14px] leading-relaxed break-keep text-muted-foreground">
            {isRateLimited ? (
              <>
                짧은 시간 동안 너무 많은 인증 시도가 있었어요.
                <br className="hidden sm:inline" /> 잠시 기다린 후 다시 접속하거나,
                새 인증 메일을 요청해 주세요.
              </>
            ) : (
              <>
                링크가 잘못되었거나 유효 기간이 지났어요. 받은 메일의
                <br className="hidden sm:inline" /> 링크를 다시 눌러 보거나, 인증
                메일을 다시 받아 주세요.
              </>
            )}
          </CardDescription>
        </div>
      </CardHeader>

      <CardContent className="mt-2 flex flex-col gap-3">
        {showResendInput ? (
          <form
            onSubmit={handleResendSubmit}
            noValidate
            className="flex flex-col gap-3 text-left"
          >
            <div className="flex flex-col gap-2">
              <Label htmlFor="resend-email" className="text-sm font-medium">
                가입한 이메일
              </Label>
              <Input
                id="resend-email"
                name="email"
                type="email"
                autoComplete="email"
                placeholder="name@example.com"
                defaultValue={defaultEmail}
                aria-invalid={!!resendError || undefined}
                aria-describedby={resendError ? "resend-email-error" : undefined}
                onBlur={(e) => validateEmailField(e.target.value)}
                onChange={() => {
                  if (resendError) setResendError(null);
                  if (resendSuccess) setResendSuccess(false);
                }}
                className="h-11 bg-card"
                autoFocus
                disabled={isResending}
              />
              {resendError && (
                <p id="resend-email-error" className="text-[13px] text-destructive">
                  {resendError}
                </p>
              )}
            </div>

            {resendSuccess ? (
              <p className="py-2 text-center text-sm font-medium text-emerald-600 dark:text-emerald-400">
                인증 메일을 전송했습니다. 메일함을 확인해 주세요.
              </p>
            ) : (
              <Button
                type="submit"
                disabled={isResending}
                className="h-12 w-full cursor-pointer rounded-xl text-[15px] font-semibold"
              >
                {isResending ? "전송하는 중..." : "인증 메일 전송"}
              </Button>
            )}
          </form>
        ) : (
          <Button
            type="button"
            onClick={() => setShowResendInput(true)}
            className="h-12 w-full cursor-pointer rounded-xl text-[15px] font-semibold"
          >
            인증 메일 다시 받기
          </Button>
        )}

        <Link
          to="/"
          className={buttonVariants({
            variant: "ghost",
            className:
              "h-10 text-[14px] font-medium text-muted-foreground hover:text-foreground",
          })}
        >
          메인으로
        </Link>
      </CardContent>
    </Card>
  );
}
