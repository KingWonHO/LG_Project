"""column_mapper 모듈: 컬럼 자동 매핑 (ANA-002).

업로드 파일마다 다른 컬럼명을 표준 컬럼명으로 매핑한다.
표준 컬럼명은 trip_analyzer/baseline_analyzer/result_builder 등 후속 모듈이 공통으로 사용한다.
"""

from __future__ import annotations

import pandas as pd

# 표준 컬럼명 -> 별칭(다양한 원본 표기) 매핑 테이블.
# 별칭은 정규화(소문자, 공백/언더스코어/하이픈 제거) 후 비교한다.
STANDARD_COLUMN_ALIASES: dict[str, list[str]] = {
    "Trip_Code": ["trip_code", "tripcode", "trip code", "트립코드", "트립 코드"],
    "컴프전류": ["컴프전류", "컴프 전류", "comp_current", "compcurrent"],
    "전압": ["전압", "voltage", "volt"],
    "RT": ["rt"],
    # 전류/기준값 계열 (Ide/Iqe 계열) — 정상데이터/관리필요데이터/PCB변경 트립 샘플 기준
    "Ide": ["ide", "ide(0.01)"],
    "Iqe": ["iqe"],
    "Idef": ["idef"],
    "Iqef": ["iqef"],
    "Ide_ref": ["ide_ref", "ide ref"],
    "Iqe_ref": ["iqe_ref", "iqeref", "iqe ref"],
    "REF": ["ref"],
}


def _normalize(name: str) -> str:
    """컬럼명 비교를 위해 정규화한다 (소문자, 공백/언더스코어/하이픈 제거)."""
    return name.strip().lower().replace(" ", "").replace("_", "").replace("-", "")


_ALIAS_TO_STANDARD: dict[str, str] = {
    _normalize(alias): standard
    for standard, aliases in STANDARD_COLUMN_ALIASES.items()
    for alias in aliases
}


def map_column_name(raw_name: str) -> str:
    """원본 컬럼명을 표준 컬럼명으로 매핑한다. 매칭되는 표준 컬럼이 없으면 원본을 그대로 반환한다."""
    return _ALIAS_TO_STANDARD.get(_normalize(raw_name), raw_name)


def map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame의 모든 컬럼명을 표준 컬럼명으로 변환한다 (file_parser 결과에 이어서 호출)."""
    return df.rename(columns={col: map_column_name(col) for col in df.columns})
