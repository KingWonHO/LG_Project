"""FastAPI 진입점 — React 프론트엔드용 REST API.

※ 현재 스켈레톤 단계: 엔드포인트 구조만 정의하고 응답은 placeholder.
   실제 로직은 src/* 모듈을 호출하도록 채워나간다 (기능 ID 주석 참고).

실행:
    uv run uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings
from src import db_manager

app = FastAPI(title="LG Comp 확인 에이전트 API", version="0.1.0")


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
    """파일 업로드 → 분석 (ANA-001~007). 현재 placeholder."""
    # 업로드 파일 디스크 저장
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    save_path = upload_dir / file.filename
    content = await file.read()
    save_path.write_bytes(content)

    # DB-001: 파일 정보 저장
    db_file = db_manager.save_file_info(
        filename=file.filename,
        file_path=str(save_path),
        row_count=None,  # TODO: file_parser 구현 후 실제 행 수로 교체
    )
    db_manager.update_file_status(db_file.id, "processing")

    try:
        # TODO: file_parser → column_mapper → trip/baseline/quality → verdict → result_builder
        result = {
            "verdict": "관리필요",
            "trip": {"count": 3, "ranges": [[150, 172]]},
            "baseline": {"out_of_range": ["CoolingPower"]},
            "quality": {"missing": 0, "outliers": 2},
        }

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
    # TODO: rag_engine → llm_report(Qwen) → report_generator (RPT-001/002)
    return {
        "summary": "Trip 3회 감지, CoolingPower 초과로 관리필요.",
        "causes": ["냉매 부족 가능성", "컴프 과부하"],
        "actions": ["냉매 충전량 점검", "컴프 전류 파형 재측정"],
    }
