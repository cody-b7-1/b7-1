import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter } from "react-router";
import "./index.css";
import { PhilosopherAvatar } from "@/components/philosopher-avatar";
import { PhilosopherDetailDialog } from "@/components/philosopher-detail-dialog";
import { PhilosopherPortrait } from "@/components/philosopher-portrait";
import { SiteHeader } from "@/components/site-header";
import {
  Avatar,
  AvatarBadge,
  AvatarFallback,
  AvatarGroup,
  AvatarGroupCount,
  AvatarImage,
} from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { PhilosopherDetailed } from "@/lib/api";
import { getMockResponse } from "@/lib/api.mock";
import { type ResolvedPhilosopher, withDefaults } from "@/lib/philosopher";

const variants = [
  "default",
  "outline",
  "secondary",
  "ghost",
  "destructive",
  "link",
] as const;
const sizes = ["xs", "sm", "default", "lg"] as const;

const philosophers = [1, 2, 3, 4].map((id) =>
  withDefaults(
    getMockResponse("GET", `/philosophers/${id}`) as PhilosopherDetailed,
  ),
);
// 이미지·색이 비어 있을 때 기본값이 어떻게 보이는지 확인용
const fallbackPhilosopher = withDefaults({
  id: 0,
  name: "무명",
  description: null,
  profileImageUrl: null,
  iconImageUrl: null,
  introduction: null,
  avatarColor: null,
  inkColor: null,
  softColor: null,
});

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function Showcase() {
  const [name, setName] = useState("");
  const [selected, setSelected] = useState<ResolvedPhilosopher | null>(null);

  return (
    <main className="mx-auto max-w-3xl space-y-10 p-8">
      <h1 className="text-2xl font-bold">UI Components</h1>

      <Section title="Button">
        <div className="flex flex-wrap gap-2">
          {variants.map((v) => (
            <Button key={v} variant={v}>
              {v}
            </Button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {sizes.map((s) => (
            <Button key={s} size={s}>
              {s}
            </Button>
          ))}
          <Button disabled>disabled</Button>
        </div>
      </Section>

      <Section title="Input / Label / Textarea">
        <div className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="name">이름</Label>
            <Input
              id="name"
              placeholder="이름을 입력하세요"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="invalid">잘못된 입력</Label>
            <Input id="invalid" aria-invalid defaultValue="invalid" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="bio">소개</Label>
            <Textarea id="bio" placeholder="자기소개를 적어 주세요" />
          </div>
        </div>
      </Section>

      <Section title="Avatar">
        <div className="flex items-center gap-4">
          <Avatar size="sm">
            <AvatarFallback>SM</AvatarFallback>
          </Avatar>
          <Avatar>
            <AvatarImage src="https://github.com/shadcn.png" alt="shadcn" />
            <AvatarFallback>CN</AvatarFallback>
          </Avatar>
          <Avatar size="lg">
            <AvatarFallback>LG</AvatarFallback>
            <AvatarBadge />
          </Avatar>
          <AvatarGroup>
            <Avatar>
              <AvatarFallback>A</AvatarFallback>
            </Avatar>
            <Avatar>
              <AvatarFallback>B</AvatarFallback>
            </Avatar>
            <AvatarGroupCount>+3</AvatarGroupCount>
          </AvatarGroup>
        </div>
      </Section>

      <Section title="Card">
        <Card>
          <CardHeader>
            <CardTitle>카드 제목</CardTitle>
            <CardDescription>카드 설명 텍스트입니다.</CardDescription>
            <CardAction>
              <Button variant="ghost" size="sm">
                Action
              </Button>
            </CardAction>
          </CardHeader>
          <CardContent>
            <p>안녕하세요{name && `, ${name}님`}!</p>
          </CardContent>
          <CardFooter className="gap-2">
            <Button variant="outline">취소</Button>
            <Button>확인</Button>
          </CardFooter>
        </Card>
      </Section>

      <Section title="Dialog">
        <Dialog>
          <DialogTrigger render={<Button variant="outline" />}>
            다이얼로그 열기
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>다이얼로그 제목</DialogTitle>
              <DialogDescription>다이얼로그 설명입니다.</DialogDescription>
            </DialogHeader>
            <Input placeholder="무언가 입력" />
            <DialogFooter showCloseButton>
              <DialogClose render={<Button />}>저장</DialogClose>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </Section>

      <h1 className="text-2xl font-bold">App Components</h1>

      <Section title="SiteHeader">
        <div className="space-y-2 rounded-xl border">
          <SiteHeader />
          <SiteHeader email="test@test.com" onLogout={() => {}} />
        </div>
      </Section>

      <Section title="PhilosopherAvatar">
        <div className="flex items-center gap-4">
          {[...philosophers, fallbackPhilosopher].map((p) => (
            <PhilosopherAvatar key={p.id} philosopher={p} />
          ))}
          <PhilosopherAvatar
            philosopher={philosophers[0]}
            className="size-16"
          />
        </div>
        {/* shadcn AvatarGroup으로 겹치기 (AuthShell과 같은 설정) */}
        <AvatarGroup max={4} className="-space-x-3 *:data-[slot=avatar]:ring-4">
          {philosophers.map((p) => (
            <PhilosopherAvatar key={p.id} philosopher={p} className="size-14" />
          ))}
        </AvatarGroup>
      </Section>

      <Section title="PhilosopherPortrait">
        <div className="grid grid-cols-3 gap-4 sm:grid-cols-5">
          {[...philosophers, fallbackPhilosopher].map((p) => (
            <PhilosopherPortrait key={p.id} philosopher={p} />
          ))}
        </div>
      </Section>

      <Section title="PhilosopherDetailDialog">
        <div className="flex flex-wrap gap-2">
          {[...philosophers, fallbackPhilosopher].map((p) => (
            <Button key={p.id} variant="outline" onClick={() => setSelected(p)}>
              {p.name}
            </Button>
          ))}
        </div>
        <PhilosopherDetailDialog
          philosopher={selected}
          onClose={() => setSelected(null)}
          onStartChat={() => setSelected(null)}
        />
      </Section>

      <Section title="AvatarGroup">
        <div className="flex flex-col">
          <AvatarGroup
            max={4}
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
        </div>
      </Section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <MemoryRouter>
      <Showcase />
    </MemoryRouter>
  </StrictMode>,
);
