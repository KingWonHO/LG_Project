# 백엔드 명세서 (Backend Specification)

> LGE Internal Use Only
> 대상: FastAPI API + `backend/src` 로직 · 데이터 · DB · RAG · LLM(로컬 Ollama) 계층

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
| LLM | **로컬 Ollama** (`ollama` 파이썬 라이브러리 직접 호출) · 기본 `gemma3:4b`, 대체 `qwen2.5:3b` |
| 리포트 | 로컬 LLM 요약 → Markdown (PDF 생성은 RPT-002로 미구현) |
| 설정 | pydantic-settings (`src/config.py`) |

---

## 2. 아키텍처 / 계층

```
[React] --REST/JSON--> [FastAPI main.py] --호출--> [src/* 로직] --> [DB / Chroma / Ollama]
```

- `main.py`: 라우팅·검증(pydantic)·CORS만 담당. 비즈니스 로직은 `src/`에 위임.
- `src/`: 화면·HTTP 비의존. 단위 테스트 가능한 순수 모듈.
- 차트 렌더는 프론트(recharts) 담당 → 백엔드는 차트용 **데이터(JSON)**만 제공.

---

## 3. REST API 엔드포인트 (`main.py`)

| 메서드 | 경로 | 기능 ID | 호출 모듈 |
|--------|------|---------|-----------|
| GET | `/api/health` | - | - |
| GET | `/api/compressors` | USR-003 | Comp_Parameter.json 서빙 |
| POST | `/api/analyze` | ANA-001~007, USR-001~006 | file_parser → column_mapper → noise_filter → trip/baseline → verdict_engine → result_builder |
| GET | `/api/history` | ADM-002 | db_manager |
| GET | `/api/history/{id}` | ADM-002 | db_manager (상세·차트 복원) |
| DELETE | `/api/history/{id}` | ADM-002 | db_manager |
| GET/PUT | `/api/trip-codes` | ENG-002, DB-003 | db_manager |
| GET/PUT | `/api/baseline` | ENG-003, DB-004 | db_manager |
| GET/PUT | `/api/rules` | ENG-004 | GET: engineer_rules / PUT: no-op(미구현) |
| GET/PUT | `/api/prompt` | ENG-005, DB-005 | db_manager |
| POST | `/api/report` | RPT-001, LLM-001, RAG-002 | rag_engine → llm_report(Ollama) |
| POST | `/api/rag/index` | RAG-001 | rag_engine 재인덱싱 |
| GET/POST | `/api/rag/engineer` | RAG-001 | 엔지니어 지식 등록·조회 |
| POST | `/api/chat` | LLM 확장 | llm_chat (분석 컨텍스트 기반 대화) |
| POST | `/api/learn` | - | baseline 자동 학습(placeholder) |

응답·요청 스키마는 pydantic 모델로 정의한다(예: `TripCode`).

---

## 4. 분석 파이프라인 (ANA)

| 기능 ID | 모듈 | 책임 |
|---------|------|------|
| ANA-001 | `file_parser.py` | CSV/XLSX → DataFrame |
| ANA-002 | `column_mapper.py` | 파일별 컬럼명 → 표준 컬럼명 |
| ANA 보조 | `noise_filter.py` | 정상범위 초과 값(노이즈/수집오류) 제거 전처리 |
| ANA-003 | `trip_analyzer.py` | Trip_Code≠0 탐지, 발생 횟수·구간 계산 |
| ANA-004 | `baseline_analyzer.py` | 정상 baseline 대비 이탈 판단 |
| ANA-005 | (미구현) | 데이터 품질(이상값·누락·파싱오류) 탐지 — 현재 `quality`는 0 고정 |
| ANA-006 | `verdict_engine.py` | 종합 → PASS·관리필요·FAIL |
| ANA-007 | `result_builder.py` | 표준 JSON 결과 생성 (화면·리포트·차트 공용) |

흐름: `parse → column_map → noise_filter → (trip | baseline) → verdict → result(JSON)`
> ANA-005 데이터 품질 검사는 아직 구현되지 않았다(전용 모듈 없음, `quality` 0 고정).

