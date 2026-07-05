"""FastAPI 진입점 — React 프론트엔드용 REST API.

엔드포인트(main.py)는 라우팅·검증만 담당하고, 실제 분석/판정/저장/LLM 로직은
src/* 모듈을 호출한다 (기능 ID 주석 참고). src 모듈 자체는 수정하지 않는다.

실행:
    uv run uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings
from src import db_manager
from src import llm_report
from src import rag_engine
from src import engineer_rules
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


def _load_comp_parameters(model: str | None) -> dict | None:
    """선택한 컴프 모델의 제어 파라미터를 Comp_Parameter.json에서 로드한다 (경로 A: LLM 결정적 주입).

    RAG(유사검색) 대신, 선택 모델의 정확한 파라미터를 그대로 LLM 프롬프트에 넣기 위한 결정적 조회.
    """
    if not model:
        return None
    import json
    path = Path(__file__).parent / "data" / "agentData" / "Comp_Parameter.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    entry = data.get("compressors", {}).get(model)
    return entry.get("parameters") if entry else None


# 룰베이스 이상치: 컴프 파라미터 임계값 → 비교할 데이터 컬럼(canonical). 초과 시 이상.
# shunt_over_current는 KB 지침상 Imag와 직접 비교 금지 → 제외.
_PARAM_THRESHOLD_COLUMNS = {
    "power_over": "Power",
    "torque_limit_by_model": "Avg_Torque",
}


def _detect_param_anomalies(df, comp_params: dict | None) -> list[dict]:
    """선택 모델 파라미터 임계값을 실제 컬럼 최댓값과 비교해 초과 항목을 반환한다 (ANA-005 룰베이스 이상치).

    컬럼이 없거나 파라미터가 없으면 조용히 건너뛴다. shunt_over_current는 제외(Imag 직접비교 금지).
    """
    if not comp_params:
        return []
    found: list[dict] = []
    for pkey, col in _PARAM_THRESHOLD_COLUMNS.items():
        limit = comp_params.get(pkey)
        if limit is None or col not in df.columns:
            continue
        try:
            peak = float(df[col].max())
        except (ValueError, TypeError):
            continue
        if peak > float(limit):
            found.append({"param": pkey, "column": col, "peak": round(peak, 2), "limit": limit})
    return found


def _load_mtoc_reference() -> str:
    """MtoC 8bit 제어 프로토콜 해석 기준(bit 의미 + 에이전트 지시문)을 LLM 프롬프트용 텍스트로 로드한다.

    경로 B(결정적 주입): MtoC는 유사검색(RAG)이 아니라 고정된 해석 규칙이므로,
    프로토콜 지식을 그대로 프롬프트에 넣어 LLM이 MtoC 값을 올바르게 해석하도록 한다.
    """
    import json
    path = Path(__file__).parent / "data" / "agentData" / "MtoC_Protocol.json"
    if not path.exists():
        return ""
    d = json.loads(path.read_text(encoding="utf-8"))
    lines = ["[MtoC 8bit 제어 프로토콜 해석 기준]"]
    for b in d.get("bit_definitions", []):
        vm = b.get("value_meaning", {})
        meaning = ", ".join(f"{k}={v}" for k, v in vm.items())
        lines.append(f"- bit{b.get('bit_index')} {b.get('display_name_ko', '')}({b.get('bit_name', '')}): {meaning}")
    instr = d.get("agent_global_instruction", [])
    if instr:
        lines.append("[MtoC 해석 지시]")
        lines += [f"- {s}" for s in instr]
    return "\n".join(lines)


def _decode_mtoc_states(df) -> list[dict] | None:
    """DataFrame에 MtoC 컬럼이 있으면 등장한 값들을 8bit로 디코드해 반환한다 (경로 B).

    없으면 None. 결정적 디코드(유사검색 아님) — 값 10진수 → 8bit → bit별 의미.
    """
    if "MtoC" not in df.columns:
        return None
    import json
    path = Path(__file__).parent / "data" / "agentData" / "MtoC_Protocol.json"
    if not path.exists():
        return None
    bit_defs = json.loads(path.read_text(encoding="utf-8")).get("bit_definitions", [])
    states: list[dict] = []
    seen: set[int] = set()
    for v in df["MtoC"].dropna().unique():
        try:
            iv = int(v)
        except (ValueError, TypeError):
            continue
        if iv in seen or len(states) >= 20:
            continue
        seen.add(iv)
        bits = {}
        for b in bit_defs:
            idx = b.get("bit_index")
            on = (iv >> idx) & 1
            bits[b.get("bit_name", f"bit{idx}")] = b.get("value_meaning", {}).get(str(on), str(on))
        states.append({"value": iv, "binary": format(iv & 0xFF, "08b"), "bits": bits})
    return states or None


def _load_mtoc_rules() -> str:
    """MtoC analysis_rules(엔지니어 해석 규칙)를 LLM 프롬프트용 텍스트로 로드한다 (경로 C).

    이 규칙들은 PASS/FAIL을 바꾸는 하드 규칙이 아니라 해석 지침(severity 대부분 INFO)이므로,
    verdict 엔진이 아니라 LLM 프롬프트에 주입해 리포트 설명에 반영한다.
    (판정 자체를 바꾸는 규칙엔진은 Engineer_Analysis_Rule이 작성된 뒤 별도 반영.)
    """
    import json
    path = Path(__file__).parent / "data" / "agentData" / "MtoC_Protocol.json"
    if not path.exists():
        return ""
    rules = json.loads(path.read_text(encoding="utf-8")).get("analysis_rules", [])
    if not rules:
        return ""
    lines = ["[MtoC 분석 규칙 (엔지니어 해석 지침 — 판정 변경용 아님)]"]
    for r in rules:
        cols = ", ".join(c.get("canonical_name", "") for c in r.get("required_columns", []))
        lines.append(
            f"- ({r.get('data_type')}/{r.get('severity')}) {r.get('rule_name_ko', '')}"
            f" [필요컬럼: {cols}]: {r.get('logic_ko', '')}"
            f" → 지침: {r.get('llm_instruction', '')}"
        )
    return "\n".join(lines)


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
    # RAG-001: Trip Code 지식 데이터 ChromaDB 인덱싱
    rag_engine.index_trip_codes_from_db()


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


@app.get("/api/compressors")
def compressors() -> dict:
    """컴프 모델 파라미터 라이브러리 서빙 (data/agentData/Comp_Parameter.json).

    프론트 모델 선택 드롭다운 + 파라미터 표시에 사용한다.
    반환: {models: [...], definitions: {...}, compressors: {모델: {parameters, metadata}}}
    """
    import json
    path = Path(__file__).parent / "data" / "agentData" / "Comp_Parameter.json"
    if not path.exists():
        return {"models": [], "definitions": {}, "compressors": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    comps = data.get("compressors", {})
    return {
        "models": list(comps.keys()),
        "definitions": data.get("parameter_definitions", {}),
        "compressors": comps,
    }


# ---------------------------------------------------------------------------
# 분석 (USR / ANA)
# ---------------------------------------------------------------------------
@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...), comp_model: str | None = Form(None)) -> dict:
    """파일 업로드 → 분석 (ANA-001~007).

    src 분석 파이프라인을 순서대로 호출한다:
      file_parser → column_mapper → trip_analyzer / baseline_analyzer → verdict_engine → result_builder
    (data_quality(ANA-005)는 모듈 미구현 상태이므로 생략 → verdict/result_builder가 quality 없이 동작)

    comp_model: 선택한 컴프 모델명(Comp_Parameter.json). 현재는 응답에 반영만 하며,
    파라미터 기반 판정 로직은 규칙 정의 후 별도 반영 예정.
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

        # ANA-005(룰베이스 이상치): 컴프 모델 파라미터 임계값 초과 탐지 → quality.outliers
        comp_params = _load_comp_parameters(comp_model)
        param_anomalies = _detect_param_anomalies(df, comp_params)
        quality = {"missing": 0, "outliers": len(param_anomalies)}

        # ANA-006: 종합 판정 (트립 + baseline 이탈 + 이상치 → PASS/관리필요/FAIL)
        # 트립이 없어도 이상치(outliers>0)나 baseline 이탈이 있으면 verdict_engine이 관리필요로 판정
        verdict = verdict_engine.analyze_verdict(trip, baseline, quality)

        # ANA-007: 표준 결과 JSON (차트용 series 포함)
        result = result_builder.build_result(df, DEFAULT_CHART_COLUMNS, verdict, trip, baseline, quality)

        # 경로 B: MtoC 컬럼이 있으면 8bit 상태 디코드 (없으면 None)
        mtoc_states = _decode_mtoc_states(df)

        # data_type 추론 (엔지니어 룰 필터용): DPS=Trial_Count / NODPS=Wait_Time 컬럼으로 판별
        if "Trial_Count" in df.columns:
            data_type = "DPS"
        elif "Wait_Time" in df.columns:
            data_type = "NODPS"
        else:
            data_type = None

        # DB-002: 분석 결과 저장
        db_result = db_manager.save_analysis_result(
            file_id=db_file.id,
            verdict=result["verdict"],
            anomalies={"baseline": result["baseline"], "quality": result["quality"], "param_anomalies": param_anomalies},
            trip_info=result["trip"],
        )
        db_manager.update_file_status(db_file.id, "done")

        return {**result, "filename": file.filename, "file_id": db_file.id, "result_id": db_result.id, "comp_model": comp_model, "mtoc": mtoc_states, "data_type": data_type, "param_anomalies": param_anomalies}

    except Exception:
        db_manager.update_file_status(db_file.id, "error")
        raise


