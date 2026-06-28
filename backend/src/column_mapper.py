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
    "Time": ["time"],
    "컴프전류": ["컴프전류", "컴프 전류", "comp_current", "compcurrent"],
    # 전압: 헤더 텍스트가 아니라 실측값 패턴(정지 시 310V 고정)으로 식별함.
    # 정상데이터/관리필요데이터 계열은 헤더 그대로 "Ide"가, PCB변경 계열은 "Idef"가 이 패턴을 보임.
    # 반면 헤더에 글자 그대로 적힌 "DC_Link"는 값 범위가 0~6이라 전압이 아닌 것으로 판단해 별도 유지.
    "전압": ["전압", "voltage", "volt", "ide", "idef"],
    "RT": ["rt"],
    # Ide(0.01)은 PCB변경 계열의 진짜 d축 전류(정지 시 0, 운전 시 증가) — "Ide"(전압)와 다른 신호.
    "Ide": ["ide(0.01)"],
    "Iqe": ["iqe"],
    "Iqef": ["iqef"],
    "Ide_ref": ["ide_ref", "ide ref"],
    "Iqe_ref": ["iqe_ref", "iqeref", "iqe ref"],
    "REF": ["ref"],
    # Trip/Relay/NC 제어 계열
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
    # 출력/온도/펄스/제어 계열
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
