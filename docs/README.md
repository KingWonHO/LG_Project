# 프로젝트 문서 (docs)

> LGE Internal Use Only

## 아키텍처

React(shadcn/ui) 프론트 → FastAPI 백엔드 → 로컬 Ollama LLM(gemma3:4b). DB: SQLite/SQLAlchemy, RAG: ChromaDB + 로컬 임베딩(sentence-transformers).

## 문서 목록

| 문서 | 설명 | 상태 |
|------|------|------|
| [functional_spec.md](./functional_spec.md) | 기능 명세 (기능 ID 매핑) | ✅ |
| [frontend_spec.md](./frontend_spec.md) | 프론트 명세 (React/shadcn) | ✅ |
| [backend_spec.md](./backend_spec.md) | 백엔드 명세 (FastAPI/Ollama) | ✅ |
| [git_workflow.md](./git_workflow.md) | Git 협업 워크플로 | ✅ |
| [ollama_setup.md](./ollama_setup.md) | Ollama(로컬 LLM) 설치·연결 가이드 | ✅ |
| [todo_next.md](./todo_next.md) | 남은 작업 목록 | ✅ |

---

## 구현 진행 현황

상태: ⬜ 미착수 / 🟨 진행중 / ✅ 완료

### 프론트엔드 (React, `frontend/`)
- ✅ 화면 4종(사용자분석/리포트/이력/엔지니어) + 사이드바·역할분리(ADM-001)
- ✅ API 클라이언트(`lib/api.ts`) + vite 프록시(`/api`→8000)
- ✅ 사용자분석 → `POST /api/analyze` 실 CSV/XLSX 분석 (USR-001~004)
- ✅ 컬럼명 인덱스 매핑 — `lib/columnSchema.ts`(trip_case.json schema_reference 번들), 엑셀 헤더 대신 column_index → canonical_name
- ✅ 평압/차압(NODPS/DPS) 토글 → 인덱스 9·16·17 컬럼명 즉시 전환 (`UserAnalysis.tsx`)
- ✅ 컴프 모델 선택(Comp_Parameter.json) → 평압/차압 옆 드롭다운 + 선택 모델 파라미터 표시 + analyze에 `comp_model` 전달 (판정 로직 적용은 규칙 정의 후)
- ✅ 다중 그래프: "그래프 추가" 버튼 + 그래프별 컬럼 선택, 분석결과(위)/그래프(아래) 레이아웃
- ✅ 그래프 시간축 확대/이동 — recharts `Brush`
- ✅ 발생 Trip Code 표시 — 클라 파싱(idx20 고유값) → 엔지니어 DB 정의로 코드→이름 매핑
- ✅ 분석이력 → `GET /api/history` 목록 + `GET /api/history/{id}` 상세(차트 복원)
- ✅ 분석이력 삭제 → `DELETE /api/history/{id}` (사이드바 항목 X 버튼)
- ✅ 엔지니어 관리 → trip-codes/baseline/prompt `GET·PUT` + **RAG 재인덱싱**(`POST /api/rag/index`)
- ✅ 리포트 → `POST /api/report` 로컬 LLM 요약 + **RAG 참고자료 패널**(RAG-002)
- ✅ 사용자분석/리포트 화면 상태 유지(context) — 화면 이동 후 복귀 시 유지
- 🟨 학습 탭(정상 baseline 자동 학습) — 백엔드 미구현으로 "추후 제공" placeholder

### 백엔드 (FastAPI, `backend/`)
- ✅ 엔드포인트: health / analyze(+comp_model) / compressors / history / history/{id} / history/{id}(DELETE) / trip-codes / baseline / rules / prompt / report / rag/index
- ✅ 컴프 파라미터 서빙: `GET /api/compressors` (data/agentData/Comp_Parameter.json) — 모델·파라미터·정의
- ✅ 분석 파이프라인 연결(ANA-001~007): parse→map→trip/baseline→verdict→result_builder (+차트 series)
- ✅ DB(SQLAlchemy): 파일·분석결과·TripCode·baseline·Prompt (DB-001~005) + 분석결과 삭제
- ✅ RAG(RAG-001/002): `rag_engine`(ChromaDB+sentence-transformers) → report에 컨텍스트 주입 + 수동 재인덱싱
- ✅ LLM(LLM-001): `llm_report` 로컬 Ollama(gemma3:4b) 요약, 실패 시 rule-based 폴백
- ⬜ ANA-005 데이터 품질(`data_quality_checker.py` 빈 스텁) → quality 0 고정
- ⬜ baseline 자동 학습(학습 탭용) 엔드포인트
- ⬜ RPT-002 리포트 PDF 생성
- ⬜ LLM-002/003 원인·조치 분리 출력

### 환경/배포
- ✅ uv 환경(pyproject), Ollama 설치·연결 가이드, Docker(compose: backend/frontend/qwen)

---

## 핵심 플로우 상태

업로드 → 실 CSV/XLSX 분석(판정·트립코드·차트) → 이력 누적/삭제 → LLM+RAG 리포트 생성: **end-to-end 동작**.
엔지니어가 Trip Code 수정 → RAG 재인덱싱 → 리포트 참고자료에 최신 반영.

---

_최종 수정: 2026-07-03_