---

## 5. 엔지니어/관리 로직 (ENG) · DB

| 기능 ID | 모듈 | 책임 |
|---------|------|------|
| ENG-002 | `db_manager.py` | Trip Code 등록/수정 (`/api/trip-codes`, 전용 manager 없이 직접 CRUD) |
| ENG-003 | `db_manager.py` | 정상 기준(Iqe·CoolingPower·Initial_Delay 등) 등록/수정 (`/api/baseline`) |
| ENG-004 | `engineer_rules.py` | `Engineer_Analysis_Rule.xlsx` 로더(GET). Rule JSON 저장(PUT)은 아직 no-op |
| ENG-005 | `db_manager.py` | 리포트 프롬프트 등록/수정 (`/api/prompt`) |
| ENG-006 / DB-001~005 | `db_manager.py` | 파일정보·분석결과·Trip Code·정상기준·Prompt 저장 (SQLAlchemy) |

DB는 SQLAlchemy 모델로 정의 → `DB_URL`만 바꿔 SQLite↔PostgreSQL 전환.
> Trip Code·baseline·Prompt는 별도 manager 모듈 없이 `main.py`가 `db_manager`를 직접 호출한다. Rule JSON 실제 저장(ENG-004 PUT)은 미구현.

---

## 6. RAG 계층 (RAG) — `rag_engine.py`

| 기능 ID | 책임 |
|---------|------|
| RAG-001 | 지식 데이터(Trip Code 설명·조치 가이드·과거 사례) 임베딩 후 Chroma 저장 |
| RAG-002 | 분석 결과 관련 Trip Code·Rule·과거 사례 유사 검색 |

임베딩: sentence-transformers(로컬). 외부 전송 없음.

---

## 7. LLM 계층 (LLM, 로컬 Ollama) — `llm_report.py` · `llm_chat.py`

| 기능 ID | 책임 |
|---------|------|
| LLM-001 | 분석 JSON + RAG 검색 결과 → 요약 생성 (`llm_report.py`). 호출 실패 시 rule-based 폴백 |
| LLM 확장 | 분석 컨텍스트 기반 다중 턴 대화 (`llm_chat.py`, `/api/chat`) |
| LLM-002 | (미구현) 원인 후보 분리 출력 |
| LLM-003 | (미구현) 점검 항목·조치 방향 분리 출력 |

- 호출: `ollama` 파이썬 라이브러리로 **로컬 Ollama 데몬**에 직접 요청 (`ollama.chat(...)`).
  - 기본 모델 `gemma3:4b`, 대체 `qwen2.5:3b`. 모델명은 `LOCAL_LLM_MODEL` 환경변수로 지정.
- 데이터는 사내/로컬에서만 처리(외부 전송 없음).
- 참고: `config.py`의 `llm_base_url`/`llm_api_key`/`llm_model`(OpenAI 호환) 설정은 현재 미사용 레거시.

예시:
```python
import ollama
resp = ollama.chat(model="gemma3:4b", messages=[...], options={"temperature": 0.3})
```

---

## 8. 리포트 생성 (RPT)

| 기능 ID | 책임 | 상태 |
|---------|------|------|
| RPT-001 | 분석 JSON + RAG → 로컬 LLM 요약(Markdown) | ✅ `/api/report` |
| RPT-002 | 리포트 PDF/HTML 파일 생성 | ⬜ 미구현 (현재 Markdown만) |

---

## 9. 설정 — `config.py`

`.env`/환경변수에서 로드: `DB_URL`, `EMBEDDING_MODEL`, `CHROMA_DIR`, `UPLOAD_DIR`, `REPORT_DIR`, `CORS_ORIGINS`, `ENGINEER_ACCESS_CODE`. LLM 모델은 `LOCAL_LLM_MODEL` 환경변수로 지정(`llm_report.py`). `llm_base_url`/`llm_api_key`/`llm_model` 필드는 레거시(미사용).

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

_최종 수정: 2026-07-13_
