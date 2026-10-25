import { Outlet, useLoaderData, useNavigate, useRevalidator } from "react-router";

import { SiteHeader } from "@/components/site-header";
import { ApiError, getMe, logout, type User } from "@/lib/api";

// 전체 화면의 공통 사용자 인증 정보 로더
// - 401 Unauthorized: 비로그인 상태이므로 null을 반환하여 비로그인 UI(로그인 버튼 등)를 유지합니다.
// - 500 등 서버 장애: 일시적인 서버 오류 시에도 화면 전체가 깨지지 않도록 콘솔에 로깅 후 null을 반환합니다.
export async function rootLayoutLoader(): Promise<User | null> {
  try {
    return await getMe();
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null;
    }
    // 네트워크 장애나 5xx 서버 오류는 추적 가능하게 콘솔에 남겨둡니다.
    console.error("사용자 정보 조회 중 오류 발생:", error);
    return null;
  }
}

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
    // 채팅 화면은 높이를 화면에 고정하고 대화창 안에서 스크롤
    <div className="flex min-h-svh flex-col has-[[data-chat]]:h-svh">
      <SiteHeader email={user?.email} onLogout={handleLogout} />
      <div className="flex min-h-0 flex-1 flex-col">
        <Outlet context={{ user }} />
      </div>
      <footer className="mx-auto w-full max-w-7xl border-t px-6 pt-6 pb-12 text-[13px] text-muted-foreground md:px-12">
        실제 철학자가 아닌, 철학 사상에 기반한 AI 캐릭터입니다. 응답에는 오류가
        있을 수 있습니다.
      </footer>
    </div>
  );
}
