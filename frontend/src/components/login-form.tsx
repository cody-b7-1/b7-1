import { useState } from "react";
import { useLocation, useNavigate, useRevalidator } from "react-router";
import { CheckCircle2 } from "lucide-react";
import { z } from "zod";

import { AuthErrorAlert, type AuthServerError } from "@/components/auth-error-alert";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, login } from "@/lib/api";

const loginSchema = z.object({
  email: z
    .string()
    .trim()
    .min(1, "이메일을 입력해 주세요.")
    .pipe(z.email("올바른 이메일 형식을 입력해 주세요.")),
  password: z.string().min(1, "비밀번호를 입력해 주세요."),
});

type FormErrors = {
  email?: string;
  password?: string;
};

type SignupLocationState = {
  signupSuccess?: boolean;
  emailSent?: boolean;
  email?: string;
};

function getSignupSuccessMessage(state: SignupLocationState | null): string | null {
  if (!state?.signupSuccess) return null;
  if (state.emailSent === false) {
    return "회원가입이 완료되었으나 인증 메일 발송에 실패했습니다.\n로그인 후 인증 안내 페이지에서 다시 요청해 주세요.";
  }
  return "회원가입이 완료되었습니다.\n이메일로 전송된 인증 링크를 확인해 주세요.";
}

function toLoginServerError(error: unknown, email: string): AuthServerError {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return { message: "이메일 주소 또는 비밀번호가 일치하지 않습니다." };
    }
    if (error.status === 403) {
      return {
        message: "이메일 인증이 완료되지 않은 계정입니다.\n이메일을 확인해 주세요.",
        linkText: "인증 안내 페이지로 이동",
        linkTo: "/verify-email",
        linkState: { email },
      };
    }
    if (error.status === 422) {
      return { message: "요청 값이 올바르지 않거나 누락되었습니다." };
    }
    if (error.status === 429) {
      return { message: "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요." };
    }
    if (typeof error.body === "object" && error.body && "detail" in error.body) {
      return { message: String((error.body as { detail: unknown }).detail) };
    }
  }
  return { message: "로그인 중 문제가 발생했습니다. 잠시 후 다시 시도해 주세요." };
}

export function LoginForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const revalidator = useRevalidator();
  const signupState = location.state as SignupLocationState | null;

  const [errors, setErrors] = useState<FormErrors>({});
  const [serverError, setServerError] = useState<AuthServerError | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(() =>
    getSignupSuccessMessage(signupState)
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateField = (field: keyof FormErrors, value: string) => {
    const result = loginSchema.shape[field].safeParse(value);
    setErrors((prev) => ({
      ...prev,
      [field]: result.success ? undefined : result.error.issues[0]?.message,
    }));
  };

  const clearFieldError = (field: keyof FormErrors) => {
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSuccessMessage(null);
    setServerError(null);
    setErrors({});

    const formData = new FormData(e.currentTarget);
    const result = loginSchema.safeParse({
      email: String(formData.get("email") ?? ""),
      password: String(formData.get("password") ?? ""),
    });

    if (!result.success) {
      const { fieldErrors } = z.flattenError(result.error);
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
      setServerError(toLoginServerError(error, result.data.email));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-5">
      {successMessage && (
        <Alert className="border-primary/20 bg-primary/5 text-primary">
          <CheckCircle2 className="size-4" />
          <AlertDescription className="whitespace-pre-line text-foreground">
            {successMessage}
          </AlertDescription>
        </Alert>
      )}

      <AuthErrorAlert error={serverError} />

      <div className="flex flex-col gap-2">
        <Label htmlFor="login-email">이메일</Label>
        <Input
          id="login-email"
          name="email"
          type="email"
          autoComplete="email"
          placeholder="name@example.com"
          defaultValue={signupState?.email ?? ""}
          className="h-11 bg-card"
          aria-invalid={!!errors.email || undefined}
          aria-describedby={errors.email ? "login-email-error" : undefined}
          onBlur={(e) => validateField("email", e.target.value)}
          onChange={() => clearFieldError("email")}
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
          aria-describedby={errors.password ? "login-password-error" : undefined}
          onBlur={(e) => validateField("password", e.target.value)}
          onChange={() => clearFieldError("password")}
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
