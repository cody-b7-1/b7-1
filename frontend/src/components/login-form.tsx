import { useState } from "react";
import { useNavigate, useRevalidator } from "react-router";
import { z } from "zod";

import { AuthErrorAlert, type AuthServerError } from "@/components/auth-error-alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, login } from "@/lib/api";

const loginSchema = z.object({
  email: z
    .string()
    .min(1, "이메일을 입력해 주세요.")
    .email("올바른 이메일 형식을 입력해 주세요."),
  password: z.string().min(1, "비밀번호를 입력해 주세요."),
});

type FormErrors = {
  email?: string;
  password?: string;
};

export function LoginForm() {
  const navigate = useNavigate();
  const revalidator = useRevalidator();
  const [errors, setErrors] = useState<FormErrors>({});
  const [serverError, setServerError] = useState<AuthServerError | null>(null);
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
            message:
              "이메일 인증이 완료되지 않은 계정입니다.\n이메일을 확인해 주세요.",
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
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-5">
      <AuthErrorAlert error={serverError} />

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
            const result = loginSchema.shape.password.safeParse(e.target.value);
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
          <p id="login-password-error" className="text-[13px] text-destructive">
            {errors.password}
          </p>
        )}
      </div>

      <Button
        type="submit"
        disabled={isSubmitting}
        className="mt-2 h-12 w-full cursor-pointer rounded-xl text-[15px] font-semibold"
      >
        {isSubmitting ? "로그인 중..." : "로그인"}
      </Button>
    </form>
  );
}
