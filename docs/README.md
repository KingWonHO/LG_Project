# 프로젝트 문서 (docs)

> LGE Internal Use Only

분석 자동화 프로젝트의 문서 모음입니다.

## 문서 목록

| 문서 | 설명 |
|------|------|
| [functional_spec.md](./functional_spec.md) | 기능 명세서 (전체 기능 ID / 코드 구현 매핑) |
| [frontend_spec.md](./frontend_spec.md) | 프론트엔드 명세서 (Streamlit 화면/UI 계층) |
| [backend_spec.md](./backend_spec.md) | 백엔드 명세서 (src 로직·DB·RAG·LLM 계층) |
| [git_workflow.md](./git_workflow.md) | Git 협업 워크플로 (브랜치·PR·머지 순서) |

## 배포 방향

- **운영 형태**: 웹(서버) 배포 — 엔지니어가 룰/baseline/Prompt/DB를 한 곳에서 유지보수
- **최종 배포**: Docker 컨테이너로 사내 서버에 배포
- 일반 사용자는 분석 화면만, 엔지니어는 DB 업데이트 화면까지 접근 (ADM-001)

---

## 구현 진행 현황

상태 표기: ⬜ 미착수 / 🟨 진행중 / ✅ 완료

### 사용자 화면 (USR)

- 🟨 USR-001 CSV/XLSX 파일 업로드 — `pages/user_analysis.py` _(UI 골격 완료, XLSX 지원 추가 필요)_
- 🟨 USR-002 분석 실행 — `pages/user_analysis.py` _(UI 완료, 실제 로직 연결 필요)_
- 🟨 USR-003 컬럼 선택 — `pages/user_analysis.py`
- 🟨 USR-004 분석 결과 표시 — `pages/user_analysis.py`
- ⬜ USR-005 그래프 표시 — `src/chart_viewer.py`
- ⬜ USR-006 이상 구간 표시 — `src/chart_viewer.py`

### 분석 기능 (ANA)

- ⬜ ANA-001 파일 파싱 — `src/file_parser.py`
- ⬜ ANA-002 컬럼 자동 매핑 — `src/column_mapper.py`
- ⬜ ANA-003 Trip Code 분석 — `src/trip_analyzer.py`
- ⬜ ANA-004 정상 기준 비교 — `src/baseline_analyzer.py`
- ⬜ ANA-005 데이터 품질 이상 탐지 — `src/data_quality_checker.py`
- ⬜ ANA-006 최종 판정 생성 — `src/verdict_engine.py`
- ⬜ ANA-007 분석 결과 JSON 생성 — `src/result_builder.py`

### 엔지니어 화면 (ENG)

- ⬜ ENG-001 정상 데이터 업로드 — `pages/engineer_admin.py`
- ⬜ ENG-002 Trip Code 등록/수정 — `src/rule_manager.py`
- ⬜ ENG-003 정상 기준 등록/수정 — `src/baseline_manager.py`
- ⬜ ENG-004 Rule JSON 등록/수정 — `src/rule_manager.py`
- ⬜ ENG-005 Prompt 등록/수정 — `src/prompt_manager.py`
- ⬜ ENG-006 DB 업데이트 — `src/db_manager.py`

### DB 기능 (DB)

- ⬜ DB-001 파일 정보 저장 — `src/db_manager.py`
- ⬜ DB-002 분석 결과 저장 — `src/db_manager.py`
- ⬜ DB-003 Trip Code DB 저장 — `src/db_manager.py`
- ⬜ DB-004 정상 기준 DB 저장 — `src/db_manager.py`
- ⬜ DB-005 Prompt 저장 — `src/db_manager.py`

### RAG 기능 (RAG)

- ⬜ RAG-001 지식 데이터 저장 — `src/rag_engine.py`
- ⬜ RAG-002 유사 근거 검색 — `src/rag_engine.py`

### LLM 기능 (LLM)

- ⬜ LLM-001 분석 요약 생성 — `src/llm_report.py`
- ⬜ LLM-002 원인 후보 생성 — `src/llm_report.py`
- ⬜ LLM-003 조치 권고 생성 — `src/llm_report.py`

### 리포트 기능 (RPT)

- ⬜ RPT-001 리포트 화면 출력 — `pages/report.py`
- ⬜ RPT-002 리포트 파일 생성 — `src/report_generator.py`

### 관리 기능 (ADM)

- ✅ ADM-001 사용자/엔지니어 화면 분리 — `app.py` _(st.navigation 역할별 노출 + 접근코드 게이팅)_
- 🟨 ADM-002 분석 이력 조회 — `pages/history.py` _(페이지 골격 완료, db_manager 연동 필요)_

---

_최종 수정: 2026-06-18_
