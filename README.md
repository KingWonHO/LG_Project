# LG_Project — LG Comp 확인 에이전트

> LGE Internal Use Only

압축기(Comp) 데이터를 업로드하면 **Trip / baseline 이탈 / 데이터 품질**을 자동 분석하여
**PASS · 관리필요 · FAIL** 판정과 **로컬 LLM** 기반 리포트를 생성하는 분석 에이전트.

---

## 아키텍처

```text
[React 프론트엔드]  --HTTP/REST-->  [FastAPI 백엔드]  -->  [Ollama 로컬 LLM]
   shadcn/ui                          분석·판정·RAG·리포트        gemma3 / qwen2.5 / llama3.2
```

- **프론트엔드**: React + TypeScript + Vite + Tailwind + shadcn/ui (`frontend/`)
- **백엔드**: FastAPI + 분석 로직(`backend/src`) (`backend/`)
- **LLM**: Ollama 기반 로컬 LLM
  - 기본 모델: `gemma3:4b`
  - 대체 모델: `qwen2.5:3b`, `llama3.2`
- **DB**: SQLite + SQLAlchemy (PostgreSQL 전환 가능)
- **RAG**: ChromaDB + sentence-transformers (로컬 임베딩, 외부 유출 없음)
- **배포**: Docker (frontend + backend + ollama/local-llm)

## 프로젝트 방향성

- 엔지니어의 수기 판정·리포트 작성을 자동화. 누구나 CSV/XLSX만 올리면 일관된 기준으로 진단·리포트.
- 일반 사용자(분석 화면) / 엔지니어(룰·baseline·Prompt·DB 관리) 역할 분리 (ADM-001).
- 규칙 기반 분석 + RAG + 로컬 LLM으로 원인 후보·조치 권고 생성.
- LLM·임베딩 모두 사내/로컬로 운영하여 분석 데이터 외부 유출 없음.

기능 정의: [docs/functional_spec.md](docs/functional_spec.md) · 진행 현황: [docs/README.md](docs/README.md)

---

## 폴더 구조

```text
LG_Project/
├── frontend/               # React + shadcn/ui (UI)
│   ├── src/pages/          # UserAnalysis / Report / History / EngineerAdmin
│   ├── src/components/ui/   # shadcn 컴포넌트
│   └── package.json ...
├── backend/                # FastAPI + 분석 로직
│   ├── main.py             # REST 엔드포인트
│   ├── src/                # file_parser, trip_analyzer, ... llm_report
│   ├── prompts/ rules/ data/
│   ├── pyproject.toml      # uv 의존성
│   └── .env.example
├── docs/                   # 명세서·진행관리
└── README.md
```

---

## 실행 (개발)

두 개의 터미널에서 백엔드/프론트를 각각 실행한다.

### 1. 로컬 LLM 준비

본 프로젝트는 외부 API 키를 사용하지 않고 Ollama 기반 로컬 LLM을 사용한다.

Ollama 설치 후 사용할 모델을 내려받는다.

```bash
ollama pull gemma3:4b
ollama pull qwen2.5:3b
ollama pull llama3.2
```

모델 우선순위는 다음과 같다.

| 우선순위 | 모델명 | 용도 |
|---:|---|---|
| 1 | `gemma3:4b` | 기본 모델. 한국어 요약 품질과 보고서 문장 안정성이 가장 좋음 |
| 2 | `qwen2.5:3b` | Qwen 계열 대체 모델. 한국어 요약 품질이 준수하고 비교적 가벼움 |
| 3 | `llama3.2` | 경량 대체 모델. 실행 속도는 빠르지만 요약 중복 가능성이 있음 |

다운로드된 모델 목록 확인:

```bash
ollama list
```

사용하지 않는 모델 삭제:

```bash
ollama rm 모델명
```

기본 모델은 `backend/src/llm_report.py`에서 관리한다.

```python
DEFAULT_LOCAL_MODEL = "gemma3:4b"
```

다른 모델을 사용하려면 환경변수 `LOCAL_LLM_MODEL`을 설정한다.

PowerShell 예시:

```powershell
$env:LOCAL_LLM_MODEL="qwen2.5:3b"
```

환경변수를 설정하지 않으면 기본값인 `gemma3:4b`가 사용된다.

### 2. 백엔드 (FastAPI)

```bash
cd backend
uv sync
uv add ollama
uv run uvicorn main:app --reload --port 8000
```

LLM 요약 기능만 단독 테스트하려면 다음 명령어를 사용한다.

```bash
uv run python test_llm_report.py
```

- API 문서: http://localhost:8000/docs

### 3. 프론트엔드 (React)

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

---

## GPU 사용 확인

Ollama는 지원되는 GPU와 정상적인 드라이버가 있으면 자동으로 GPU를 사용한다.  
Python 코드에서 별도로 `cuda` 설정을 할 필요는 없다.

모델 실행 중 다른 PowerShell에서 아래 명령어로 확인한다.

```powershell
nvidia-smi -l 1
```

출력에 `ollama.exe`가 표시되고 GPU 메모리 사용량이 증가하면 GPU를 사용 중인 것이다.

---

## 배포 (Docker)

```bash
docker compose up -d --build
```

Ollama 사용 시 모델 최초 1회 내려받기:

```bash
docker exec -it lgproject-ollama ollama pull gemma3:4b
```

- 프론트: `http://<서버>:8080`
- API: `http://<서버>:8000`

> PostgreSQL 전환: `docker-compose.yml`의 `db` 서비스와 `backend/pyproject.toml`의 `psycopg2-binary` 주석 해제 후 `.env`의 `DB_URL` 변경.

---

_최종 수정: 2026-06-21_
