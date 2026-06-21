"""FastAPI 진입점 — React 프론트엔드용 REST API.

엔드포인트(main.py)는 라우팅·검증만 담당하고, 실제 분석/판정/저장/LLM 로직은
src/* 모듈을 호출한다 (기능 ID 주석 참고). src 모듈 자체는 수정하지 않는다.

실행:
    uv run uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings
from src import db_manager
from src import llm_report
# ANA-001~007 분석 파이프라인 (src 모듈 호출 전용 — 모듈 자체는 수정하지 않음)
from src import (
    file_parser,
    column_mapper,
    trip_analyzer,
    baseline_analyzer,
    verdict_engine,
    result_builder,
)

app = FastAPI(title="LG Comp 확인 에이전트 API", version="0.1.0")

# USR-003/005: 차트(series)에 기본으로 담을 주요 컬럼 (DataFrame에 없는 항목은 result_builder가 조용히 건너뜀)
DEFAULT_CHART_COLUMNS = ["Iqe", "CoolingPower", "Power", "DC_Link", "Ide", "Initial_Delay"]


def _load_baseline_ranges() -> dict[str, dict]:
    """DB에 등록된 정상 기준(ENG-003)을 baseline_analyzer 입력 형식으로 변환한다.

    {"CoolingPower": {"min": 17, "max": 23}, ...} — min/max가 모두 있는 항목만 비교 대상.
    """
    ranges: dict[str, dict] = {}
    for row in db_manager.get_all_baselines():
        if row.min_val is not None and row.max_val is not None:
            ranges[row.feature_name] = {"min": row.min_val, "max": row.max_val}
    return ranges


@app.on_event("startup")
def on_startup() -> None:
    db_manager.init_db()
    # DB-003: Trip Code 초기 데이터 시딩 (최초 1회만)
    if not db_manager.get_all_trip_codes():
        seed_path = Path(__file__).parent / "data" / "trip_case.json"
        if seed_path.exists():
            db_manager.seed_trip_codes_from_json(seed_path)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 공통
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "llm_model": settings.llm_model}


# ---------------------------------------------------------------------------
# 분석 (USR / ANA)
# ---------------------------------------------------------------------------
@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)) -> dict:
    """파일 업로드 → 분석 (ANA-001~007).

    src 분석 파이프라인을 순서대로 호출한다:
      file_parser → column_mapper → trip_analyzer / baseline_analyzer → verdict_engine → result_builder
    (data_quality(ANA-005)는 모듈 미구현 상태이므로 생략 → verdict/result_builder가 quality 없이 동작)
    """
    # 업로드 파일 디스크 저장
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    save_path = upload_dir / file.filename
    content = await file.read()
    save_path.write_bytes(content)

    # ANA-001/002: 파싱 + 표준 컬럼 매핑 (실패 시 400, DB 기록 없음)
    try:
        df = column_mapper.map_columns(file_parser.parse_file(file.filename, content))
    except file_parser.FileParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # DB-001: 파일 정보 저장 (행 수 = 파싱된 실제 행 수)
    db_file = db_manager.save_file_info(
        filename=file.filename,
        file_path=str(save_path),
        row_count=int(len(df)),
    )
    db_manager.update_file_status(db_file.id, "processing")

    try:
        # ANA-003: Trip 분석 (Trip_Code 컬럼이 없으면 트립 없음으로 처리)
        if "Trip_Code" in df.columns:
            trip = trip_analyzer.analyze_trip(df)
        else:
            trip = {"count": 0, "ranges": []}

        # ANA-004: baseline 비교 (정상 기준은 DB에서 로드 / 미등록 시 이탈 없음)
        baseline = baseline_analyzer.analyze_baseline(df, _load_baseline_ranges())

        # ANA-006: 종합 판정
        verdict = verdict_engine.analyze_verdict(trip, baseline)

        # ANA-007: 표준 결과 JSON (차트용 series 포함)
        result = result_builder.build_result(df, DEFAULT_CHART_COLUMNS, verdict, trip, baseline)

        # DB-002: 분석 결과 저장
        db_result = db_manager.save_analysis_result(
            file_id=db_file.id,
            verdict=result["verdict"],
            anomalies={"baseline": result["baseline"], "quality": result["quality"]},
            trip_info=result["trip"],
        )
        db_manager.update_file_status(db_file.id, "done")

        return {**result, "filename": file.filename, "file_id": db_file.id, "result_id": db_result.id}

    except Exception:
        db_manager.update_file_status(db_file.id, "error")
        raise


# ---------------------------------------------------------------------------
# 이력 (ADM-002)
# ---------------------------------------------------------------------------
@app.get("/api/history")
def history() -> list[dict]:
    return db_manager.get_analysis_history()


# ---------------------------------------------------------------------------
# 엔지니어 관리 (ENG / DB)
# ---------------------------------------------------------------------------
class TripCodeBody(BaseModel):
    trip_no: int
    trip_key: str
    trip_name_ko: str
    summary_ko: str
    restart_delay_s: int | None = None
    solution: dict | None = None


class BaselineBody(BaseModel):
    feature_name: str
    min_val: float | None = None
    max_val: float | None = None
    unit: str | None = None


class PromptBody(BaseModel):
    version: str
    text: str


@app.get("/api/trip-codes")
def get_trip_codes() -> list[dict]:
    rows = db_manager.get_all_trip_codes()
    return [
        {
            "trip_no": r.trip_no,
            "trip_key": r.trip_key,
            "trip_name_ko": r.trip_name_ko,
            "summary_ko": r.summary_ko,
            "restart_delay_s": r.restart_delay_s,
            "solution": r.solution,
            "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M"),
        }
        for r in rows
    ]


@app.put("/api/trip-codes")
def put_trip_codes(items: list[TripCodeBody]) -> dict:
    for item in items:
        db_manager.upsert_trip_code(
            trip_no=item.trip_no,
            trip_key=item.trip_key,
            trip_name_ko=item.trip_name_ko,
            summary_ko=item.summary_ko,
            restart_delay_s=item.restart_delay_s,
            solution=item.solution,
        )
    return {"saved": len(items)}


@app.get("/api/baseline")
def get_baseline() -> list[dict]:
    rows = db_manager.get_all_baselines()
    return [
        {
            "feature_name": r.feature_name,
            "min_val": r.min_val,
            "max_val": r.max_val,
            "unit": r.unit,
            "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M"),
        }
        for r in rows
    ]


@app.put("/api/baseline")
def put_baseline(items: list[BaselineBody]) -> dict:
    for item in items:
        db_manager.upsert_baseline(
            feature_name=item.feature_name,
            min_val=item.min_val,
            max_val=item.max_val,
            unit=item.unit,
        )
    return {"saved": len(items)}


@app.put("/api/rules")
def put_rules(rules: dict) -> dict:
    # TODO: rule_manager (ENG-004)
    return {"ok": True}


@app.get("/api/prompt")
def get_prompt() -> dict:
    prompt = db_manager.get_latest_prompt()
    if not prompt:
        return {"version": None, "text": ""}
    return {"version": prompt.version, "text": prompt.text}


@app.put("/api/prompt")
def put_prompt(body: PromptBody) -> dict:
    db_manager.save_prompt(version=body.version, text=body.text)
    return {"ok": True}


# ---------------------------------------------------------------------------
# 리포트 (RPT)
# ---------------------------------------------------------------------------
@app.post("/api/report")
def report(analysis: dict) -> dict:
    """분석 결과(dict) → 로컬 LLM 요약 생성 (LLM-001). RAG/PDF는 추후."""
    trip = analysis.get("trip") or {}
    baseline = analysis.get("baseline") or {}
    quality = analysis.get("quality") or {}
    out_of_range = baseline.get("out_of_range") or []

    # analyze 응답 키 → llm_report.generate_llm_summary 입력 스키마로 매핑
    llm_input = {
        "final_judgement": analysis.get("verdict", "UNKNOWN"),
        "trip_count": trip.get("count", 0),
        "abnormal_items": out_of_range,
        "baseline_deviation": [
            {"column": c, "description": "정상 baseline 이탈"} for c in out_of_range
        ],
        "data_quality": f"누락 {quality.get('missing', 0)}건, 이상치 {quality.get('outliers', 0)}건",
    }
    summary = llm_report.generate_llm_summary(llm_input)
    return {"summary": summary, "model": llm_report.get_local_model_name()}
