# Backend (FastAPI + Qwen)

LG Comp 확인 에이전트 백엔드. 분석·판정·RAG·리포트 로직(`src/`)을 REST API로 제공한다.
LLM은 **로컬 Ollama**(기본 gemma3:4b, Qwen 등 교체 가능)를 사용한다.

## 실행

```bash
cd backend
uv sync                 # 의존성 설치 (.venv 생성)
copy .env.example .env  # (macOS/Linux: cp) 후 값 수정
uv run uvicorn main:app --reload --port 8000
```

API 확인: http://localhost:8000/docs (Swagger)

## LLM (로컬 Ollama)

이 백엔드는 `src/llm_report.py`에서 **`ollama` 파이썬 패키지**로 로컬 Ollama 데몬
(`http://localhost:11434`)에 접속한다. (vLLM/`LLM_BASE_URL` 방식 아님 — 그 설정은 현재 미사용)

빠른 시작:
```bash
# 1) Ollama 설치 (https://ollama.com/download/windows) → 설치 시 데몬 자동 실행(11434)
# 2) 모델 받기 (기본 gemma3:4b, Qwen이면 qwen2.5:3b)
ollama pull gemma3:4b
# 3) .env 에서 모델 지정
#    LOCAL_LLM_MODEL=gemma3:4b
# 4) 연결 테스트
uv run python test_llm_report.py
```

자세한 설치/문제해결은 **[../docs/ollama_setup.md](../docs/ollama_setup.md)** 참고.

## 구조

```
backend/
├── main.py            # FastAPI 진입점 (REST 엔드포인트)
├── pyproject.toml     # 의존성 (uv)
├── .env.example
└── src/               # 핵심 로직 모듈 (기능 ID 매핑은 ../docs 참고)
    ├── config.py
    ├── file_parser.py / column_mapper.py / trip_analyzer.py ...
    ├── db_manager.py / rag_engine.py / llm_report.py / report_generator.py
    └── prompts/ rules/ data/ (상위 backend/ 하위 폴더)
```

## 엔드포인트 (스켈레톤)

| 메서드 | 경로 | 기능 |
|--------|------|------|
| GET | /api/health | 헬스체크 |
| POST | /api/analyze | 파일 분석 (ANA) |
| GET | /api/history | 분석 이력 (ADM-002) |
| GET/PUT | /api/trip-codes | Trip Code (ENG-002) |
| GET | /api/baseline | 정상 기준 (ENG-003) |
| PUT | /api/rules | Rule JSON (ENG-004) |
| GET | /api/prompt | Prompt (ENG-005) |
| POST | /api/report | 리포트 생성 (RPT) |
