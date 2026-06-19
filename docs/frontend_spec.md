# 프론트엔드 명세서 (Frontend Specification)

> LGE Internal Use Only
> 대상: React 기반 화면(UI) 계층 (`frontend/`)

화면(페이지) 구성, 사용자 인터랙션, 표시 요소를 정의한다. 비즈니스 로직은 [backend_spec.md](./backend_spec.md)의 FastAPI(`backend/src`)에 위임하며, 프론트엔드는 **입력 수집 · API 호출 · 결과 표시**만 담당한다.

---

## 1. 기술 스택 (Frontend)

| 영역 | 사용 |
|------|------|
| 프레임워크 | React 18 + TypeScript + Vite |
| 스타일 | Tailwind CSS |
| 컴포넌트 | shadcn/ui (radix 기반) |
| 라우팅 | react-router-dom |
| 차트 | recharts (시계열·이상 구간) |
| 아이콘 | lucide-react |
| 상태 | React state + Context (`context.tsx`) |
| 백엔드 통신 | fetch → FastAPI REST (`/api/*`) |

---

## 2. 디렉터리 구조

```
frontend/src/
├── main.tsx / App.tsx        # 진입 + 라우팅
├── index.css                 # Tailwind + shadcn 테마 변수(HSL)
├── context.tsx               # 역할(user/engineer) 상태 + 접근코드
├── lib/utils.ts              # cn() 헬퍼
├── lib/mock.ts               # 더미 데이터 (→ 추후 API 호출로 교체)
├── components/Layout.tsx     # 사이드바 + 역할별 네비 (ADM-001)
├── components/ui/            # shadcn 컴포넌트 (button/card/badge/tabs/select/input/separator)
└── pages/                    # 화면별 컴포넌트
```

---

## 3. 라우팅 / 화면 분리 (ADM-001)

`App.tsx`에서 `<Layout>` 하위에 라우트를 정의한다. `Layout.tsx`가 역할(role)에 따라 메뉴 노출을 제어한다.

| 경로 | 컴포넌트 | 노출 |
|------|----------|------|
| `/` | `pages/UserAnalysis.tsx` | 전체 |
| `/report` | `pages/Report.tsx` | 전체 |
| `/history` | `pages/History.tsx` | 전체 |
| `/engineer` | `pages/EngineerAdmin.tsx` | 엔지니어만 |

- 역할 상태는 `context.tsx`의 `RoleProvider`/`useRole`로 관리 (`"user" | "engineer"`).
- 엔지니어 로그인: 사이드바에서 접근 코드 입력 → `MOCK_ACCESS_CODE`(현재 `1234`, 추후 백엔드 인증으로 교체).
- 이중 방어: `EngineerAdmin.tsx` 내부에서도 `role !== "engineer"`면 안내 카드만 표시.

---

## 4. 화면별 명세

### 4.1 사용자 분석 — `pages/UserAnalysis.tsx`

상단 탭(분석/학습). 좌측(업로드·옵션·그래프) / 우측(평압·Pass/Fail·결과·리포트). shadcn `Card`/`Tabs`/`Select`/`Badge` 사용.

| 기능 ID | 요소 | API 연동(예정) |
|---------|------|----------------|
| USR-001 | CSV/XLSX 업로드 + 샘플 불러오기 | `POST /api/analyze` (multipart) |
| USR-002 | 실행 버튼 → 판정 | `POST /api/analyze` 응답 사용 |
| USR-003 | 컴프/전압/RT Select + 컬럼 badge | 요청 파라미터 |
| USR-004 | Pass/Fail 배지 + 결과 표 | 응답 `verdict`, 항목 |
| USR-005 | recharts LineChart | 응답 시계열 |
| USR-006 | `ReferenceArea`로 Trip 구간 하이라이트 | 응답 `trip.ranges` |

### 4.2 리포트 — `pages/Report.tsx`

| 기능 ID | 요소 | API 연동(예정) |
|---------|------|----------------|
| RPT-001 | 요약·메트릭·원인 후보·조치 권고 카드 | `POST /api/report` |
| (연계) | 리포트 다운로드 버튼 | 백엔드 생성 PDF/HTML |

### 4.3 분석 이력 — `pages/History.tsx`

| 기능 ID | 요소 | API 연동(예정) |
|---------|------|----------------|
| ADM-002 | 이력 표 + 판정 배지 | `GET /api/history` |

### 4.4 엔지니어 관리 — `pages/EngineerAdmin.tsx`

5개 탭(정상 데이터 / Trip Code / 정상 기준 / Rule JSON / Prompt) + DB 반영 버튼.

| 기능 ID | 요소 | API 연동(예정) |
|---------|------|----------------|
| ENG-001 | 정상 데이터 업로드 폼 | `POST /api/analyze`(baseline 용) |
| ENG-002 | Trip Code 표 | `GET/PUT /api/trip-codes` |
| ENG-003 | 정상 기준 입력 | `GET /api/baseline` (+ PUT) |
| ENG-004 | Rule JSON 편집 | `PUT /api/rules` |
| ENG-005 | Prompt 편집 | `GET /api/prompt` (+ PUT) |
| ENG-006 | DB 반영 버튼 | 저장 API 호출 |

---

## 5. shadcn 컴포넌트 (`components/ui/`)

button, card, badge, tabs, select, input, separator. 추가 필요 시:

```bash
npx shadcn@latest add dialog dropdown-menu table toast
```

테마 색상은 `index.css`의 CSS 변수(HSL)로 정의되어 light/dark 모드 자동 대응.

---

## 6. 백엔드 연동 가이드 (다음 단계)

1. `lib/api.ts` 추가 — `fetch` 래퍼 (`VITE_API_BASE` 환경변수, 기본 `/api`).
2. 각 페이지의 `lib/mock.ts` 사용부를 API 호출로 교체.
3. 개발 시 CORS: 백엔드 `.env`의 `CORS_ORIGINS=http://localhost:5173`. 배포 시 nginx가 `/api`를 backend로 프록시.

---

_최종 수정: 2026-06-18_
