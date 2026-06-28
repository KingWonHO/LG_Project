"""trip_analyzer 모듈: Trip Code 분석 (ANA-003).

Trip_Code가 0이 아닌 데이터를 탐지하고 발생 횟수와 구간을 계산한다.
column_mapper를 거쳐 표준 컬럼명(Trip_Code, Time)으로 정규화된 DataFrame을 입력으로 받는다.
"""

from __future__ import annotations

import pandas as pd


def detect_trip_mask(df: pd.DataFrame) -> pd.Series:
    """Trip_Code가 0이 아닌 행을 표시하는 불리언 마스크를 반환한다.

    Trip_Code≠0인 연속 구간 단위로 판단한다 — 그 구간 안에 운전(실제주파수)과 REF(지령주파수)가
    모두 0이 아니었던 순간이 한 번이라도 있으면 구간 전체를 트립으로 인정하고, 한 번도 없으면
    (=구간 내내 아무 동작 지령도 없었던 완전 정지 상태) 노이즈성 단발 블립으로 보고 제외한다.
    행 단위로 운전≠0/REF≠0를 같이 요구하면 트립 도중 운전값이 잠깐 흔들릴 때 구간이 잘게
    쪼개져 발생 횟수가 부풀려지므로, 구간 단위로만 판정한다.
    """
    raw_mask = df["Trip_Code"] != 0
    if not raw_mask.any():
        return raw_mask
    group_id = (raw_mask != raw_mask.shift()).cumsum()
    was_active = (df["운전"] != 0) & (df["REF"] != 0)
    group_was_ever_active = was_active.groupby(group_id).transform("any")
    return raw_mask & group_was_ever_active


def count_trip_occurrences(df: pd.DataFrame) -> int:
    """Trip_Code가 연속으로 0이 아닌 구간(발생 1회 단위)의 개수를 계산한다."""
    mask = detect_trip_mask(df)
    if not mask.any():
        return 0
    group_id = (mask != mask.shift()).cumsum()
    return group_id[mask].nunique()


def find_trip_ranges(df: pd.DataFrame) -> list[list]:
    """Trip_Code가 연속으로 0이 아닌 구간별 [시작 Time, 종료 Time]을 계산한다."""
    mask = detect_trip_mask(df)
    if not mask.any():
        return []
    group_id = (mask != mask.shift()).cumsum()
    ranges = []
    for _, group in df[mask].groupby(group_id[mask]):
        ranges.append([group["Time"].iloc[0].item(), group["Time"].iloc[-1].item()])
    return ranges


def analyze_trip(df: pd.DataFrame) -> dict:
    """Trip 발생 횟수와 구간을 종합하여 표준 trip 결과를 생성한다 (verdict_engine/result_builder에서 사용)."""
    return {
        "count": count_trip_occurrences(df),
        "ranges": find_trip_ranges(df),
    }
