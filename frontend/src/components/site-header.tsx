import { Link } from "react-router";

import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button-variants";

type Props = {
  /** 로그인한 사용자의 이메일. 없으면 로그인 버튼을 보여줌 */
  email?: string | null;
  onLogout?: () => void;
};

// 메인·로그인·회원가입·인증 화면이 함께 쓰는 상단 영역
export function SiteHeader({ email, onLogout }: Props) {
  return (
    <header className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-6 md:px-12">
      <Link to="/" className="text-xl font-bold tracking-tight">
        철학자의 방
      </Link>
      {email ? (
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <span className="hidden sm:inline">{email}</span>
          <Button
            variant="outline"
            className="h-11 rounded-full px-5"
            onClick={onLogout}
          >
            로그아웃
          </Button>
        </div>
      ) : (
        <Link
          to="/login"
          className={buttonVariants({
            variant: "outline",
            className: "h-11 rounded-full px-5 text-[15px]",
          })}
        >
          로그인
        </Link>
      )}
    </header>
  );
}
