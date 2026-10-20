# 디자인 참고 자료

《철학자의 방》 시안에서 shadcn/ui와 외부 레퍼런스를 어디에 썼는지 정리했습니다.
**A. 실제 코드에 사용한 것**과 **B. 디자인만 참고한 것**을 나눠 적었습니다.

---

## A. 실제 코드에 사용한 것

### A-1. shadcn/ui 컴포넌트 7종

`source/src/components/ui/`의 파일은 shadcn/ui 공식 저장소의 원본 코드입니다.

- 스타일: **new-york (v4)**, Tailwind CSS v4 기준
- 출처: [shadcn/ui GitHub 저장소](https://github.com/shadcn-ui/ui) (`apps/v4/registry/new-york-v4/ui/`), MIT 라이선스
- 파일 안의 코드는 고치지 않았습니다. 화면에서는 `className`과 `variant`로만 모양을 조정했습니다.

| 컴포넌트 | 문서 | 쓴 화면 | 쓴 곳 |
| --- | --- | --- | --- |
| Card | [docs/components/card](https://ui.shadcn.com/docs/components/card) | 메인, 로그인, 회원가입, 인증 결과 | 철학자 카드 4장, 로그인·회원가입 상자, 인증 결과 상자 |
| Button | [docs/components/button](https://ui.shadcn.com/docs/components/button) | 6개 화면 모두 | 기본형: 대화하기·로그인·가입하기·보내기 / `outline`: 상단 로그인·로그아웃·다른 철학자와 이어가기 / `ghost`: 메인으로 / `icon`: 보내기 |
| Input | [docs/components/input](https://ui.shadcn.com/docs/components/input) | 로그인, 회원가입 | 이메일·비밀번호 입력 |
| Label | [docs/components/label](https://ui.shadcn.com/docs/components/label) | 로그인, 회원가입 | 입력칸 이름 |
| Avatar | [docs/components/avatar](https://ui.shadcn.com/docs/components/avatar) | 채팅, 로그인·회원가입·인증 상단 | 철학자 얼굴 아이콘 (`philosopher-avatar.tsx`로 감싸서 사용) |
| Textarea | [docs/components/textarea](https://ui.shadcn.com/docs/components/textarea) | 채팅 | 메시지 입력창 |
| Dialog | [docs/components/dialog](https://ui.shadcn.com/docs/components/dialog) | 채팅 | 철학자 전환 창 ('다른 철학자와 이어가기'를 누르면 열림) |

### A-2. shadcn/ui 설정 방식

| 항목 | 문서 | 우리가 한 것 |
| --- | --- | --- |
| 테마 변수 | [docs/theming](https://ui.shadcn.com/docs/theming) | `--background`, `--primary`, `--muted-foreground` 등 변수 이름과 짝 구조는 그대로 두고 값만 바꿈 |
| 기본 색 | 〃 | `neutral` 기반에서 출발해 배경 #F3F4F1, 카드 흰색, 주요 색(버튼) 잉크 #1D2024로 조정 |
| 새 색 변수 | 〃 (새 색 추가 방법) | 철학자별 `--erasmus` / `--erasmus-ink` / `--erasmus-soft` 등 12개 추가 |
| Vite 설치 구성 | [docs/installation/vite](https://ui.shadcn.com/docs/installation/vite) | `@` 경로 별칭, `components.json`, `cn()` 함수(`lib/utils.ts`) |

shadcn/ui와 함께 따라오는 라이브러리: `radix-ui`(Dialog·Avatar·Label 동작), `class-variance-authority`(Button 변형), `lucide-react`(아이콘), `tw-animate-css`(Dialog 애니메이션).

### A-3. 그 밖에 코드에 쓴 것

| 항목 | 출처 | 비고 |
| --- | --- | --- |
| Pretendard 글꼴 | [orioncactus/pretendard](https://github.com/orioncactus/pretendard) | SIL Open Font License |
| 철학자 초상·얼굴 그림 | 팀 제작 | `philosophers/portrait/`(메인), `philosophers/avatar/`(채팅) |

---

## B. 디자인만 참고한 것 (코드는 가져오지 않음)

| 참고한 것 | 링크 | 어디에 반영했나 |
| --- | --- | --- |
| shadcn/ui 로그인 블록 | [ui.shadcn.com/blocks/login](https://ui.shadcn.com/blocks/login) | 로그인·회원가입: 카드 하나 안에 제목, 설명, 입력칸, 버튼, 아래쪽 '회원가입/로그인' 링크를 두는 구성. 블록 코드는 쓰지 않고 위 컴포넌트로 직접 짰습니다. |
| Hume AI 디자인 정리 | [shadcn.io/design/hume](https://www.shadcn.io/design/hume) | 순백이 아닌 은은한 배경, 거의 검정색 버튼 하나로 통일, 포인트 색은 버튼이 아니라 장식(초상 뒤 원)에만 사용. ※ shadcn.io는 공식 shadcn/ui와 **관계없는 별도 사이트**입니다. |
| Notion Faces | [buck.co/work/notion-faces](https://buck.co/work/notion-faces) | 철학자 그림의 방향: 밝은 배경 위 검은 잉크 선, 특징 한두 개로 알아보게 하는 단순한 얼굴. 그림 자체는 팀이 새로 만들었습니다. |
| Pi (Inflection AI) | [ustwo.com/work/inflection-ai](https://ustwo.com/work/inflection-ai/) | 채팅 화면의 분위기: 도구보다 차분한 대화 상대처럼, 편하게 성찰할 수 있는 공간. 화면 구성은 참고하지 않았습니다. |

---

## 철학자 색 (두 화면 공통)

메인의 초상 뒤 원과 채팅의 아바타 바탕은 같은 변수를 씁니다. 이름 글자에는 읽기 쉬운 진한 톤을 따로 씁니다.

| 철학자 | 원·아바타 | 이름 글자 | 초상 카드 바탕 |
| --- | --- | --- | --- |
| 에라스무스 | `--erasmus` #C9C35A | `--erasmus-ink` #5A5A10 | `--erasmus-soft` #F3F2E1 |
| 쇼펜하우어 | `--schopenhauer` #A68BA3 | `--schopenhauer-ink` #614661 | `--schopenhauer-soft` #F2EDF1 |
| 니체 | `--nietzsche` #5468E8 | `--nietzsche-ink` #2C40C2 | `--nietzsche-soft` #ECEEFC |
| 에픽테토스 | `--epictetus` #5FAE9C | `--epictetus-ink` #1E6152 | `--epictetus-soft` #E8F3F0 |

정의된 곳: `source/src/index.css`
