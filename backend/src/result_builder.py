"""result_builder 모듈: 분석 결과 JSON 생성 (ANA-007).

trip_analyzer(ANA-003)/baseline_analyzer(ANA-004)/data_quality_checker(ANA-005)/
verdict_engine(ANA-006)의 결과 dict와 DataFrame을 받아, 화면 표시·차트·리포트용
표준 JSON 결과(backend_spec.md 10번 섹션)를 생성한다.

표준 결과 형식:
    {
      "verdict": "관리필요",
      "trip": {"count": 3, "ranges": [[150, 172]]},
      "baseline": {"out_of_range": ["CoolingPower"]},
      "quality": {"missing": 0, "outliers": 2},
      "series": [{"time": 0, "컴프전류": 50.1, "전압": 220.3}]
    }
"""

from __future__ import annotations

import pandas as pd


def _downsample_indices(n_rows: int, max_points: int) -> list[int]:
    """전체 행 수가 max_points를 넘으면 균등 간격으로 max_points개의 행 인덱스를 뽑는다.

    원본 데이터는 수만~십만 행 단위라 그대로 JSON으로 보내면 응답이 과도하게 커지므로
    차트(USR-005/006) 렌더링에 충분한 만큼만 균등 추출한다.
    """
    if n_rows <= max_points:
        return list(range(n_rows))
    step = n_rows / max_points
    return [int(i * step) for i in range(max_points)]
