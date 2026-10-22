import { Link, useSearchParams } from "react-router";

import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

// 메일 속 인증 링크로 들어오는 화면: ?token=... 을 서버에 보내 성공/실패를 보여줍니다.
export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  // 토큰이 없는 비정상 접근 시 안내 카드 표시
  if (!token) {
    return (
      <Card className="text-center">
        <CardHeader>
          <CardTitle className="text-xl">인증 링크가 올바르지 않습니다</CardTitle>
          <CardDescription className="pt-2">
            메일로 발송된 인증 링크를 통해 접속해 주세요.
          </CardDescription>
        </CardHeader>
        <CardFooter className="justify-center pt-2">
          <Link
            to="/"
            className={buttonVariants({
              variant: "outline",
              className: "rounded-full px-6",
            })}
          >
            홈으로 돌아가기
          </Link>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="text-center">
      <CardHeader>
        <CardTitle className="text-xl">이메일 인증</CardTitle>
        <CardDescription className="pt-2">
          이메일 인증을 확인하고 있습니다... (token: {token})
        </CardDescription>
      </CardHeader>
    </Card>
  );
}