# ---------------------------------------------------------------------------
# 이력 (ADM-002)
# ---------------------------------------------------------------------------
@app.get("/api/history")
def history() -> list[dict]:
    return db_manager.get_analysis_history()


@app.get("/api/history/{result_id}")
def history_detail(result_id: int) -> dict:
    """ADM-002 상세 — 과거 분석의 verdict/trip/baseline/quality + 차트용 series를 반환한다.

    series는 DB에 저장하지 않으므로, 업로드 당시 저장해둔 원본 파일(file_path)을 다시 읽어서
    file_parser → column_mapper → result_builder로 그 자리에서 재계산한다 (src 모듈 수정 없음).
    """
    result = db_manager.get_analysis_result_by_id(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
    db_file = db_manager.get_file_info(result.file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="원본 파일 정보를 찾을 수 없습니다.")

    file_path = Path(db_file.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="원본 파일이 더 이상 존재하지 않습니다.")

    df = column_mapper.map_columns(file_parser.parse_file(db_file.filename, file_path.read_bytes()))
    trip = result.trip_info or {"count": 0, "ranges": []}
    series = result_builder.build_series(df, DEFAULT_CHART_COLUMNS, trip=trip)

    anomalies = result.anomalies or {}
    return {
        "verdict": result.verdict,
        "trip": trip,
        "baseline": anomalies.get("baseline", {"out_of_range": []}),
        "quality": anomalies.get("quality", {"missing": 0, "outliers": 0}),
        "series": series,
        "filename": db_file.filename,
        "file_id": db_file.id,
        "result_id": result.id,
    }


@app.delete("/api/history/{result_id}")
def delete_history(result_id: int) -> dict:
    """ADM-002 — 분석 이력 삭제."""
    if not db_manager.delete_analysis_result(result_id):
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
    return {"deleted": result_id}


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


@app.get("/api/rules")
def get_rules() -> dict:
    """엔지니어 분석 규칙 현황 (Engineer_Analysis_Rule.xlsx, mtime 자동 최신).

    전체 로드 룰 + 실제 적용(enabled=Y, status=approved) 룰 수를 반환해 엔지니어가 확인한다.
    """
    all_rules = engineer_rules.load_rules()
    return {
        "total": len(all_rules),
        "approved_count": len(engineer_rules.get_applicable_rules()),
        "rules": all_rules,
    }


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
    """분석 결과(dict) → RAG 검색 + 로컬 LLM 요약 생성 (RAG-002, LLM-001)."""
    trip = analysis.get("trip") or {}
    baseline = analysis.get("baseline") or {}
    quality = analysis.get("quality") or {}
    out_of_range = baseline.get("out_of_range") or []

    # RAG-002: 분석 결과와 유사한 Trip Code 검색 → LLM 컨텍스트
    rag_context = rag_engine.build_rag_context(analysis)

    # 경로 A: 선택 컴프 모델의 제어 파라미터를 결정적으로 로드해 LLM에 주입
    comp_model = analysis.get("comp_model")
    comp_parameters = _load_comp_parameters(comp_model)

    # 경로 B: MtoC 프로토콜 해석 기준을 결정적으로 주입 (LLM이 MtoC를 올바르게 해석하도록)
    mtoc_protocol = _load_mtoc_reference()

    # 경로 C: MtoC 분석 규칙(해석 지침)을 LLM에 주입 (판정 변경 아님)
    mtoc_rules = _load_mtoc_rules()

    # 엔지니어 분석 규칙(Engineer_Analysis_Rule.xlsx, mtime 자동 최신) — 승인 룰만 필터해 주입
    _rule_scope = "TRIP" if trip.get("count", 0) > 0 else "NORMAL"
    engineer_rules_ctx = engineer_rules.build_rules_context(
        data_type=analysis.get("data_type"), rule_scope=_rule_scope
    )

    # analyze 응답 키 → llm_report.generate_llm_summary 입력 스키마로 매핑
    # (build_summary_prompt가 입력 dict 전체를 프롬프트에 넣으므로 아래 키가 그대로 LLM에 반영됨)
    llm_input = {
        "final_judgement": analysis.get("verdict", "UNKNOWN"),
        "trip_count": trip.get("count", 0),
        "abnormal_items": out_of_range,
        "baseline_deviation": [
            {"column": c, "description": "정상 baseline 이탈"} for c in out_of_range
        ],
        "data_quality": f"누락 {quality.get('missing', 0)}건, 이상치 {quality.get('outliers', 0)}건",
        "comp_model": comp_model,
        "comp_parameters": comp_parameters,
        "mtoc_protocol": mtoc_protocol,
        "mtoc_rules": mtoc_rules,
        "engineer_rules": engineer_rules_ctx,
        "mtoc_states": analysis.get("mtoc"),
        "rag_context": rag_context,
    }
    summary = llm_report.generate_llm_summary(llm_input)
    return {
        "summary": summary,
        "model": llm_report.get_local_model_name(),
        "rag_context": rag_context,
        "comp_model": comp_model,
        "comp_parameters": comp_parameters,
    }


@app.post("/api/rag/index")
def rag_index() -> dict:
    """DB의 Trip Code를 ChromaDB에 재인덱싱 (RAG-001 수동 트리거)."""
    count = rag_engine.index_trip_codes_from_db()
    return {"indexed": count}


@app.post("/api/rag/engineer")
async def add_engineer_rule(
    rule_name: str = Form(...),
    interpretation: str = Form(...),
    file: UploadFile = File(...),
    comp_model: str | None = Form(None),
) -> dict:
    """엔지니어 RAG 룰 추가: 룰(해석) + 대표 CSV → CSV 분석 시그니처 임베딩으로 engineer_rag 저장.

    이후 유사한 분석이 들어오면(build_rag_context 이중검색) 이 엔지니어 룰이 기존 Trip Code보다 우선 사용된다.
    """
    content = await file.read()
    try:
        df = column_mapper.map_columns(file_parser.parse_file(file.filename, content))
    except file_parser.FileParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    trip = trip_analyzer.analyze_trip(df) if "Trip_Code" in df.columns else {"count": 0, "ranges": []}
    baseline = baseline_analyzer.analyze_baseline(df, _load_baseline_ranges())
    quality = {"missing": 0, "outliers": len(_detect_param_anomalies(df, _load_comp_parameters(comp_model)))}
    verdict = verdict_engine.analyze_verdict(trip, baseline, quality)

    signature = rag_engine._build_signature({"verdict": verdict["verdict"], "trip": trip, "baseline": baseline})
    rid = rag_engine.index_engineer_rule(
        rule_name=rule_name,
        interpretation=interpretation,
        signature_text=signature,
        extra_meta={"filename": file.filename, "verdict": verdict["verdict"], "comp_model": comp_model or ""},
    )
    return {
        "ok": True,
        "id": rid,
        "rule_name": rule_name,
        "signature": signature,
        "verdict": verdict["verdict"],
        "count": rag_engine.engineer_rules_count(),
    }


@app.get("/api/rag/engineer")
def engineer_rules_status() -> dict:
    """등록된 엔지니어 RAG 룰 수."""
    return {"count": rag_engine.engineer_rules_count()}
