// 레이아웃 라우트의 loader (Fast Refresh를 위해 컴포넌트 파일과 분리)

import {
  ApiError,
  getMe,
  getPhilosopher,
  getPhilosopherList,
  type User,
} from "@/lib/api";
import { type ResolvedPhilosopher, withDefaults } from "@/lib/philosopher";

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

// 위에 겹쳐 보여 줄 철학자 수
export const AVATAR_COUNT = 4;

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
