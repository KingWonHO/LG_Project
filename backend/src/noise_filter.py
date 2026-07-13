"""noise_filter 모듈: 정상범위 초과 값(노이즈/수집오류) 제거 전처리 (ANA 보조).

엔지니어 스펙(연번=column_index 기준)의 정상범위를 벗어난 값은 실제 이상이 아니라
데이터 수집 시 잘못 들어온 튀는 값(노이즈)이므로 분석 전에 제거한다.
- 일반 컬럼: 노이즈 → NaN (median/max 등 통계에서 자동 제외 → 판정 왜곡 방지)
- Trip(20)  : 노이즈 → 0 (잘못 튄 값이 트립으로 오검출되지 않도록)
- Time(0)   : 제외 (시간축)

★ 단, Trip_Code가 1~20인 행(=실제 트립 발생 구간)은 노이즈 필터링에서 통째로 제외한다.
  실제 트립 순간에는 각 신호가 정상범위를 벗어나는 게 당연한 '실제 이상 이벤트'이므로,
  이를 노이즈로 제거하면 트립 자체가 사라져 PASS로 오판정된다.
프론트 columnSchema.ts 의 노이즈 규칙과 동일한 값을 사용한다.
"""

from __future__ import annotations

import pandas as pd

Bounds = tuple[float | None, float | None]

# 공통(모드 무관) 정상범위 [min, max]  (None = 제한 없음). 음수 이상치는 min=0.
_COMMON: dict[int, Bounds] = {
    1: (None, None),   # Imag (전체)
    2: (None, None),   # (전체)
    3: (100, 400),     # DC_link
    4: (0, 100),       # Ref_Hz
    5: (0, 100),       # Real_Hz
    6: (None, None),   # (전체)
    7: (0, 600),       # Power
    8: (0, 300),       # IPM
    10: (0, 100),      # Ramp_Hz
    11: (0, 3000),     # LeadA
    12: (0, 3000),     # LeadA_FW
    13: (0, 3000),     # LeadA_Add
    14: (0, 3000),     # LeadA_Total
    15: (0, 255),      # MtoC
    18: (0, 300),      # R_temp
    19: (0, 2000),     # Avg_Torque
    20: (0, 20),       # Trip
}
# 모드별로 다른 컬럼(9·16·17)
_NODPS: dict[int, Bounds] = {9: (0, 1000), 16: (0, 255), 17: (0, 255)}
_DPS: dict[int, Bounds] = {9: (0, 255), 16: (0, 100), 17: (0, 100)}

TIME_INDEX = 0
TRIP_INDEX = 20

# 실제 트립으로 인정하는 Trip_Code 범위 (이 구간의 행은 노이즈 필터링 제외)
TRIP_CODE_MIN = 1
TRIP_CODE_MAX = 20


def _bounds(pos: int, is_dps: bool) -> Bounds | None:
    if pos in (9, 16, 17):
        return (_DPS if is_dps else _NODPS).get(pos)
    return _COMMON.get(pos)


def clean_noise(df: pd.DataFrame, data_type: str | None = None) -> pd.DataFrame:
    """정상범위를 벗어난 값을 제거한 DataFrame을 반환한다 (컬럼 위치=인덱스 기준).

    data_type: "DPS"/"NODPS"/None (None이면 NODPS 기준으로 처리).
    Trip_Code(1~20)가 있는 행은 실제 트립 구간이므로 노이즈 필터링에서 제외한다.
    """
    is_dps = data_type == "DPS"

    # 실제 트립 구간 마스크: Trip_Code(위치 20)가 1~20인 행 → 노이즈 필터 제외
    trip_active = pd.Series(False, index=df.index)
    if df.shape[1] > TRIP_INDEX:
        tc = pd.to_numeric(df.iloc[:, TRIP_INDEX], errors="coerce")
        trip_active = tc.between(TRIP_CODE_MIN, TRIP_CODE_MAX)

    for pos in range(df.shape[1]):
        if pos == TIME_INDEX:
            continue
        b = _bounds(pos, is_dps)
        if b is None:
            continue
        lo, hi = b
        col = df.columns[pos]
        s = pd.to_numeric(df[col], errors="coerce")
        mask = pd.Series(False, index=df.index)
        if lo is not None:
            mask = mask | (s < lo)
        if hi is not None:
            mask = mask | (s > hi)
        # ★ 실제 트립 구간(Trip_Code 1~20)의 값은 노이즈가 아니므로 제거 대상에서 제외
        mask = mask & ~trip_active
        if not mask.any():
            continue
        if pos == TRIP_INDEX:
            df[col] = s.mask(mask, 0)     # Trip 노이즈 → 0 (오검출 방지, 단 트립행은 보존)
        else:
            df[col] = s.where(~mask)      # 노이즈 → NaN (단 트립행은 보존)
    return df
