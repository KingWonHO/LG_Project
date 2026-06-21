# 프로젝트 문서 (docs)

> LGE Internal Use Only

## 아키텍처

React(shadcn/ui) 프론트 → FastAPI 백엔드 → Ollama 기반 로컬 LLM.  
DB: SQLite/SQLAlchemy, RAG: ChromaDB + 로컬 임베딩.

LLM 분석 요약 기능은 외부 API 키를 사용하지 않고, 로컬 PC 또는 사내 서버에서 Ollama 모델을 실행하는 방식으로 구성한다. 기본 모델은 `gemma3:4b`이며, 대체 모델로 `qwen2.5:3b`, `llama3.2`를 사용할 수 있다.

## 문서 목록

| 문서 | 설명 | 상태 |
|------|------|------|
| [functional_spec.md](./functional_spec.md) | 기능 명세 (기능 ID 매핑) | ✅ 유효 (React/FastAPI) |
| [frontend_spec.md](./frontend_spec.md) | 프론트 명세 (React/shadcn) | ✅ 유효 |
| [backend_spec.md](./backend_spec.md) | 백엔드 명세 (FastAPI/Ollama Local LLM) | ✅ 유효 |
| [git_workflow.md](./git_workflow.md) | Git 협업 워크플로 | ✅ 유효 |

## 배포 방향

- 운영: 웹(서버) 배포. 엔지니어가 룰/baseline/Prompt/DB를 한 곳에서 유지보수.
- 최종: Docker (frontend + backend + ollama/local-llm).
- 역할 분리: 일반 사용자(분석 화면) / 엔지니어(관리 화면) (ADM-001).

---

## 로컬 LLM 설정

분석 요약 기능(`LLM-001`)은 Ollama를 사용해 로컬 LLM을 호출한다.  
분석 모듈에서 생성된 JSON 결과와 RAG 검색 결과를 입력으로 받아, 사용자가 이해하기 쉬운 한국어 분석 요약문을 생성한다.

### 사용 모델 우선순위

| 우선순위 | 모델명 | 용도 |
|---:|---|---|
| 1 | `gemma3:4b` | 기본 모델. 한국어 요약 품질과 보고서 문장 안정성이 가장 우수 |
| 2 | `qwen2.5:3b` | Qwen 계열 대체 모델. 한국어 요약 품질이 준수하고 비교적 가벼움 |
| 3 | `llama3.2` | 경량 대체 모델. 실행 속도는 빠르지만 요약 중복 가능성이 있음 |

### 모델 다운로드

```powershell
ollama pull gemma3:4b
ollama pull qwen2.5:3b
ollama pull llama3.2
```

다운로드된 모델 목록 확인:

```powershell
ollama list
```

사용하지 않는 모델 삭제:

```powershell
ollama rm 모델명
```

예시:

```powershell
ollama rm qwen2.5:3b
```

### Backend 의존성 설치

`backend` 폴더에서 실행한다.

```powershell
cd backend
uv sync
uv add ollama
```

이미 `ollama` 의존성이 추가되어 있다면 `uv sync`만 실행해도 된다.

### 기본 모델

기본 모델은 `backend/src/llm_report.py`에서 관리한다.

```python
DEFAULT_LOCAL_MODEL = "gemma3:4b"
```

환경변수 `LOCAL_LLM_MODEL`을 설정하면 기본 모델 대신 다른 모델을 사용할 수 있다.

PowerShell 예시:

```powershell
$env:LOCAL_LLM_MODEL="qwen2.5:3b"
```

또는:

```powershell
$env:LOCAL_LLM_MODEL="llama3.2"
```

환경변수를 설정하지 않으면 `gemma3:4b`가 사용된다.

### LLM 요약 기능 테스트

`backend` 폴더에서 실행한다.

```powershell
uv run python test_llm_report.py
```

테스트 파일은 후보 모델별 분석 요약 결과를 출력한다.

### GPU 사용 확인

Ollama는 지원되는 GPU와 정상적인 드라이버가 있으면 자동으로 GPU를 사용한다.  
Python 코드에서 별도로 `cuda` 설정을 할 필요는 없다.

모델 실행 중 다른 PowerShell에서 아래 명령어로 확인한다.

```powershell
nvidia-smi -l 1
```

출력에 `ollama.exe`가 표시되고 GPU 메모리 사용량이 증가하면 GPU를 사용 중인 것이다.

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
- 🟨 LLM-001 분석 요약 생성 — `src/llm_report.py` _(Ollama 로컬 LLM 연동, 기본 모델: gemma3:4b)_
- ⬜ LLM-002 원인 후보 설명 생성 — `src/llm_report.py`
- ⬜ LLM-003 개선 Action 설명 생성 — `src/llm_report.py`
- ⬜ RPT-002 리포트 파일 생성 — `src/report_generator.py`
- ⬜ USR-005/006 차트 데이터 — `src/chart_viewer.py` (프론트 recharts로 렌더)

---

## LLM-001 동작 흐름

```text
분석 JSON + RAG 검색 결과
        ↓
backend/src/llm_report.py
        ↓
Ollama 로컬 LLM 호출
        ↓
한국어 분석 요약문 생성
```

생성되는 요약문에는 다음 내용이 포함된다.

- 최종 판정
- Trip 발생 여부 및 횟수
- 주요 이상 항목
- baseline 이탈 항목
- RAG 근거 기반 원인 후보
- 우선 점검해야 할 개선 Action

---

_최종 수정: 2026-06-21_
