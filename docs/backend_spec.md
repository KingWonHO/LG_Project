# 백엔드 명세서 (Backend Specification)

> LGE Internal Use Only
> 대상: FastAPI API + `backend/src` 로직 · 데이터 · DB · RAG · LLM(Qwen) 계층

분석·판정·저장·검색·생성 로직과 이를 노출하는 REST API를 정의한다. 화면 계층은 [frontend_spec.md](./frontend_spec.md) 참고. 모든 `src/` 모듈은 UI/HTTP에 독립적인 순수 함수/클래스로 작성하고, `main.py`(FastAPI)가 이를 호출하여 엔드포인트로 노출한다.

---

## 1. 기술 스택 (Backend)

| 영역 | 사용 |
|------|------|
| API 서버 | FastAPI + uvicorn |
| 데이터 처리 | pandas / numpy / openpyxl |
| DB | SQLAlchemy (SQLite 기본 → PostgreSQL 전환 가능) |
| 벡터DB(RAG) | ChromaDB (로컬) |
| 임베딩 | sentence-transformers (로컬, 외부 유출 없음) |
| LLM | **Qwen** (vLLM/Ollama 등 OpenAI 호환 엔드포인트, `openai` 클라이언트) |
| 리포트 | Jinja2 → WeasyPrint(PDF) |
| 설정 | pydantic-settings (`src/config.py`) |

---

## 2. 아키텍처 / 계층

```
[React] --REST/JSON--> [FastAPI main.py] --호출--> [src/* 로직] --> [DB / Chroma / Qwen]
```

- `main.py`: 라우팅·검증(pydantic)·CORS만 담당. 비즈니스 로직은 `src/`에 위임.
- `src/`: 화면·HTTP 비의존. 단위 테스트 가능한 순수 모듈.
- 차트 렌더는 프론트(recharts) 담당 → 백엔드는 차트용 **데이터(JSON)**만 제공.

---

## 3. REST API 엔드포인트 (`main.py`)

| 메서드 | 경로 | 기능 ID | 호출 모듈(예정) |
|--------|------|---------|------------------|
| GET | `/api/health` | - | - |
| POST | `/api/analyze` | ANA-001~007, USR-001~006 | file_parser → column_mapper → trip/baseline/quality → verdict_engine → result_builder |
| GET | `/api/history` | ADM-002 | db_manager |
| GET/PUT | `/api/trip-codes` | ENG-002, DB-003 | rule_manager, db_manager |
| GET/PUT | `/api/baseline` | ENG-003, DB-004 | baseline_manager, db_manager |
| PUT | `/api/rules` | ENG-004 | rule_manager |
| GET/PUT | `/api/prompt` | ENG-005, DB-005 | prompt_manager, db_manager |
| POST | `/api/report` | RPT-001/002, LLM-001~003, RAG-002 | rag_engine → llm_report(Qwen) → report_generator |

응답·요청 스키마는 pydantic 모델로 정의한다(예: `TripCode`).

---

## 4. 분석 파이프라인 (ANA)

| 기능 ID | 모듈 | 책임 |
|---------|------|------|
| ANA-001 | `file_parser.py` | CSV/XLSX → DataFrame |
| ANA-002 | `column_mapper.py` | 파일별 컬럼명 → 표준 컬럼명 |
| ANA-003 | `trip_analyzer.py` | Trip_Code≠0 탐지, 발생 횟수·구간 계산 |
| ANA-004 | `baseline_analyzer.py` | 정상 baseline 대비 이탈 판단 |
| ANA-005 | `data_quality_checker.py` | 이상값·누락·파싱오류 탐지 |
| ANA-006 | `verdict_engine.py` | 종합 → PASS·관리필요·FAIL |
| ANA-007 | `result_builder.py` | 표준 JSON 결과 생성 (화면·리포트·차트 공용) |

흐름: `parse → column_map → (trip | baseline | quality) → verdict → result(JSON)`

---

## 5. 엔지니어/관리 로직 (ENG) · DB

| 기능 ID | 모듈 | 책임 |
|---------|------|------|
| ENG-002/004 | `rule_manager.py` | Trip Code·Rule JSON 등록/수정 |
| ENG-003 | `baseline_manager.py` | 정상 기준(Iqe·CoolingPower·Initial_Delay 등) 등록/수정 |
| ENG-005 | `prompt_manager.py` | Qwen 리포트 프롬프트 등록/수정 |
| ENG-006 / DB-001~005 | `db_manager.py` | 파일정보·분석결과·Trip Code·정상기준·Prompt 저장 (SQLAlchemy) |

DB는 SQLAlchemy 모델로 정의 → `DB_URL`만 바꿔 SQLite↔PostgreSQL 전환.

---

## 6. RAG 계층 (RAG) — `rag_engine.py`

| 기능 ID | 책임 |
|---------|------|
| RAG-001 | 지식 데이터(Trip Code 설명·조치 가이드·과거 사례) 임베딩 후 Chroma 저장 |
| RAG-002 | 분석 결과 관련 Trip Code·Rule·과거 사례 유사 검색 |

임베딩: sentence-transformers(로컬). 외부 전송 없음.

---

## 7. LLM 계층 (LLM, Qwen) — `llm_report.py`

| 기능 ID | 책임 |
|---------|------|
| LLM-001 | 분석 JSON + RAG 검색 결과 → 요약 생성 |
| LLM-002 | Trip Code·이상 항목·baseline 이탈 → 원인 후보 생성 |
| LLM-003 | 엔지니어 DB + RAG 근거 → 점검 항목·조치 방향 생성 |

- 호출: `openai` 클라이언트로 **Qwen OpenAI 호환 엔드포인트**(`LLM_BASE_URL`)에 요청.
  - vLLM: `Qwen/Qwen2.5-7B-Instruct` / Ollama: `qwen2.5:7b`
- 프롬프트는 `prompt_manager`/`prompts/` 사용. 데이터는 사내/로컬에서만 처리.

예시:
```python
from openai import OpenAI
client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)
resp = client.chat.completions.create(model=settings.llm_model, messages=[...])
```

---

## 8. 리포트 생성 (RPT) — `report_generator.py`

| 기능 ID | 책임 |
|---------|------|
| RPT-002 | 분석 결과 → Jinja2 HTML → WeasyPrint PDF 생성 |

---

## 9. 설정 — `config.py`

`.env`/환경변수에서 로드: `DB_URL`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `EMBEDDING_MODEL`, `CHROMA_DIR`, `UPLOAD_DIR`, `REPORT_DIR`, `CORS_ORIGINS`, `ENGINEER_ACCESS_CODE`.

---

## 10. 표준 결과 JSON (result_builder / /api/analyze 응답 예시)

```json
{
  "verdict": "관리필요",
  "trip": { "count": 3, "ranges": [[150, 172]] },
  "baseline": { "out_of_range": ["CoolingPower"] },
  "quality": { "missing": 0, "outliers": 2 },
  "series": [{ "time": 0, "컴프전류": 50.1, "전압": 220.3 }]
}
```

`series`는 프론트 recharts 차트(USR-005/006)에서 그대로 사용한다.

---

_최종 수정: 2026-06-18_
