# 다음 작업 리스트 (TODO)

> LGE Internal Use Only · 최종 정리: 2026-07-13
> 초기 연결 단계 완료. 아래는 다음에 진행할 항목.

## 현재 상태 요약

- 프론트 ↔ 백엔드 연결: **완료** (업로드→분석→판정→이력→리포트 실데이터 end-to-end)
- `/api/analyze` → src 분석 파이프라인 연결 완료 (parse→map→noise_filter→trip/baseline→verdict→result_builder)
- 로컬 LLM(gemma3:4b, Ollama) 리포트 요약 + 분석 대화(`/api/chat`) 동작
- RAG(rag_engine) 검색 + 리포트 참고자료 패널 + 수동 재인덱싱 동작
- 이력 상세/삭제, 화면 상태 유지(사용자분석·리포트) 완료

## 남은 미구현 기능 (전용 모듈 없음 — 신규 구현 필요)

> 아래 항목은 과거 빈 스텁 파일(`data_quality_checker`/`report_generator`/`rule_manager`/`prompt_manager`/`baseline_manager`/`chart_viewer`)로 존재했으나 미구현 상태라 **삭제됨**. 구현 시 신규 모듈로 추가한다.

| 기능 | 현재 영향 | 비고 |
|------|-----------|------|
| ANA-005 데이터 품질 검사 | quality 항상 0 (missing/outliers 미산출) | 신규 모듈 필요 |
| RPT-002 PDF/HTML 리포트 | 리포트 파일 생성 불가 (현재 .md 다운로드만) | 신규 모듈 필요 |
| ENG-004 Rule JSON 저장 | `/api/rules` PUT 가 no-op | GET은 `engineer_rules`가 처리 |
| ENG-003 baseline / ENG-005 Prompt | 정상 동작 | `db_manager`가 직접 처리(별도 manager 불필요) |
| 백엔드 차트 | 불필요 | 차트는 프론트 recharts 담당 |

## 프론트 측 다음 작업

1. 분석 진행 표시(대용량 파일 파싱 10~20초 소요) — 로딩 스피너/상태 메시지
2. 에러 처리 — 잘못된 파일 업로드(400) 시 사용자 안내 토스트

> 완료됨: 트립코드 식별 표시(코드→이름 매핑), 이력 상세 조회(`GET /api/history/{id}`).

## 운영/환경 이슈

- **V3 백신 실시간 검사로 소스 파일 손상(중간 절단) 재발** → IT에 `D:\LG\LG_Project` 실시간/행위기반 검사 예외 요청 (관리자 정책 잠김으로 본인 설정 불가)
- 작업 중 정상 상태에서 자주 커밋, 손상 시 `git restore <파일>`로 복구

## 참고: 정상 동작 검증값 (회귀 테스트용)

| 파일 | 행수 | trip | 판정 |
|------|------|------|------|
| 정상데이터.xlsx | 41,483 | 1 | 관리필요 |
| PCB변경_발생많음.xlsx | 108,657 | 11 | FAIL |
| PCB변경_발생적음.xlsx | 106,445 | - | 관리필요 |

> baseline 이탈 판정은 엔지니어 화면에서 정상기준(min/max) 등록 시에만 반영됨.
