import { Link } from "react-router";

import { SignupForm } from "@/components/signup-form";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function SignupPage() {
  return (
    <Card className="rounded-2xl shadow-none">
      <CardHeader>
        <CardTitle className="text-2xl font-bold tracking-tight">
          회원가입
        </CardTitle>
        <CardDescription>
          가입 후 이메일 인증을 마치면 대화를 시작할 수 있어요.
        </CardDescription>
      </CardHeader>

      <CardContent>
        <SignupForm />
      </CardContent>

      <CardFooter className="flex justify-center">
        <p className="text-sm text-muted-foreground">
          이미 계정이 있나요?{" "}
          <Link
            to="/login"
            className="font-semibold text-foreground underline underline-offset-4 hover:text-primary"
          >
            로그인
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
