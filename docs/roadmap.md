# 완성까지 로드맵 / 체크리스트

> 목표: 업로드 → **실분석** → 판정/그래프 → 이력 → **RAG+LLM 리포트(PDF)** 까지 완전 동작 + Docker 배포.
> 단계는 위에서 아래로 진행. 각 항목 완료 시 `[x]` 체크.

---

## ✅ Phase 0 — 기반 (완료)
- [x] 프론트(React/shadcn) 4화면 + 역할분리(ADM-001)
- [x] 백엔드 FastAPI 엔드포인트 + DB(SQLAlchemy) + 로컬 LLM(Ollama) 연결
- [x] 프론트↔백 연동: analyze / history / trip-codes / baseline / prompt / report
- [x] 환경(uv·Ollama)·문서·Docker 골격

---

## ☐ Phase 1 — 백엔드 실분석 파이프라인
> 현재 `/api/analyze`는 고정 더미값. 아래를 구현해 **진짜 판정**이 나오게 한다.
- [x] ANA-001 `file_parser.py` — CSV/XLSX → DataFrame (인코딩/구분자 대응)
- [x] ANA-002 `column_mapper.py` — 파일별 컬럼명 → 표준 컬럼명 매핑
- [x] ANA-003 `trip_analyzer.py` — Trip_Code≠0 탐지, 발생 횟수·구간
- [ ] ANA-004 `baseline_analyzer.py` — baseline 대비 이탈 판단 (DB baseline 사용)
- [ ] ANA-005 `data_quality_checker.py` — 이상치·누락·파싱오류 탐지
- [ ] ANA-006 `verdict_engine.py` — 종합 → PASS/관리필요/FAIL
- [ ] ANA-007 `result_builder.py` — 표준 결과 JSON 생성 (+ 차트용 `series`)
- [ ] `main.py /api/analyze` 를 위 파이프라인 호출로 교체 (더미 제거)
- [ ] 실제 CSV로 판정값이 파일마다 달라지는지 확인

## ☐ Phase 2 — 화면 정합
- [ ] 그래프: `/api/analyze` 응답의 `series`로 실제 시계열 표시 (프론트 임시 데이터 제거)
- [ ] 이상 구간(USR-006): 응답 `trip.ranges` 다중 구간 하이라이트
- [ ] 이력 상세: 백엔드 `GET /api/history/{id}` 추가 → 프론트 이력 클릭 시 전체 결과 표시
- [ ] 분석결과 카드: 실응답 필드로 정리 (이미 연동, 값만 실데이터로)

## ☐ Phase 3 — RAG + 리포트 고도화
- [ ] RAG-001 `rag_engine.py` — Trip Code 설명·조치·과거사례 임베딩 후 Chroma 저장
- [ ] RAG-002 — 분석결과 관련 근거 검색
- [ ] LLM-002/003 — 원인 후보·조치 권고를 (요약과 별도로) 구조화 출력
- [ ] `/api/report` 에 RAG 결과 주입 + 엔지니어 Prompt(DB) 사용
- [ ] RPT-002 `report_generator.py` — 결과 → HTML/PDF 생성 + 다운로드 버튼 연결

## ☐ Phase 4 — 엔지니어/관리 마무리
- [ ] ENG-001 정상 데이터 업로드 → baseline 생성 엔드포인트/로직
- [ ] ENG-004 Rule JSON 저장 로직(`rule_manager`) 실제 반영
- [ ] 엔지니어 접근 인증을 목업 코드(1234) → 백엔드 검증으로 교체

## ☐ Phase 5 — 품질/배포
- [ ] 백엔드 단위 테스트(pytest) — 파서/판정/매핑
- [ ] 프론트 빌드 확인(`npm run build`) + 타입 에러 0
- [ ] Docker `docker compose up` 전체 동작 (frontend+backend+ollama)
- [ ] README/스펙 최종 갱신, 데모 시나리오 정리

---

## 진행 방식
- 한 Phase = 한 feature 브랜치 (예: `feature/backend-analysis-pipeline`)
- 기능 단위로 커밋 → PR → 머지 → 다음 단계
- 막히면 해당 항목만 떼서 도움 요청

_최종 수정: 2026-06-21_
