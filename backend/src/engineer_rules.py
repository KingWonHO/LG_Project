"""engineer_rules 모듈: Engineer_Analysis_Rule.xlsx 로더 (ENG-004 보조).

엔지니어가 정해진 규격(RULE_EDITOR 시트)으로 xlsx를 계속 업데이트하면,
파일 수정시각(mtime) 캐시로 **변경 시 자동 재파싱**하여 항상 최신 룰을 참고한다.

룰 내용은 자유서술 텍스트(analysis_freeform_ko 등)라 판정엔진이 아니라
LLM 프롬프트/RAG 지식으로 사용한다. 적용 대상은 enabled=Y + status=approved 만.
"""

from __future__ import annotations

from pathlib import Path
from threading import Lock

_RULES_PATH = Path(__file__).parent.parent / "data" / "agentData" / "Engineer_Analysis_Rule.xlsx"

# 헤더 행 판별용(이 세 필드가 한 행에 모두 있으면 룰 테이블 헤더)
_HEADER_MARKERS = ("rule_name_ko", "data_type", "rule_scope")

# 표준 필드 -> RULE_EDITOR 헤더 별칭(오타/괄호 대응, 부분일치)
_FIELD_ALIASES: dict[str, list[str]] = {
    "rule_key": ["internal_rule_key"],
    "rule_name_ko": ["rule_name_ko"],
    "data_type": ["data_type"],
    "rule_scope": ["rule_scope"],
    "needed_column_indexes": ["needed_column_indexes", "needed_coulmn_indexes"],
    "optional_column_indexes": ["optional_column_indexes", "optional_coulmn_indexes"],
    "analysis_freeform_ko": ["analysis_freeform_ko"],
    "judgement_hint_ko": ["judgement_hint_ko"],
    "normal_pattern_ko": ["normal_pattern_ko"],
    "abnormal_pattern_ko": ["abnormal_pattern_ko"],
    "csv_based_comment_ko": ["csv_based_comment_ko"],
    "non_csv_reference_ko": ["non_csv_reference_ko"],
    "rag_keywords": ["rag_keywords"],
    "status": ["status"],
    "enabled": ["enabled"],
    "engineer_note": ["engineer_note"],
}

_cache: list[dict] = []
_cache_mtime: float = -1.0
_lock = Lock()


def _parse_rules() -> list[dict]:
    """RULE_EDITOR 시트에서 룰 테이블 헤더를 찾아 룰 행들을 dict 리스트로 파싱한다."""
    import openpyxl

    wb = openpyxl.load_workbook(_RULES_PATH, read_only=True, data_only=True)
    if "RULE_EDITOR" not in wb.sheetnames:
        return []
    rows = list(wb["RULE_EDITOR"].iter_rows(values_only=True))

    # 1) 헤더 행 찾기: _HEADER_MARKERS 를 모두 포함한 행
    header_row_idx = -1
    header_cells: dict[int, str] = {}
    for i, r in enumerate(rows):
        texts = {j: str(c).strip() for j, c in enumerate(r) if c is not None}
        if all(any(m == t for t in texts.values()) for m in _HEADER_MARKERS):
            header_row_idx = i
            header_cells = texts
            break
    if header_row_idx < 0:
        return []

    # 2) 표준 필드 -> 컬럼 인덱스 매핑 (부분일치 허용)
    field_col: dict[str, int] = {}
    for field, aliases in _FIELD_ALIASES.items():
        for col, text in header_cells.items():
            low = text.lower()
            if any(a in low for a in aliases):
                field_col[field] = col
                break

    name_col = field_col.get("rule_name_ko")
    if name_col is None:
        return []

    # 3) 헤더 다음 행부터 룰 파싱 (rule_name_ko 비면 빈 행으로 보고 skip)
    rules: list[dict] = []
    for r in rows[header_row_idx + 1:]:
        name = r[name_col] if name_col < len(r) else None
        if name is None or str(name).strip() == "":
            continue
        rule: dict = {}
        for field, col in field_col.items():
            val = r[col] if col < len(r) else None
            rule[field] = str(val).strip() if val is not None else None
        rules.append(rule)
    return rules


def load_rules(force: bool = False) -> list[dict]:
    """mtime 캐시. 파일이 바뀌면 자동 재파싱, 실패(편집 중 잠금 등) 시 직전 캐시 유지."""
    global _cache, _cache_mtime
    with _lock:
        try:
            mtime = _RULES_PATH.stat().st_mtime
        except OSError:
            return _cache
        if force or mtime != _cache_mtime:
            try:
                _cache = _parse_rules()
                _cache_mtime = mtime
            except Exception:
                # 파싱 실패 시 직전 정상 룰 유지 (서비스 중단 방지)
                pass
        return _cache


def get_applicable_rules(data_type: str | None = None, rule_scope: str | None = None) -> list[dict]:
    """enabled=Y + status=approved 중 data_type/rule_scope 조건에 맞는 룰만 반환.

    data_type: "DPS"/"NODPS" (COMMON 룰은 항상 포함). None이면 data_type 필터 없음.
    rule_scope: "TRIP"/"NORMAL" (BOTH 룰은 항상 포함). None이면 scope 필터 없음.
    """
    out: list[dict] = []
    for r in load_rules():
        if str(r.get("enabled") or "").strip().upper() != "Y":
            continue
        if str(r.get("status") or "").strip().lower() != "approved":
            continue
        rdt = str(r.get("data_type") or "").strip().upper()
        if data_type and rdt not in ("", "COMMON", data_type.upper()):
            continue
        rsc = str(r.get("rule_scope") or "").strip().upper()
        if rule_scope and rsc not in ("", "BOTH", rule_scope.upper()):
            continue
        out.append(r)
    return out


def build_rules_context(data_type: str | None = None, rule_scope: str | None = None) -> str:
    """적용 룰을 LLM 프롬프트용 텍스트로 구성한다 (승인된 룰만)."""
    rules = get_applicable_rules(data_type, rule_scope)
    if not rules:
        return ""
    lines = ["[엔지니어 분석 규칙 (승인/사용중)]"]
    for r in rules:
        head = f"■ {r.get('rule_name_ko', '')} ({r.get('data_type', '')}/{r.get('rule_scope', '')})"
        detail = []
        if r.get("analysis_freeform_ko"):
            detail.append(f"해석: {r['analysis_freeform_ko']}")
        if r.get("judgement_hint_ko"):
            detail.append(f"판정참고: {r['judgement_hint_ko']}")
        if r.get("normal_pattern_ko"):
            detail.append(f"정상패턴: {r['normal_pattern_ko']}")
        if r.get("abnormal_pattern_ko"):
            detail.append(f"이상패턴: {r['abnormal_pattern_ko']}")
        lines.append(head + " — " + " / ".join(detail))
    return "\n".join(lines)
