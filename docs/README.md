# 프로젝트 문서 (docs)

> LGE Internal Use Only

## 아키텍처

React(shadcn/ui) 프론트 → FastAPI 백엔드 → 로컬 Ollama LLM(gemma3:4b). DB: SQLite/SQLAlchemy, RAG: ChromaDB + 로컬 임베딩(예정).

## 문서 목록

| 문서 | 설명 | 상태 |
|------|------|------|
| [functional_spec.md](./functional_spec.md) | 기능 명세 (기능 ID 매핑) | ✅ |
| [frontend_spec.md](./frontend_spec.md) | 프론트 명세 (React/shadcn) | ✅ |
| [backend_spec.md](./backend_spec.md) | 백엔드 명세 (FastAPI/Ollama) | ✅ |
| [git_workflow.md](./git_workflow.md) | Git 협업 워크플로 | ✅ |
| [ollama_setup.md](./ollama_setup.md) | Ollama(로컬 LLM) 설치·연결 가이드 | ✅ |

---

## 구현 진행 현황

상태: ⬜ 미착수 / 🟨 진행중 / ✅ 완료

### 프론트엔드 (React, `frontend/`)
- ✅ 화면 4종(사용자분석/리포트/이력/엔지니어) + 사이드바·역할분리(ADM-001)
- ✅ API 클라이언트(`lib/api.ts`) + vite 프록시(`/api`→8000)
- ✅ 사용자분석 → `POST /api/analyze` 연동 (USR-001~004) — 실 CSV/XLSX 분석값 표시
- ✅ 분석이력 → `GET /api/history` 연동 (ADM-002, 요약 리스트)
- ✅ 엔지니어 관리 → trip-codes/baseline/prompt `GET·PUT` 연동
- ✅ 리포트 → `POST /api/report` (로컬 LLM 요약 표시, RPT-001)
- ✅ 그래프 `series` 백엔드 제공(analyze 응답) → 실데이터 차트
- ✅ 사용자분석/리포트 화면 상태 유지(context) — 화면 이동 후 복귀 시 유지

### 백엔드 (FastAPI, `backend/`)
- ✅ API 엔드포인트 전체(main.py): health/analyze/history/trip-codes/baseline/prompt/report
- ✅ DB(SQLAlchemy): 파일정보·분석결과·TripCode·baseline·Prompt 저장 (DB-001~005)
- ✅ LLM(LLM-001): `llm_report.generate_llm_summary` → 로컬 Ollama(gemma3:4b) 연결, `/api/report`에서 호출
- ✅ `/api/analyze` → src 분석 파이프라인 연결(실 판정). parse→map→trip/baseline→verdict→result_builder
- ✅ ANA-001 파일 파싱 — `src/file_parser.py` (연결)
- ✅ ANA-002 컬럼 자동 매핑 — `src/column_mapper.py` (연결)
- ✅ ANA-003 Trip Code 분석 — `src/trip_analyzer.py` (연결)
- ✅ ANA-004 정상 기준 비교 — `src/baseline_analyzer.py` (연결, 기준은 DB에서 로드)
- ⬜ ANA-005 데이터 품질 이상 탐지 — `src/data_quality_checker.py` (모듈 미구현 → quality 생략하고 동작)
- ✅ ANA-006 최종 판정 생성 — `src/verdict_engine.py` (연결)
- ✅ ANA-007 분석 결과 JSON 생성 — `src/result_builder.py` (+ 차트용 `series`) (연결)
- ⬜ RAG-001/002 — `src/rag_engine.py`
- ⬜ LLM-002/003 원인·조치 분리 출력 — `src/llm_report.py`
- ⬜ RPT-002 리포트 PDF 생성 — `src/report_generator.py`
- ⬜ 이력 상세 조회 엔드포인트(`GET /api/history/{id}`)

### 환경/배포
- ✅ uv 환경(pyproject), Ollama 설치·연결 가이드
- ✅ Docker(compose: backend/frontend/qwen)

---

## 핵심 플로우 상태

업로드 → 실 CSV/XLSX 분석(판정·트립·차트) → 이력 누적 → LLM 리포트 생성: **end-to-end 실분석 연결 완료**.
남은 항목: ANA-005(데이터 품질), RAG, 리포트 PDF, 이력 상세 조회.

---

_최종 수정: 2026-06-21_
