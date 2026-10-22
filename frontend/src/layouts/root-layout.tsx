import { Outlet } from "react-router";

import { SiteHeader } from "@/components/site-header";

// 모든 화면이 함께 쓰는 틀: 위에 헤더, 아래에 안내 문구를 두고 가운데에 각 화면을 끼웁니다.
export function RootLayout() {
  return (
    <div className="flex min-h-svh flex-col">
      <SiteHeader />
      <div className="flex flex-1 flex-col">
        <Outlet />
      </div>
      <footer className="mx-auto w-full max-w-7xl border-t px-6 pt-6 pb-12 text-[13px] text-muted-foreground md:px-12">
        실제 철학자가 아닌, 철학 사상에 기반한 AI 캐릭터입니다. 응답에는 오류가
        있을 수 있습니다.
      </footer>
    </div>
  );
}
