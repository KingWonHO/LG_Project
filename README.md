# LG_Project — LG Comp 확인 에이전트

> LGE Internal Use Only

압축기(Comp) 데이터를 업로드하면 **Trip / baseline 이탈 / 데이터 품질**을 자동 분석하여
**PASS · 관리필요 · FAIL** 판정과 **Qwen LLM** 기반 리포트를 생성하는 분석 에이전트.

---

## 아키텍처

```
[React 프론트엔드]  --HTTP/REST-->  [FastAPI 백엔드]  -->  [Qwen LLM (로컬/사내)]
   shadcn/ui                          분석·판정·RAG·리포트        OpenAI 호환 엔드포인트
```

- **프론트엔드**: React + TypeScript + Vite + Tailwind + shadcn/ui (`frontend/`)
- **백엔드**: FastAPI + 분석 로직(`backend/src`) (`backend/`)
- **LLM**: Qwen (vLLM/Ollama 등 OpenAI 호환 서버)
- **DB**: SQLite + SQLAlchemy (PostgreSQL 전환 가능)
- **RAG**: ChromaDB + sentence-transformers (로컬 임베딩, 외부 유출 없음)
- **배포**: Docker (frontend + backend + qwen)

## 프로젝트 방향성

- 엔지니어의 수기 판정·리포트 작성을 자동화. 누구나 CSV/XLSX만 올리면 일관된 기준으로 진단·리포트.
- 일반 사용자(분석 화면) / 엔지니어(룰·baseline·Prompt·DB 관리) 역할 분리 (ADM-001).
- 규칙 기반 분석 + RAG + Qwen으로 원인 후보·조치 권고 생성.
- LLM·임베딩 모두 사내/로컬로 운영하여 분석 데이터 외부 유출 없음.

기능 정의: [docs/functional_spec.md](docs/functional_spec.md) · 진행 현황: [docs/README.md](docs/README.md)

---

## 폴더 구조

```
LG_Project/
├── frontend/               # React + shadcn/ui (UI)
│   ├── src/pages/          # UserAnalysis / Report / History / EngineerAdmin
│   ├── src/components/ui/   # shadcn 컴포넌트
│   └── package.json ...
├── backend/                # FastAPI + 분석 로직
│   ├── main.py             # REST 엔드포인트
│   ├── src/                # file_parser, trip_analyzer, ... llm_report(Qwen)
│   ├── prompts/ rules/ data/
│   ├── pyproject.toml      # uv 의존성
│   └── .env.example
├── docs/                   # 명세서·진행관리
└── README.md
```

---

## 실행 (개발)

두 개의 터미널에서 백엔드/프론트를 각각 실행한다.

### 1. 백엔드 (FastAPI)

```bash
cd backend
uv sync
cp .env.example .env        # Windows: copy
uv run uvicorn main:app --reload --port 8000
```
- Qwen 서버를 먼저 띄우고 `.env`의 `LLM_BASE_URL`/`LLM_MODEL`을 맞춘다.
  - vLLM: `python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen2.5-7B-Instruct`
  - Ollama: `ollama pull qwen2.5:7b` → `LLM_BASE_URL=http://localhost:11434/v1`
- API 문서: http://localhost:8000/docs

### 2. 프론트엔드 (React)

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

---

## 배포 (Docker)

```bash
docker compose up -d --build
# Qwen 모델 최초 1회 내려받기 (Ollama 사용 시)
docker exec -it lgproject-qwen ollama pull qwen2.5:7b
```
- 프론트: `http://<서버>:8080`, API: `http://<서버>:8000`

> PostgreSQL 전환: `docker-compose.yml`의 `db` 서비스와 `backend/pyproject.toml`의 `psycopg2-binary` 주석 해제 후 `.env`의 `DB_URL` 변경.

---

_최종 수정: 2026-06-18_
