# Frontend (React + shadcn/ui)

LG Comp 확인 에이전트의 새 프론트엔드. React + TypeScript + Vite + Tailwind + shadcn/ui.
현재 **프론트 목업 단계**로 더미 데이터로 동작하며, 백엔드(FastAPI) 연동은 추후.

## 실행

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

빌드:

```bash
npm run build
npm run preview
```

## 구조

```
frontend/
├── index.html
├── package.json / vite.config.ts / tsconfig*.json
├── tailwind.config.js / postcss.config.js
└── src/
    ├── main.tsx / App.tsx        # 진입 + 라우팅
    ├── index.css                 # Tailwind + shadcn 테마 변수
    ├── context.tsx               # 역할(user/engineer) 상태 + 접근코드(목업 1234)
    ├── lib/utils.ts              # cn() 헬퍼
    ├── lib/mock.ts               # 더미 데이터
    ├── components/Layout.tsx     # 사이드바 + 역할별 메뉴 (ADM-001)
    ├── components/ui/            # shadcn 컴포넌트 (button/card/badge/tabs/select/input/separator)
    └── pages/                    # UserAnalysis / Report / History / EngineerAdmin
```

## 컴포넌트 추가 (선택)

shadcn CLI로 컴포넌트를 더 받고 싶으면:

```bash
npx shadcn@latest add dialog dropdown-menu table
```

## 다음 단계

- 엔지니어 접근 코드: 현재 `context.tsx`의 `MOCK_ACCESS_CODE`(1234). 추후 백엔드 인증으로 교체.
- 더미 데이터(`lib/mock.ts`)를 FastAPI REST 호출로 교체.
