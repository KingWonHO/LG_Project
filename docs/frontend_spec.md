# 프론트엔드 명세서 (Frontend Specification)

> LGE Internal Use Only
> 대상: Streamlit 기반 화면(UI) 계층

화면(페이지) 구성, 사용자 인터랙션, 표시 요소를 정의한다. 비즈니스 로직은 [backend_spec.md](./backend_spec.md)의 `src/` 모듈에 위임하며, 프론트엔드는 **입력 수집 · 호출 · 결과 표시**만 담당한다.

---

## 1. 기술 스택 (Frontend)

| 영역 | 사용 |
|------|------|
| 프레임워크 | Streamlit (멀티페이지 `pages/`) |
| 시각화 | Plotly (시계열·이상 구간) |
| 상태 관리 | `st.session_state` |
| 화면 분리 | `app.py` (사용자/엔지니어 접근 구분) |

---

## 2. 화면 구성

### 2.1 메인 / 라우팅 — `app.py`

| 기능 ID | 내용 |
|---------|------|
| ADM-001 | 사용자/엔지니어 화면 분리. 일반 사용자는 분석 화면만, 엔지니어는 관리 화면까지 접근 (접근 코드/권한 확인) |

### 2.2 사용자 분석 화면 — `pages/user_analysis.py`

레이아웃: 상단 탭(분석/학습) → 좌측(업로드·옵션·그래프) / 우측(평압·Pass/Fail·결과·리포트)

| 기능 ID | 요소 | 설명 |
|---------|------|------|
| USR-001 | CSV/XLSX 업로드 | `st.file_uploader`로 파일 수신 → 백엔드 `file_parser` 호출 |
| USR-002 | 분석 실행 | 실행 버튼 → `trip_analyzer`/`verdict_engine` 호출 |
| USR-003 | 컬럼 선택 | 컴프·전압·RT 드롭다운 + 컬럼 멀티셀렉트 |
| USR-004 | 결과 표시 | PASS·관리필요·FAIL·데이터품질이상 배지/표 |
| USR-005 | 그래프 표시 | 시계열 그래프 (`chart_viewer` 렌더 결과) |
| USR-006 | 이상 구간 표시 | Trip 발생/baseline 이탈 구간 하이라이트 |

### 2.3 엔지니어 관리 화면 — `pages/engineer_admin.py`

| 기능 ID | 요소 | 설명 |
|---------|------|------|
| ENG-001 | 정상 데이터 업로드 | baseline 생성용 정상 데이터 업로드 UI |
| ENG-002~005 | 등록/수정 폼 | Trip Code·정상 기준·Rule JSON·Prompt 입력 폼 (백엔드 manager 호출) |
| ENG-006 | DB 반영 | 수정 내용을 DB에 저장하는 버튼 |

> 접근 제어: `ENGINEER_ACCESS_CODE`(`.env`)로 보호. 권한 없는 사용자는 진입 불가.

### 2.4 리포트 화면 — `pages/report.py`

| 기능 ID | 요소 | 설명 |
|---------|------|------|
| RPT-001 | 리포트 출력 | 분석 요약·Trip 분석·이상 항목·원인 후보·조치 권고 표시 |
| (연계) | 파일 다운로드 | 백엔드 `report_generator`가 만든 HTML/PDF 다운로드 버튼 |

### 2.5 분석 이력 화면 — `pages/history.py`

| 기능 ID | 요소 | 설명 |
|---------|------|------|
| ADM-002 | 이력 조회 | 과거 업로드 파일·분석 결과 목록 조회 및 재열람 |

---

## 3. 화면 ↔ 백엔드 호출 흐름

```
[user_analysis] 업로드 → file_parser.parse()
                실행   → trip_analyzer / baseline_analyzer / data_quality_checker
                        → verdict_engine.judge() → result_builder.build()
                그래프 → chart_viewer.render()
[report]        리포트 → llm_report → report_generator.generate()
[engineer_admin] 저장 → rule/baseline/prompt_manager → db_manager
[history]       조회   → db_manager
```

---

## 4. UI 상태 (session_state) 표준 키

| 키 | 의미 |
|----|------|
| `raw_df` | 업로드된 원본 DataFrame |
| `analysis_result` | 분석 결과(JSON/DataFrame) |
| `verdict` | 최종 판정 (PASS/관리필요/FAIL) |
| `report_bytes` | 생성된 리포트 파일 바이트 |

---

_최종 수정: 2026-06-18_
