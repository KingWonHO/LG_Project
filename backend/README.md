# Backend (FastAPI + Qwen)

LG Comp 확인 에이전트 백엔드. 분석·판정·RAG·리포트 로직(`src/`)을 REST API로 제공한다.
LLM은 **Qwen**(로컬/사내 서버, OpenAI 호환 엔드포인트)을 사용한다.

## 실행

```bash
cd backend
uv sync                 # 의존성 설치 (.venv 생성)
copy .env.example .env  # (macOS/Linux: cp) 후 값 수정
uv run uvicorn main:app --reload --port 8000
```

API 확인: http://localhost:8000/docs (Swagger)

## Qwen 서빙

OpenAI 호환 엔드포인트면 무엇이든 가능. 예시:

- vLLM: `python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen2.5-7B-Instruct`
  → `.env`: `LLM_BASE_URL=http://localhost:8000/v1` (서버 포트 주의), `LLM_MODEL=Qwen/Qwen2.5-7B-Instruct`
- Ollama: `ollama pull qwen2.5:7b`
  → `.env`: `LLM_BASE_URL=http://localhost:11434/v1`, `LLM_MODEL=qwen2.5:7b`

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
