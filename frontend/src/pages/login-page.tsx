import { useState } from "react";
import { Link, useNavigate, useRevalidator } from "react-router";
import { AlertCircle } from "lucide-react";
import { z } from "zod";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, login } from "@/lib/api";

const loginSchema = z.object({
  email: z
    .string()
    .min(1, "이메일을 입력해 주세요.")
    .email("올바른 이메일 형식을 입력해 주세요."),
  password: z
    .string()
    .min(1, "비밀번호를 입력해 주세요."),
});

type FormErrors = {
  email?: string;
  password?: string;
};

type ServerError = {
  message: string;
  linkText?: string;
  linkTo?: string;
};

export function LoginPage() {
  const navigate = useNavigate();
  const revalidator = useRevalidator();
  const [errors, setErrors] = useState<FormErrors>({});
  const [serverError, setServerError] = useState<ServerError | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setServerError(null);
    setErrors({});

    const formData = new FormData(e.currentTarget);
    const rawValues = {
      email: String(formData.get("email") ?? "").trim(),
      password: String(formData.get("password") ?? ""),
    };

    const result = loginSchema.safeParse(rawValues);

    if (!result.success) {
      const { fieldErrors } = result.error.flatten();
      setErrors({
        email: fieldErrors.email?.[0],
        password: fieldErrors.password?.[0],
      });
      return;
    }

    setIsSubmitting(true);

    try {
      await login(result.data);
      revalidator.revalidate();
      navigate("/");
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 401) {
          setServerError({
            message: "이메일 주소 또는 비밀번호가 일치하지 않습니다.",
          });
          return;
        }
        if (error.status === 403) {
          setServerError({
            message: "이메일 인증이 완료되지 않은 계정입니다.\n이메일을 확인해 주세요.",
            linkText: "인증 안내 페이지로 이동",
            linkTo: "/verify-email",
          });
          return;
        }
        if (error.status === 422) {
          setServerError({
            message: "요청 값이 올바르지 않거나 누락되었습니다.",
          });
          return;
        }
        if (
          typeof error.body === "object" &&
          error.body &&
          "detail" in error.body
        ) {
          setServerError({
            message: String((error.body as { detail: unknown }).detail),
          });
          return;
        }
      }
      setServerError({
        message: "로그인 중 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="rounded-2xl shadow-none">
      <CardHeader>
        <CardTitle className="text-2xl font-bold tracking-tight">
          로그인
        </CardTitle>
        <CardDescription>
          철학자와 나눈 대화를 이어가려면 로그인해 주세요.
        </CardDescription>
      </CardHeader>

      <CardContent className="flex flex-col gap-5">
        {serverError && (
          <Alert variant="destructive">
            <AlertCircle className="size-4" />
            <AlertDescription className="flex flex-col gap-1.5">
              <span className="whitespace-pre-line">{serverError.message}</span>
              {serverError.linkTo && serverError.linkText && (
                <Link
                  to={serverError.linkTo}
                  className="font-medium underline underline-offset-4 hover:opacity-80"
                >
                  {serverError.linkText}
                </Link>
              )}
            </AlertDescription>
          </Alert>
        )}

        <form
          id="login-form"
          onSubmit={handleSubmit}
          noValidate
          className="flex flex-col gap-5"
        >
          <div className="flex flex-col gap-2">
            <Label htmlFor="login-email">이메일</Label>
            <Input
              id="login-email"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="name@example.com"
              className="h-11 bg-card"
              aria-invalid={!!errors.email || undefined}
              aria-describedby={errors.email ? "login-email-error" : undefined}
              onBlur={(e) => {
                const result = loginSchema.shape.email.safeParse(
                  e.target.value.trim()
                );
                setErrors((prev) => ({
                  ...prev,
                  email: result.success
                    ? undefined
                    : result.error.issues[0]?.message,
                }));
              }}
              onChange={() => {
                if (errors.email) {
                  setErrors((prev) => ({ ...prev, email: undefined }));
                }
              }}
            />
            {errors.email && (
              <p id="login-email-error" className="text-[13px] text-destructive">
                {errors.email}
              </p>
            )}
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="login-password">비밀번호</Label>
            <Input
              id="login-password"
              name="password"
              type="password"
              autoComplete="current-password"
              className="h-11 bg-card"
              aria-invalid={!!errors.password || undefined}
              aria-describedby={
                errors.password ? "login-password-error" : undefined
              }
              onBlur={(e) => {
                const result = loginSchema.shape.password.safeParse(
                  e.target.value
                );
                setErrors((prev) => ({
                  ...prev,
                  password: result.success
                    ? undefined
                    : result.error.issues[0]?.message,
                }));
              }}
              onChange={() => {
                if (errors.password) {
                  setErrors((prev) => ({ ...prev, password: undefined }));
                }
              }}
            />
            {errors.password && (
              <p
                id="login-password-error"
                className="text-[13px] text-destructive"
              >
                {errors.password}
              </p>
            )}
          </div>
        </form>
      </CardContent>

      <CardFooter className="mt-7 flex flex-col gap-4">
        <Button
          type="submit"
          form="login-form"
          disabled={isSubmitting}
          className="h-12 w-full rounded-xl text-[15px] font-semibold cursor-pointer"
        >
          {isSubmitting ? "로그인 중..." : "로그인"}
        </Button>
        <p className="text-sm text-muted-foreground">
          아직 계정이 없나요?{" "}
          <Link
            to="/signup"
            className="font-semibold text-foreground underline underline-offset-4 hover:text-primary"
          >
            회원가입
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
