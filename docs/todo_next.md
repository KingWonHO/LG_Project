# 다음 작업 리스트 (TODO)

> LGE Internal Use Only · 최종 정리: 2026-06-21
> 초기 연결 단계 완료. 아래는 다음에 진행할 항목.

## 현재 상태 요약

- 프론트 ↔ 백엔드 연결: **완료** (업로드→분석→판정→이력→리포트 실데이터 end-to-end)
- `/api/analyze` → src 분석 파이프라인 연결 완료 (parse→map→trip/baseline→verdict→result_builder)
- 로컬 LLM(gemma3:4b) 리포트 요약 동작
- 화면 상태 유지(사용자분석·리포트)

## 백엔드 미구현 모듈 (빈 스텁 → 담당자 구현 필요)

| 모듈 | 기능 | 영향 |
|------|------|------|
| `src/rag_engine.py` | RAG-001/002 검색 | 리포트 "원인 후보" 근거 없음 → "RAG 결과 없음" 표시 |
| `src/data_quality_checker.py` | ANA-005 품질 검사 | quality 항상 0 (missing/outliers 미산출) |
| `src/report_generator.py` | RPT-002 PDF/HTML 리포트 | 리포트 파일 생성 불가 (현재 .md 다운로드만) |
| `src/rule_manager.py` | ENG-002/004 Rule JSON | `/api/rules` 가 no-op |
| `src/prompt_manager.py` | ENG-005 프롬프트 관리 | 현재 db_manager로 대체 동작 중 |
| `src/baseline_manager.py` | ENG-003 baseline 관리 | 현재 db_manager로 대체 동작 중 |
| `src/chart_viewer.py` | (백엔드 차트) | 미사용(차트는 프론트 recharts) |

## 프론트 측 다음 작업 (내 파트)

1. **트립코드 식별 표시** — analyze 응답에 발생 트립코드 번호 추가(main.py 연결 계층에서 df 고유값 추출 + DB 트립정의 조인) 후, 화면에 "코드 7 — FO Trip / 조치" 표시
2. **이력 상세 조회** — `GET /api/history/{id}` 엔드포인트 추가 필요 → History 화면에서 과거 결과 클릭 시 상세/차트 복원
3. 분석 진행 표시(대용량 파일 파싱 10~20초 소요) — 로딩 스피너/상태 메시지
4. 에러 처리 — 잘못된 파일 업로드(400) 시 사용자 안내 토스트

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
