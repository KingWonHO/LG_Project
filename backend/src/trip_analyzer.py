"""trip_analyzer 모듈: Trip Code 분석 (ANA-003).

Trip_Code가 0이 아닌 데이터를 탐지하고 발생 횟수와 구간을 계산한다.
column_mapper를 거쳐 표준 컬럼명(Trip_Code, Time)으로 정규화된 DataFrame을 입력으로 받는다.
"""

from __future__ import annotations

import pandas as pd


def detect_trip_mask(df: pd.DataFrame) -> pd.Series:
    """Trip_Code가 0이 아닌 행을 표시하는 불리언 마스크를 반환한다."""
    return df["Trip_Code"] != 0


def count_trip_occurrences(df: pd.DataFrame) -> int:
    """Trip_Code가 연속으로 0이 아닌 구간(발생 1회 단위)의 개수를 계산한다."""
    mask = detect_trip_mask(df)
    if not mask.any():
        return 0
    group_id = (mask != mask.shift()).cumsum()
    return group_id[mask].nunique()
