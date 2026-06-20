"""baseline_analyzer 모듈: 정상 기준(baseline) 비교 (ANA-004).

정상 baseline과 업로드 데이터를 비교하여 관리 필요 여부를 판단한다.
baseline 등록/수정 자체는 baseline_manager(ENG-003)가 담당하며, 이 모듈은
주어진 baseline 기준값(dict)과 DataFrame을 비교하는 순수 분석 로직만 담당한다.

baseline 형식 예시:
    {"CoolingPower": {"min": 17, "max": 23}, "Initial_Delay": {"min": 25, "max": 35}}
"""

from __future__ import annotations

import pandas as pd


def summarize_feature(df: pd.DataFrame, column: str) -> float:
    """컬럼의 대표값을 계산한다 (median).

    Iqe/CoolingPower/Initial_Delay 등은 정지·과도 구간의 이상치(0, 급변값)가 섞여 있어
    평균보다 median이 정상 운전 시점의 대표값을 더 안정적으로 반영한다.
    """
    return float(df[column].median())


def is_within_baseline(value: float, baseline_range: dict) -> bool:
    """값이 baseline 허용 범위(min/max) 내에 있는지 확인한다."""
    return baseline_range["min"] <= value <= baseline_range["max"]
