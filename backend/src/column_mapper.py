"""column_mapper 모듈: 컬럼 자동 매핑 (ANA-002).

업로드 파일마다 다른 컬럼명을 표준 컬럼명으로 매핑한다.
DPS/NODPS Raw Data(21컬럼)는 JSON의 column_index 순서를 기준으로 매핑하고,
그 외 형식은 기존 컬럼명 기반 별칭 매핑을 사용한다.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

_JSON_DIR = Path(__file__).parent.parent / "data"

# DPS/NODPS Raw Data 컬럼 수 (0~20, 총 21개)
_RAW_COLUMN_COUNT = 21

# 컬럼명 기반 별칭 매핑 (DPS/NODPS 외 형식 폴백용)
STANDARD_COLUMN_ALIASES: dict[str, list[str]] = {
    "Trip_Code": ["trip_code", "tripcode", "trip code", "트립코드", "트립 코드"],
    "Time": ["time"],
    "컴프전류": ["컴프전류", "컴프 전류", "comp_current", "compcurrent"],
    "전압": ["전압", "voltage", "volt"],
    "RT": ["rt"],
    "Ide": ["ide", "ide(0.01)"],
    "Iqe": ["iqe"],
    "Idef": ["idef"],
    "Iqef": ["iqef"],
    "Ide_ref": ["ide_ref", "ide ref"],
    "Iqe_ref": ["iqe_ref", "iqeref", "iqe ref"],
    "REF": ["ref"],
    "운전": ["운전"],
    "Comp_On": ["comp_on", "comp on", "comp_on_time", "comp on time"],
    "Relay": ["relay"],
    "Relay_Flag": ["relay_flag", "relay flag"],
    "Forced_Drive": ["forced_drive", "forced drive", "forced_dri", "forced dri"],
    "NC_Min": ["nc_min", "nc min"],
    "NC_Flag": ["nc_flag", "nc flag"],
    "NC_Sec": ["nc_sec", "nc sec"],
    "LQC_Count": ["lqc_count", "lqc count", "lqc_coun", "lqc coun"],
    "추가각": ["추가각"],
    "진각합": ["진각합"],
    "Power": ["power"],
    "F_Power": ["f_power", "f power"],
    "R+F_Power": ["r+f_power", "r+f power"],
    "Pulse_Value": ["pulse_value", "pulse value", "pulse_valu", "pulse valu"],
    "Comp_Step": ["comp_step", "comp step", "comp_ste", "comp ste"],
    "Delay_Time": ["delay_time", "delay time", "delay_tim", "delay tim"],
    "Ramp": ["ramp"],
    "Ramping": ["ramping"],
    "Duty": ["duty"],
    "최적각": ["최적각"],
    "FW": ["fw"],
    "Initial_Delay": ["initial_delay", "initialdelay", "initial delay", "initial_del"],
    "CoolingPower": ["coolingpower", "cooling_power", "cooling power", "coolingpc"],
    "OnOffByte": ["onoffbyte", "onoff_byte", "onoff byte"],
    "Open_Loop": ["open_loop", "open loop", "open_loo", "open loo", "open_loop_step", "open loop step"],
    "PGM_Ver": ["pgm_ver", "pgm ver"],
    "DC_Link": ["dc_link", "dc link"],
    "First": ["first"],
    "second": ["second"],
}


def _normalize(name: str) -> str:
    return name.strip().lower().replace(" ", "").replace("_", "").replace("-", "")


_ALIAS_TO_STANDARD: dict[str, str] = {
    _normalize(alias): standard
    for standard, aliases in STANDARD_COLUMN_ALIASES.items()
    for alias in aliases
}


def map_column_name(raw_name: str) -> str:
    """원본 컬럼명을 표준 컬럼명으로 매핑한다. 매칭 없으면 원본 반환."""
    return _ALIAS_TO_STANDARD.get(_normalize(raw_name), raw_name)


# ---------------------------------------------------------------------------
# DPS / NODPS column_index 기반 매핑
# ---------------------------------------------------------------------------

def _load_index_mapping(data_type: str) -> dict[int, str]:
    """JSON에서 column_index → canonical_name 매핑 로드. unused 컬럼 제외."""
    path = _JSON_DIR / f"{data_type}_columns.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        col["column_index"]: col["canonical_name"]
        for col in data.get("columns", [])
        if col.get("category") != "unused"
    }


def _detect_data_type(df: pd.DataFrame) -> str | None:
    """21컬럼 Raw Data의 DPS/NODPS 타입 감지.

    컬럼 수가 21개가 아니면 None 반환 → 이름 기반 폴백 사용.
    DPS 전용 컬럼명(Trial_Count, 1st_Freq, 2nd_Freq) 존재 여부로 판별하고,
    판별 불가 시 NODPS 기본값.
    """
    if len(df.columns) != _RAW_COLUMN_COUNT:
        return None
    normalized = {_normalize(c) for c in df.columns}
    dps_markers = {"trialcount", "1stfreq", "2ndfreq"}
    if normalized & dps_markers:
        return "DPS"
    nodps_markers = {"waittime"}
    if normalized & nodps_markers:
        return "NODPS"
    return "NODPS"  # 21컬럼이지만 판별 불가 → NODPS 기본값


def map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame의 컬럼명을 표준 컬럼명으로 변환한다.

    - 21컬럼 Raw Data: JSON column_index 순서 기준 매핑 (DPS/NODPS)
    - 그 외: 컬럼명 별칭 기반 매핑 (폴백)
    """
    data_type = _detect_data_type(df)
    if data_type:
        index_map = _load_index_mapping(data_type)
        if index_map:
            rename = {
                col: index_map[idx]
                for idx, col in enumerate(df.columns)
                if idx in index_map
            }
            return df.rename(columns=rename)
    return df.rename(columns={col: map_column_name(col) for col in df.columns})
