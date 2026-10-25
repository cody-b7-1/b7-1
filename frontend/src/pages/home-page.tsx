import { useCallback, useEffect, useState } from "react";
import { useOutletContext, useNavigate } from "react-router";
import { getPhilosopherList, type PhilosopherId, type User } from "@/lib/api";
import { withDefaults, type ResolvedPhilosopher } from "@/lib/philosopher";

import { PhilosopherCard } from "@/components/philosopher-card";
import { PhilosopherCardSkeleton } from "@/components/philosopher-card-skeleton";
import { PhilosopherDetailDialog } from "@/components/philosopher-detail-dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";

// 철학자 카드를 나열하는 메인 화면

export function HomePage() {
  const { user } = useOutletContext<{ user: User | null }>();
  const [philosophers, setPhilosophers] = useState<ResolvedPhilosopher[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState<PhilosopherId | null>(null);
  const navigate = useNavigate();

  const handleStartChat = (philosopher?: ResolvedPhilosopher) => {
    if (!user) {
      navigate("/login");
      return;
    }
    // 로그인된 사용자는 채팅방으로 이동 (추후 startChat API 또는 첫 대화 생성)
    navigate("/chats/new", { state: { philosopherId: philosopher?.id } });
  };

  const selectedPhilosopher = philosophers.find((p) => p.id === selectedId);
  const handleUpdatePhilosopher = useCallback((updated: ResolvedPhilosopher) => {
    setPhilosophers((prev) =>
      prev.map((p) => (p.id === updated.id ? updated : p)),
    );
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const { signal } = controller;

    async function loadPhilosophers() {
      try {
        const list = await getPhilosopherList(signal);
        if (!signal.aborted) setPhilosophers(list.map(withDefaults));
      } catch {
        // 화면을 떠나며 중단한 요청은 오류로 표시하지 않습니다.
        if (!signal.aborted) {
          setError("철학자 목록을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.");
        }
      } finally {
        if (!signal.aborted) setLoading(false);
      }
    }

    void loadPhilosophers();
    return () => {
      controller.abort();
    };
  }, []);

  return (
    <main>
      <section className="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-x-16 gap-y-6 px-6 pt-12 pb-12 md:px-12 md:pt-16">
        <h1 className="text-4xl leading-tight font-bold tracking-tighter md:text-[56px]">
          하나의 고민,
          <br />
          네 가지 관점.
        </h1>
        <p className="max-w-md text-[17px] leading-relaxed text-muted-foreground">
          철학 사상에 기반한 AI 캐릭터와 대화하며 내 고민과 선택 기준을 살펴보세요. 대화
          중에도 다른 철학자로 바꿔 같은 고민을 이어갈 수 있어요.
        </p>
      </section>

      <section
        aria-label="철학자 목록"
        aria-busy={loading}
        className="mx-auto grid max-w-7xl grid-cols-1 gap-6 px-6 pb-14 sm:grid-cols-2 md:px-12 lg:grid-cols-4"
      >
        {loading && (
          <>
            <p role="status" className="sr-only">
              철학자를 불러오는 중입니다.
            </p>
            {Array.from({ length: 4 }, (_, index) => (
              <PhilosopherCardSkeleton key={index} />
            ))}
          </>
        )}
        {error && (
          <Alert variant="destructive" className="col-span-full">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {!loading && !error && philosophers.length === 0 && (
          <Alert role="status" className="col-span-full">
            <AlertDescription>아직 등록된 철학자가 없습니다.</AlertDescription>
          </Alert>
        )}
        {philosophers.map((philosopher) => (
          <PhilosopherCard
            key={philosopher.id}
            philosopher={philosopher}
            onViewDetails={() => setSelectedId(philosopher.id)}
            onStartChat={() => handleStartChat(philosopher)}
          />
        ))}
      </section>

      {selectedId !== null && (
        <PhilosopherDetailDialog
          key={selectedId}
          philosopherId={selectedId}
          initialPhilosopher={selectedPhilosopher}
          onUpdate={handleUpdatePhilosopher}
          onClose={() => setSelectedId(null)}
          onStartChat={handleStartChat}
        />
      )}
    </main>
  );
}
