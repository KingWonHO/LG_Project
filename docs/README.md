# 프로젝트 문서 (docs)

> LGE Internal Use Only

## 아키텍처

React(shadcn/ui) 프론트 → FastAPI 백엔드 → Qwen LLM(로컬/사내). DB: SQLite/SQLAlchemy, RAG: ChromaDB + 로컬 임베딩.

## 문서 목록

| 문서 | 설명 | 상태 |
|------|------|------|
| [functional_spec.md](./functional_spec.md) | 기능 명세 (기능 ID 매핑) | ✅ 유효 (React/FastAPI) |
| [frontend_spec.md](./frontend_spec.md) | 프론트 명세 (React/shadcn) | ✅ 유효 |
| [backend_spec.md](./backend_spec.md) | 백엔드 명세 (FastAPI/Qwen) | ✅ 유효 |
| [git_workflow.md](./git_workflow.md) | Git 협업 워크플로 | 유효 |

## 배포 방향

- 운영: 웹(서버) 배포. 엔지니어가 룰/baseline/Prompt/DB를 한 곳에서 유지보수.
- 최종: Docker (frontend + backend + qwen).
- 역할 분리: 일반 사용자(분석 화면) / 엔지니어(관리 화면) (ADM-001).

---

## 구현 진행 현황

상태: ⬜ 미착수 / 🟨 진행중(목업) / ✅ 완료

### 프론트엔드 (React, `frontend/src`)

- 🟨 USR-001~006 사용자 분석 화면 — `pages/UserAnalysis.tsx` _(목업: 업로드/실행/그래프/결과)_
- 🟨 RPT-001 리포트 화면 — `pages/Report.tsx` _(목업)_
- 🟨 ADM-002 분석 이력 — `pages/History.tsx` _(목업)_
- 🟨 ENG-001~006 엔지니어 관리 화면 — `pages/EngineerAdmin.tsx` _(목업 폼)_
- ✅ ADM-001 사용자/엔지니어 화면 분리 — `components/Layout.tsx` + `context.tsx` _(역할별 메뉴 + 접근코드)_

### 백엔드 (FastAPI, `backend/`)

- 🟨 API 스켈레톤 — `main.py` _(엔드포인트 구조만, 응답 placeholder)_
- ✅ ANA-001 파일 파싱 — `src/file_parser.py` _(CSV/XLSX -> DataFrame 변환)_
- 🟨 ANA-002 컬럼 자동 매핑 — `src/column_mapper.py`
- ⬜ ANA-003 Trip Code 분석 — `src/trip_analyzer.py`
- ⬜ ANA-004 정상 기준 비교 — `src/baseline_analyzer.py`
- ⬜ ANA-005 데이터 품질 이상 탐지 — `src/data_quality_checker.py`
- ⬜ ANA-006 최종 판정 생성 — `src/verdict_engine.py`
- ⬜ ANA-007 분석 결과 JSON 생성 — `src/result_builder.py`
- ⬜ ENG-002/004 Rule·Trip Code 관리 — `src/rule_manager.py`
- ⬜ ENG-003 정상 기준 관리 — `src/baseline_manager.py`
- ⬜ ENG-005 Prompt 관리 — `src/prompt_manager.py`
- ⬜ ENG-006 / DB-001~005 DB — `src/db_manager.py`
- ⬜ RAG-001/002 — `src/rag_engine.py`
- ⬜ LLM-001~003 (Qwen) — `src/llm_report.py`
- ⬜ RPT-002 리포트 파일 생성 — `src/report_generator.py`
- ⬜ USR-005/006 차트 데이터 — `src/chart_viewer.py` (프론트 recharts로 렌더)

---

_최종 수정: 2026-06-18_
