import { Link } from "react-router";

import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button-variants";

type Props = {
  /** 로그인한 사용자의 이메일. 없으면 로그인 버튼을 보여줌 */
  email?: string | null;
  onLogout?: () => void;
};

// 메인·로그인·회원가입·인증 화면이 함께 쓰는 상단 영역 (모바일에서는 높이 및 패딩을 슬림하게 조정)
export function SiteHeader({ email, onLogout }: Props) {
  return (
    <header className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3 sm:px-6 sm:py-4 md:px-12 md:py-6">
      <Link to="/" className="text-lg font-bold tracking-tight sm:text-xl">
        철학자의 방
      </Link>
      {email ? (
        <div className="flex items-center gap-2 text-sm text-muted-foreground sm:gap-3">
          <span className="hidden sm:inline">{email}</span>
          <Button
            variant="outline"
            className="h-8 rounded-full px-3 text-xs sm:h-11 sm:px-5 sm:text-sm"
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
            className: "h-8 rounded-full px-3 text-xs sm:h-11 sm:px-5 sm:text-[15px]",
          })}
        >
          로그인
        </Link>
      )}
    </header>
  );
}
