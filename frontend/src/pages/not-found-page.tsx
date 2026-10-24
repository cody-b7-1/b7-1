import { Link } from "react-router";

import { buttonVariants } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-20 text-center">
      <p className="text-sm font-semibold tracking-wide text-muted-foreground uppercase">
        404 Not Found
      </p>
      <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
        페이지를 찾을 수 없습니다
      </h1>
      <p className="mt-4 text-base text-muted-foreground break-keep">
        요청하신 페이지가 존재하지 않거나, 주소가 잘못 입력되었을 수 있습니다.
      </p>
      <div className="mt-8">
        <Link
          to="/"
          className={buttonVariants({
            variant: "outline",
            className: "h-11 rounded-full px-6",
          })}
        >
          홈으로 돌아가기
        </Link>
      </div>
    </main>
  );
}
