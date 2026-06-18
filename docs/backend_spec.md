# 백엔드 명세서 (Backend Specification)

> LGE Internal Use Only
> 대상: `src/` 로직 · 데이터 · DB · RAG · LLM 계층

분석·판정·저장·검색·생성 로직을 정의한다. 화면 계층은 [frontend_spec.md](./frontend_spec.md) 참고. 모든 모듈은 UI에 독립적이며 함수/클래스로 호출 가능해야 한다.

---

## 1. 기술 스택 (Backend)

| 영역 | 사용 |
|------|------|
| 데이터 처리 | pandas / numpy / openpyxl |
| DB | SQLAlchemy (SQLite 기본 → PostgreSQL 전환 가능) |
| 벡터DB(RAG) | ChromaDB (로컬) |
| 임베딩 | sentence-transformers (로컬, 외부 유출 없음) |
| LLM | 사내/로컬 모델 (Ollama 등 HTTP 호출) |
| 리포트 | Jinja2 → WeasyPrint(PDF) |
| 설정 | pydantic-settings (`src/config.py`) |

---

## 2. 분석 파이프라인 (ANA)

| 기능 ID | 모듈 | 책임 |
|---------|------|------|
| ANA-001 | `file_parser.py` | CSV/XLSX → DataFrame 변환 |
| ANA-002 | `column_mapper.py` | 파일별 상이한 컬럼명 → 표준 컬럼명 매핑 |
| ANA-003 | `trip_analyzer.py` | Trip_Code≠0 탐지, 발생 횟수·구간 계산 |
| ANA-004 | `baseline_analyzer.py` | 정상 baseline 대비 이탈 → 관리필요 판단 |
| ANA-005 | `data_quality_checker.py` | 이상값·누락·파싱오류 탐지 |
| ANA-006 | `verdict_engine.py` | Trip/baseline/품질 종합 → PASS·관리필요·FAIL |
| ANA-007 | `result_builder.py` | 화면·리포트용 표준 JSON 생성 |

표준 분석 흐름:
```
parse → column_map → (trip | baseline | quality) → verdict → result(JSON)
```

---

## 3. 엔지니어/관리 로직 (ENG)

| 기능 ID | 모듈 | 책임 |
|---------|------|------|
| ENG-002 | `rule_manager.py` | Trip Code 의미·원인·조치 등록/수정 |
| ENG-003 | `baseline_manager.py` | Iqe·CoolingPower·Initial_Delay 등 정상 기준 등록/수정 |
| ENG-004 | `rule_manager.py` | 이상 판단용 Rule JSON 등록/수정 |
| ENG-005 | `prompt_manager.py` | LLM 리포트 프롬프트 등록/수정 |
| ENG-006 | `db_manager.py` | 수정된 Trip Code/Rule/Prompt/baseline DB 반영 |

---

## 4. DB 계층 (DB) — `db_manager.py`

| 기능 ID | 저장 대상 |
|---------|-----------|
| DB-001 | 파일 정보 (파일명·경로·업로드 시간·행 수·상태) |
| DB-002 | 분석 결과 (판정·이상 항목·Trip 정보·리포트) |
| DB-003 | Trip Code (설명·원인·조치 가이드) |
| DB-004 | 정상 기준 (baseline 값·feature별 정상 범위) |
| DB-005 | Prompt 버전 |

- ORM: SQLAlchemy 모델로 정의 → 접속 문자열(`DB_URL`)만 바꿔 SQLite↔PostgreSQL 전환.

---

## 5. RAG 계층 (RAG) — `rag_engine.py`

| 기능 ID | 책임 |
|---------|------|
| RAG-001 | 지식 데이터(Trip Code 설명·조치 가이드·과거 사례) 임베딩 후 Chroma 저장 |
| RAG-002 | 분석 결과 관련 Trip Code·Rule·과거 사례 유사 검색 |

- 임베딩: sentence-transformers(로컬). 외부 전송 없음.

---

## 6. LLM 계층 (LLM) — `llm_report.py`

| 기능 ID | 책임 |
|---------|------|
| LLM-001 | 분석 JSON + RAG 검색 결과 → 요약 문장 생성 |
| LLM-002 | Trip Code·이상 항목·baseline 이탈 → 원인 후보 생성 |
| LLM-003 | 엔지니어 DB + RAG 근거 → 점검 항목·조치 방향 생성 |

- 호출: `OLLAMA_URL`의 로컬 LLM 서버에 HTTP 요청. 프롬프트는 `prompt_manager`/`prompts/` 사용.

---

## 7. 리포트 생성 (RPT) — `report_generator.py`

| 기능 ID | 책임 |
|---------|------|
| RPT-002 | 분석 결과 → Jinja2 HTML 템플릿 → WeasyPrint로 PDF 생성 |

---

## 8. 설정 — `config.py`

`.env` / 환경 변수에서 로드: `DB_URL`, `OLLAMA_URL`, `LLM_MODEL`, `EMBEDDING_MODEL`, `CHROMA_DIR`, `UPLOAD_DIR`, `REPORT_DIR`, `ENGINEER_ACCESS_CODE`.

---

## 9. 표준 결과 JSON (result_builder 출력 예시)

```json
{
  "verdict": "관리필요",
  "trip": { "count": 3, "ranges": [[120, 145], [300, 312]] },
  "baseline": { "out_of_range": ["CoolingPower", "Initial_Delay"] },
  "quality": { "missing": 0, "outliers": 2 },
  "report": { "summary": "...", "causes": ["..."], "actions": ["..."] }
}
```

---

_최종 수정: 2026-06-18_
