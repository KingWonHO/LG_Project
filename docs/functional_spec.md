# 기능 명세서 (Functional Specification)

> LGE Internal Use Only
> 배포 형태: **웹(서버) 배포 → 최종 Docker 컨테이너 배포**

본 문서는 프로젝트의 기능 명세를 정의한다. 기능은 대분류별로 그룹화되며, 각 기능은 고유 ID와 코드 구현 위치를 가진다.

---

## 1. 사용자 화면 (USR)

| 기능 ID | 기능명 | 기능설명 | 코드 구현 |
|---------|--------|----------|-----------|
| USR-001 | CSV/XLSX 파일 업로드 | 사용자가 분석할 CSV 또는 Excel 파일을 업로드한다. | `pages/user_analysis.py` |
| USR-002 | 분석 실행 | 업로드된 파일을 기준으로 분석을 시작한다. | `pages/user_analysis.py` |
| USR-003 | 컬럼 선택 | 컴프, 전압, RT 등 분석에 사용할 주요 컬럼을 선택한다. | `pages/user_analysis.py` |
| USR-004 | 분석 결과 표시 | PASS, 관리필요, FAIL, 데이터품질이상 결과를 화면에 표시한다. | `pages/user_analysis.py` |
| USR-005 | 그래프 표시 | 주요 데이터 컬럼을 시계열 그래프로 표시한다. | `src/chart_viewer.py` |
| USR-006 | 이상 구간 표시 | Trip 발생 구간 또는 baseline 이탈 구간을 그래프와 표에 표시한다. | `src/chart_viewer.py` |

## 2. 분석 기능 (ANA)

| 기능 ID | 기능명 | 기능설명 | 코드 구현 |
|---------|--------|----------|-----------|
| ANA-001 | 파일 파싱 | CSV/XLSX 파일을 읽고 데이터프레임 형태로 변환한다. | `src/file_parser.py` |
| ANA-002 | 컬럼 자동 매핑 | 파일마다 다른 컬럼명을 표준 컬럼명으로 매핑한다. | `src/column_mapper.py` |
| ANA-003 | Trip Code 분석 | Trip_Code가 0이 아닌 데이터를 탐지하고 발생 횟수와 구간을 계산한다. | `src/trip_analyzer.py` |
| ANA-004 | 정상 기준 비교 | 정상 baseline과 업로드 데이터를 비교하여 관리 필요 여부를 판단한다. | `src/baseline_analyzer.py` |
| ANA-005 | 데이터 품질 이상 탐지 | 비정상적으로 큰 값, 누락값, 파싱 오류 가능성이 있는 데이터를 탐지한다. | `src/data_quality_checker.py` |
| ANA-006 | 최종 판정 생성 | Trip, baseline, 데이터 품질 결과를 종합하여 PASS/관리필요/FAIL을 결정한다. | `src/verdict_engine.py` |
| ANA-007 | 분석 결과 JSON 생성 | 화면 표시와 리포트 생성을 위한 표준 JSON 결과를 생성한다. | `src/result_builder.py` |

## 3. 엔지니어 화면 (ENG)

| 기능 ID | 기능명 | 기능설명 | 코드 구현 |
|---------|--------|----------|-----------|
| ENG-001 | 정상 데이터 업로드 | 엔지니어가 정상 baseline 생성을 위한 정상 데이터를 업로드한다. | `pages/engineer_admin.py` |
| ENG-002 | Trip Code 등록/수정 | Trip Code별 의미, 원인, 조치 방법을 등록하거나 수정한다. | `src/rule_manager.py` |
| ENG-003 | 정상 기준 등록/수정 | Iqe, CoolingPower, Initial_Delay 등 주요 항목의 정상 기준을 등록하거나 수정한다. | `src/baseline_manager.py` |
| ENG-004 | Rule JSON 등록/수정 | 이상 판단에 사용할 Rule JSON을 등록하거나 수정한다. | `src/rule_manager.py` |
| ENG-005 | Prompt 등록/수정 | LLM 리포트 생성을 위한 프롬프트를 등록하거나 수정한다. | `src/prompt_manager.py` |
| ENG-006 | DB 업데이트 | 엔지니어가 수정한 Trip Code, Rule, Prompt, baseline 정보를 DB에 반영한다. | `src/db_manager.py` |

## 4. DB 기능 (DB)

| 기능 ID | 기능명 | 기능설명 | 코드 구현 |
|---------|--------|----------|-----------|
| DB-001 | 파일 정보 저장 | 업로드 파일명, 경로, 업로드 시간, 행 수, 분석 상태를 저장한다. | `src/db_manager.py` |
| DB-002 | 분석 결과 저장 | 분석 판정, 이상 항목, Trip 정보, 리포트 내용을 저장한다. | `src/db_manager.py` |
| DB-003 | Trip Code DB 저장 | Trip Code별 설명, 원인, 조치 가이드를 저장한다. | `src/db_manager.py` |
| DB-004 | 정상 기준 DB 저장 | baseline 기준값과 feature별 정상 범위를 저장한다. | `src/db_manager.py` |
| DB-005 | Prompt 저장 | 리포트 생성용 프롬프트 버전을 저장한다. | `src/db_manager.py` |

## 5. RAG 기능 (RAG)

| 기능 ID | 기능명 | 기능설명 | 코드 구현 |
|---------|--------|----------|-----------|
| RAG-001 | 지식 데이터 저장 | Trip Code 설명, 조치 가이드, 과거 사례 내용을 저장한다. | `src/rag_engine.py` |
| RAG-002 | 유사 근거 검색 | 분석 결과와 관련된 Trip Code 설명, Rule 설명, 과거 사례를 검색한다. | `src/rag_engine.py` |

## 6. LLM 기능 (LLM)

| 기능 ID | 기능명 | 기능설명 | 코드 구현 |
|---------|--------|----------|-----------|
| LLM-001 | 분석 요약 생성 | 분석 JSON과 RAG 검색 결과를 바탕으로 요약 문장을 생성한다. | `src/llm_report.py` |
| LLM-002 | 원인 후보 생성 | Trip Code, 이상 항목, baseline 이탈 내용을 바탕으로 원인 후보를 생성한다. | `src/llm_report.py` |
| LLM-003 | 조치 권고 생성 | 엔지니어 DB와 RAG 근거를 바탕으로 점검 항목과 조치 방향을 작성한다. | `src/llm_report.py` |

## 7. 리포트 기능 (RPT)

| 기능 ID | 기능명 | 기능설명 | 코드 구현 |
|---------|--------|----------|-----------|
| RPT-001 | 리포트 화면 출력 | 분석 요약, Trip 분석, 이상 항목, 원인 후보, 조치 권고를 화면에 표시한다. | `pages/report.py` |
| RPT-002 | 리포트 파일 생성 | 분석 결과를 HTML 또는 PDF 파일로 생성한다. | `src/report_generator.py` |

## 8. 관리 기능 (ADM)

| 기능 ID | 기능명 | 기능설명 | 코드 구현 |
|---------|--------|----------|-----------|
| ADM-001 | 사용자/엔지니어 화면 분리 | 일반 사용자는 분석 화면만, 엔지니어는 DB 업데이트 화면까지 접근하도록 구분한다. | `app.py` |
| ADM-002 | 분석 이력 조회 | 과거 업로드 파일과 분석 결과를 다시 조회한다. | `pages/history.py` |

---

_최종 수정: 2026-06-18_
