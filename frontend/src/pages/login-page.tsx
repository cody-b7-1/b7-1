import { Link } from "react-router";

import { LoginForm } from "@/components/login-form";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function LoginPage() {
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

      <CardContent>
        <LoginForm />
      </CardContent>

      <CardFooter className="flex justify-center">
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
