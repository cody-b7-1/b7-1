import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router";
import { Loader2 } from "lucide-react";

import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { VerifyEmailErrorCard } from "@/components/verify-email-error-card";
import { VerifyEmailSuccessCard } from "@/components/verify-email-success-card";
import { ApiError, verifyEmailToken } from "@/lib/api";

type VerifyResult = {
  token: string;
  status: "success" | "error";
  isRateLimited?: boolean;
};

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  const [result, setResult] = useState<VerifyResult | null>(null);
  const verifiedTokenRef = useRef<string | null>(null);

  useEffect(() => {
    if (!token) {
      verifiedTokenRef.current = null;
      return;
    }

    if (verifiedTokenRef.current === token) return;
    verifiedTokenRef.current = token;

    verifyEmailToken({ token })
      .then(() => {
        if (verifiedTokenRef.current === token) {
          setResult({ token, status: "success" });
        }
      })
      .catch((error: unknown) => {
        if (verifiedTokenRef.current === token) {
          const isRateLimited = error instanceof ApiError && error.status === 429;
          setResult({ token, status: "error", isRateLimited });
        }
      });
  }, [token]);

  if (!token) {
    return <VerifyEmailErrorCard />;
  }

  const isCurrentToken = result?.token === token;
  const status = isCurrentToken ? result.status : "loading";

  if (status === "loading") {
    return (
      <Card className="rounded-2xl p-4 text-center shadow-none sm:p-6">
        <CardHeader className="flex flex-col items-center gap-4">
          <div className="flex size-14 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <Loader2 className="size-6 animate-spin stroke-[2.2]" />
          </div>
          <div className="flex flex-col gap-2">
            <CardTitle className="text-2xl font-bold tracking-tight">
              이메일 인증을 확인하고 있어요
            </CardTitle>
            <CardDescription className="text-[15px] leading-relaxed break-keep text-muted-foreground">
              잠시만 기다려 주세요...
            </CardDescription>
          </div>
        </CardHeader>
      </Card>
    );
  }

  if (status === "success") {
    return <VerifyEmailSuccessCard />;
  }

  return <VerifyEmailErrorCard isRateLimited={result?.isRateLimited} />;
}
