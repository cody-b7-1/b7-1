import { Outlet, useLoaderData, useNavigate, useRevalidator } from "react-router";

import { SiteHeader } from "@/components/site-header";
import type { rootLayoutLoader } from "@/layouts/loaders";
import { logout } from "@/lib/api";

// 모든 화면이 함께 쓰는 틀: 위에 헤더, 아래에 안내 문구를 두고 가운데에 각 화면을 끼웁니다.
export function RootLayout() {
  const user = useLoaderData<typeof rootLayoutLoader>();
  const revalidator = useRevalidator();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error("로그아웃 요청 중 오류 발생:", error);
    } finally {
      revalidator.revalidate();
      navigate("/");
    }
  };

  return (
    // 채팅 화면은 높이를 화면에 고정하고 대화창 안에서 스크롤, 하단 푸터는 채팅 화면일 때 숨김
    <div className="group flex min-h-svh flex-col has-[[data-chat]]:h-svh">
      <SiteHeader email={user?.email} onLogout={handleLogout} />
      <div className="flex min-h-0 flex-1 flex-col">
        <Outlet context={{ user }} />
      </div>
      <footer className="mx-auto w-full max-w-7xl border-t px-4 pt-4 pb-6 text-xs text-muted-foreground group-has-[[data-chat]]:hidden sm:px-6 sm:text-[13px] md:px-12 md:pt-6 md:pb-12">
        실제 철학자가 아닌, 철학 사상에 기반한 AI 캐릭터입니다. 응답에는 오류가
        있을 수 있습니다.
      </footer>
    </div>
  );
}
