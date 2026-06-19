"""FastAPI 진입점 — React 프론트엔드용 REST API.

※ 현재 스켈레톤 단계: 엔드포인트 구조만 정의하고 응답은 placeholder.
   실제 로직은 src/* 모듈을 호출하도록 채워나간다 (기능 ID 주석 참고).

실행:
    uv run uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings

app = FastAPI(title="LG Comp 확인 에이전트 API", version="0.1.0")

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
    # TODO: file_parser → column_mapper → trip/baseline/quality → verdict → result_builder
    _ = await file.read()
    return {
        "verdict": "관리필요",
        "trip": {"count": 3, "ranges": [[150, 172]]},
        "baseline": {"out_of_range": ["CoolingPower"]},
        "quality": {"missing": 0, "outliers": 2},
        "filename": file.filename,
    }


# ---------------------------------------------------------------------------
# 이력 (ADM-002)
# ---------------------------------------------------------------------------
@app.get("/api/history")
def history() -> list[dict]:
    # TODO: db_manager 조회
    return [
        {"일시": "2026-06-18 09:12", "파일명": "comp_A_0618.csv", "행수": 1820, "판정": "관리필요"},
    ]


# ---------------------------------------------------------------------------
# 엔지니어 관리 (ENG / DB)
# ---------------------------------------------------------------------------
class TripCode(BaseModel):
    code: int
    의미: str
    원인: str
    조치: str


@app.get("/api/trip-codes")
def get_trip_codes() -> list[TripCode]:
    # TODO: rule_manager / db_manager
    return [TripCode(code=101, 의미="과전류", 원인="컴프 과부하", 조치="전류 점검")]


@app.put("/api/trip-codes")
def put_trip_codes(items: list[TripCode]) -> dict:
    # TODO: rule_manager 저장 → db_manager 반영 (ENG-002, ENG-006)
    return {"saved": len(items)}


@app.get("/api/baseline")
def get_baseline() -> dict:
    # TODO: baseline_manager (ENG-003)
    return {"Iqe": [0, 10], "CoolingPower": [50, 120], "Initial_Delay": [0, 5]}


@app.put("/api/rules")
def put_rules(rules: dict) -> dict:
    # TODO: rule_manager (ENG-004)
    return {"ok": True}


@app.get("/api/prompt")
def get_prompt() -> dict:
    # TODO: prompt_manager (ENG-005)
    return {"version": "v1", "text": "다음 분석 결과를 바탕으로 요약/원인/조치를 작성하라:\n{analysis_json}"}


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
