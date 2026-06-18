# LG_Project — LG Comp 확인 에이전트

> LGE Internal Use Only

압축기(Comp) 데이터를 업로드하면 **Trip / baseline 이탈 / 데이터 품질**을 자동 분석하여
**PASS · 관리필요 · FAIL** 판정과 LLM 기반 리포트를 생성하는 사내 분석 에이전트입니다.

---

## 프로젝트 방향성

- **목표**: 엔지니어의 수기 판정·리포트 작성을 자동화하여, 누구나 CSV/XLSX만 올리면 일관된 기준으로 진단·리포트를 받게 한다.
- **두 종류의 사용자**
  - *일반 사용자* — 파일 업로드 → 분석 → 결과·그래프·리포트 확인 (분석 화면만)
  - *엔지니어* — Trip Code·Rule·정상 기준(baseline)·Prompt 등록/수정 및 DB 반영 (관리 화면까지)
- **판정 + 근거**: 규칙 기반 분석(Trip/baseline/품질) 결과를 RAG(과거 사례·가이드)와 결합해 LLM이 원인 후보·조치 권고를 작성.
- **운영 형태**: **웹(서버) 배포**로 룰·baseline을 한 곳에서 유지보수 → 모든 사용자에게 즉시 반영.
- **최종 배포**: **Docker 컨테이너**로 사내 서버에 배포 (앱 + 로컬 LLM).
- **보안**: LLM·임베딩 모두 **사내/로컬 모델**을 사용하여 분석 데이터가 외부로 나가지 않는다.

자세한 기능 정의는 [docs/functional_spec.md](docs/functional_spec.md), 진행 현황은 [docs/README.md](docs/README.md) 참고.

---

## 기술 스택

| 영역 | 선택 | 비고 |
|------|------|------|
| UI / 웹 | **Streamlit** | 멀티페이지(`pages/`) 구조 |
| 데이터 처리 | **pandas / numpy / openpyxl** | CSV·XLSX 파싱 |
| 시각화 | **Plotly** | 시계열 그래프, 이상 구간 표시 |
| DB | **SQLite + SQLAlchemy** | 기본값. 접속 문자열만 바꿔 PostgreSQL 전환 가능 |
| RAG 벡터DB | **ChromaDB** | 로컬 저장/검색 |
| 임베딩 | **sentence-transformers** | 로컬 실행(외부 유출 없음), 한국어 모델 권장 |
| LLM | **사내/로컬 모델 (Ollama 등)** | HTTP 호출, 데이터 외부 전송 없음 |
| 리포트 | **Jinja2 + WeasyPrint** | HTML → PDF |
| 설정 | **pydantic-settings + .env** | |
| 배포 | **Docker / docker-compose** | app + ollama 컨테이너 |

---

## 폴더 구조

```
LG_Project/
├── app.py                  # 메인 엔트리 / 화면 분리 (ADM-001)
├── pages/                  # Streamlit 페이지
│   ├── user_analysis.py    # 사용자 분석 화면
│   ├── engineer_admin.py   # 엔지니어 관리 화면
│   ├── report.py           # 리포트 화면
│   └── history.py          # 분석 이력
├── src/                    # 핵심 로직 모듈
│   ├── config.py           # 환경 설정 로더
│   ├── file_parser.py      # 파일 파싱
│   ├── column_mapper.py    # 컬럼 자동 매핑
│   ├── trip_analyzer.py    # Trip Code 분석
│   ├── baseline_analyzer.py
│   ├── data_quality_checker.py
│   ├── verdict_engine.py   # 최종 판정
│   ├── result_builder.py   # 결과 JSON
│   ├── chart_viewer.py
│   ├── rule_manager.py / baseline_manager.py / prompt_manager.py
│   ├── db_manager.py       # DB 입출력
│   ├── rag_engine.py       # 벡터 저장/검색
│   ├── llm_report.py       # LLM 요약/원인/조치
│   └── report_generator.py # HTML/PDF 생성
├── prompts/report_prompt.txt
├── rules/default_rules.json
├── data/                   # uploads / reports / chroma (gitignore)
├── docs/                   # 명세서(프론트/백)·진행관리 문서
├── pyproject.toml          # uv 의존성 정의 (개발 기준)
├── uv.lock                 # uv 잠금 파일 (uv sync 시 생성)
├── requirements.txt        # Docker 빌드용 (pyproject 미러)
├── .env.example
├── Dockerfile / docker-compose.yml / .dockerignore
└── README.md
```

---

## 환경 설정 방법

### A. 로컬 개발 환경 (uv 사용)

의존성·가상환경 관리는 **[uv](https://docs.astral.sh/uv/)** 를 사용합니다. (pip/venv보다 빠르고 `pyproject.toml` 기반)

**1. uv 설치** (최초 1회)
```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2. 가상환경 생성 + 의존성 설치 (한 번에)**
```bash
uv sync
```
- `pyproject.toml`을 읽어 `.venv/`를 만들고 의존성을 설치합니다. (Python 3.11이 없으면 uv가 자동 설치)
- 최초 실행 시 `uv.lock`이 생성됩니다.
- PostgreSQL을 쓸 경우: `uv sync --extra postgres`
- 개발 도구(ruff/pytest)까지: `uv sync --extra dev`

**3. 환경 변수 설정**
```bash
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```
`.env`를 열어 DB·LLM·임베딩 값을 환경에 맞게 수정합니다.

> WeasyPrint(PDF)는 Windows에서 GTK 런타임이 필요할 수 있습니다. PDF 기능을 당장 안 쓰면 건너뛰어도 됩니다.

**4. 로컬 LLM 준비 (Ollama 예시)**
```bash
# Ollama 설치 후 모델 받기
ollama pull llama3.1:8b
ollama serve            # http://localhost:11434
```

**5. 앱 실행**
```bash
uv run streamlit run app.py
```
브라우저에서 `http://localhost:8501` 접속. (`uv run`은 `.venv`를 자동 활성화해 실행합니다)

### B. Docker 배포 (최종)

```bash
# 1. .env 준비 (위 4번과 동일)
# 2. 빌드 및 실행 (앱 + ollama 동시 기동)
docker compose up -d --build

# 3. LLM 모델 컨테이너에 내려받기 (최초 1회)
docker exec -it lgproject-ollama ollama pull llama3.1:8b
```
접속: `http://<서버주소>:8501`

종료/정리:
```bash
docker compose down          # 중지
docker compose logs -f app   # 로그 확인
```

> **PostgreSQL로 전환**하려면: `docker-compose.yml`의 `db` 서비스와 `requirements.txt`의 `psycopg2-binary` 주석을 해제하고, `.env`의 `DB_URL`을 PostgreSQL 주소로 변경하세요.

---

_최종 수정: 2026-06-18_
