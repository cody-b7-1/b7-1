import { useRef, useState } from "react";
import { useNavigate } from "react-router";
import { z } from "zod";

import { AuthErrorAlert, type AuthServerError } from "@/components/auth-error-alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, sendVerificationEmail, signUp } from "@/lib/api";

const signupSchema = z
  .object({
    email: z
      .string()
      .trim()
      .min(1, "이메일을 입력해 주세요.")
      .max(254, "이메일은 254자 이하여야 해요.")
      .pipe(z.email("올바른 이메일 형식을 입력해 주세요.")),
    password: z
      .string()
      .min(1, "비밀번호를 입력해 주세요.")
      .min(8, "비밀번호는 8자 이상이어야 해요.")
      .max(128, "비밀번호는 128자 이하여야 해요."),
    passwordConfirm: z
      .string()
      .min(1, "비밀번호를 한 번 더 입력해 주세요."),
  })
  .refine((data) => !data.passwordConfirm || data.password === data.passwordConfirm, {
    message: "비밀번호가 일치하지 않아요.",
    path: ["passwordConfirm"],
  });

type FormErrors = {
  email?: string;
  password?: string;
  passwordConfirm?: string;
};

function getPasswordConfirmError(password: string, passwordConfirm: string): string | undefined {
  if (!passwordConfirm) return "비밀번호를 한 번 더 입력해 주세요.";
  if (password !== passwordConfirm) return "비밀번호가 일치하지 않아요.";
  return undefined;
}

function toSignupServerError(error: unknown): AuthServerError {
  if (error instanceof ApiError) {
    if (error.status === 422) {
      return { message: "요청 값이 올바르지 않거나 누락되었습니다." };
    }
    if (typeof error.body === "object" && error.body && "detail" in error.body) {
      return { message: String((error.body as { detail: unknown }).detail) };
    }
  }
  return { message: "회원가입 중 문제가 발생했습니다. 잠시 후 다시 시도해 주세요." };
}

export function SignupForm() {
  const navigate = useNavigate();
  const formRef = useRef<HTMLFormElement>(null);
  const [errors, setErrors] = useState<FormErrors>({});
  const [serverError, setServerError] = useState<AuthServerError | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const clearFieldError = (field: keyof FormErrors) => {
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const getFormValues = () => {
    const form = formRef.current;
    if (!form) return { email: "", password: "", passwordConfirm: "" };
    const elements = form.elements as HTMLFormControlsCollection & {
      email: HTMLInputElement;
      password: HTMLInputElement;
      passwordConfirm: HTMLInputElement;
    };
    return {
      email: elements.email.value,
      password: elements.password.value,
      passwordConfirm: elements.passwordConfirm.value,
    };
  };

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    setServerError(null);
    setErrors({});

    const formData = new FormData(e.currentTarget);
    const rawValues = {
      email: String(formData.get("email") ?? ""),
      password: String(formData.get("password") ?? ""),
      passwordConfirm: String(formData.get("passwordConfirm") ?? ""),
    };

    const result = signupSchema.safeParse(rawValues);

    if (!result.success) {
      const { fieldErrors } = z.flattenError(result.error);
      setErrors({
        email: fieldErrors.email?.[0],
        password: fieldErrors.password?.[0],
        passwordConfirm: fieldErrors.passwordConfirm?.[0],
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const { email, password } = result.data;
      const nickname = (email.split("@")[0] || "사용자").slice(0, 50);

      await signUp({ email, password, nickname });

      const emailSent = await sendVerificationEmail({ email })
        .then(() => true)
        .catch(() => false);

      navigate("/login", {
        state: {
          signupSuccess: true,
          emailSent,
          email,
        },
      });
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setErrors((prev) => ({
          ...prev,
          email: "이미 등록된 이메일 주소입니다.",
        }));
        return;
      }
      setServerError(toSignupServerError(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form ref={formRef} onSubmit={handleSubmit} noValidate className="flex flex-col gap-5">
      <AuthErrorAlert error={serverError} />

      <div className="flex flex-col gap-2">
        <Label htmlFor="signup-email">이메일</Label>
        <Input
          id="signup-email"
          name="email"
          type="email"
          autoComplete="email"
          placeholder="name@example.com"
          className="h-11 bg-card"
          aria-invalid={!!errors.email || undefined}
          aria-describedby={errors.email ? "signup-email-error" : undefined}
          onBlur={(e) => {
            const result = signupSchema.shape.email.safeParse(e.target.value);
            setErrors((prev) => ({
              ...prev,
              email: result.success ? undefined : result.error.issues[0]?.message,
            }));
          }}
          onChange={() => clearFieldError("email")}
        />
        {errors.email && (
          <p id="signup-email-error" className="text-[13px] text-destructive">
            {errors.email}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="signup-password">비밀번호</Label>
        <Input
          id="signup-password"
          name="password"
          type="password"
          autoComplete="new-password"
          className="h-11 bg-card"
          aria-invalid={!!errors.password || undefined}
          aria-describedby={errors.password ? "signup-password-error" : undefined}
          onBlur={(e) => {
            const currentPassword = e.target.value;
            const { passwordConfirm } = getFormValues();
            const result = signupSchema.shape.password.safeParse(currentPassword);
            setErrors((prev) => ({
              ...prev,
              password: result.success ? undefined : result.error.issues[0]?.message,
              ...(passwordConfirm
                ? {
                    passwordConfirm: getPasswordConfirmError(
                      currentPassword,
                      passwordConfirm
                    ),
                  }
                : {}),
            }));
          }}
          onChange={() => clearFieldError("password")}
        />
        {errors.password && (
          <p id="signup-password-error" className="text-[13px] text-destructive">
            {errors.password}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="signup-password-confirm">비밀번호 확인</Label>
        <Input
          id="signup-password-confirm"
          name="passwordConfirm"
          type="password"
          autoComplete="new-password"
          className="h-11 bg-card"
          aria-invalid={!!errors.passwordConfirm || undefined}
          aria-describedby={
            errors.passwordConfirm ? "signup-password-confirm-error" : undefined
          }
          onBlur={(e) => {
            const { password } = getFormValues();
            setErrors((prev) => ({
              ...prev,
              passwordConfirm: getPasswordConfirmError(password, e.target.value),
            }));
          }}
          onChange={() => clearFieldError("passwordConfirm")}
        />
        {errors.passwordConfirm && (
          <p
            id="signup-password-confirm-error"
            className="text-[13px] text-destructive"
          >
            {errors.passwordConfirm}
          </p>
        )}
      </div>

      <Button
        type="submit"
        disabled={isSubmitting}
        className="mt-2 h-12 w-full cursor-pointer rounded-xl text-[15px] font-semibold"
      >
        {isSubmitting ? "가입하는 중..." : "가입하기"}
      </Button>
    </form>
  );
}
