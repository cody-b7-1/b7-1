import { useSearchParams } from "react-router";

// 메일 속 인증 링크로 들어오는 화면: ?token=... 을 서버에 보내 성공/실패를 보여줍니다.
export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  return <div>이메일 인증 (token: {token})</div>;
}
