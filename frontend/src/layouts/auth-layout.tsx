import { Navigate, Outlet, useLoaderData, useOutletContext } from "react-router";

import { PhilosopherAvatar } from "@/components/philosopher-avatar";
import { AvatarGroup } from "@/components/ui/avatar";
import { getPhilosopher, getPhilosopherList, type User } from "@/lib/api";
import { type ResolvedPhilosopher, withDefaults } from "@/lib/philosopher";

// 위에 겹쳐 보여 줄 철학자 수
const AVATAR_COUNT = 4;

// 위에 겹쳐 보여 줄 철학자들을 불러옵니다.
// 얼굴은 장식이라 불러오기에 실패해도 화면은 그대로 띄웁니다.
export async function authLayoutLoader(): Promise<ResolvedPhilosopher[]> {
  try {
    const list = await getPhilosopherList();
    const details = await Promise.all(
      list.slice(0, AVATAR_COUNT).map((p) => getPhilosopher(p.id)),
    );
    return details.map(withDefaults);
  } catch {
    return [];
  }
}

// 로그인·회원가입·이메일 인증 화면의 공통 틀:
// 위에 철학자 얼굴들을 겹쳐 두고, 가운데에 각 화면의 카드를 끼웁니다.
// 헤더와 푸터는 RootLayout이 붙입니다.
export function AuthLayout() {
  const { user } = useOutletContext<{ user: User | null }>();
  const philosophers = useLoaderData<typeof authLayoutLoader>();

  // 이미 로그인된 사용자는 홈("/")으로 리다이렉트합니다.
  if (user) {
    return <Navigate to="/" replace />;
  }

  return (
    <main className="flex flex-1 flex-col items-center px-6 pt-10 pb-20">
      <AvatarGroup
        max={AVATAR_COUNT}
        className="mb-6 -space-x-3 *:data-[slot=avatar]:ring-4"
        aria-hidden
      >
        {philosophers.map((p) => (
          <PhilosopherAvatar
            key={p.id}
            philosopher={p}
            decorative
            className="size-14"
          />
        ))}
      </AvatarGroup>
      <div className="w-full max-w-md">
        <Outlet />
      </div>
    </main>
  );
}
