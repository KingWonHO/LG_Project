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


def _to_native(value):
    """numpy 스칼라(np.int64 등)를 JSON 직렬화 가능한 파이썬 기본 타입으로 변환한다."""
    return value.item() if hasattr(value, "item") else value


def _trip_boundary_indices(df: pd.DataFrame, trip: dict | None) -> set[int]:
    """trip.ranges의 시작/종료 Time에 해당하는 행 인덱스를 찾는다.

    균등 다운샘플링은 1행짜리 짧은 트립의 Time을 건너뛸 수 있어, 차트 라인이 트립 시점의
    실제 신호 변화를 놓칠 수 있다. 이를 방지하기 위해 해당 행을 강제로 series에 포함시킨다.
    """
    if not trip or not trip.get("ranges"):
        return set()
    required_times = {t for start, end in trip["ranges"] for t in (start, end)}
    time_to_index = {time: idx for idx, time in enumerate(df["Time"])}
    return {time_to_index[t] for t in required_times if t in time_to_index}


def build_series(
    df: pd.DataFrame,
    columns: list[str],
    max_points: int = 500,
    trip: dict | None = None,
) -> list[dict]:
    """차트(USR-005/006)용 시계열 데이터를 생성한다.

    표준 컬럼명 Time을 표준 결과 형식의 "time" 키로 변환하고, USR-003에서 사용자가
    선택한 columns(예: 컴프전류, 전압)만 함께 담는다. 컴프레서 모델/PCB에 따라 컬럼 구성이
    달라 요청한 columns 중 DataFrame에 없는 항목은 baseline_analyzer와 동일하게 조용히
    건너뛴다 (실제로 포함된 컬럼은 각 series 레코드의 키로 그대로 드러난다).
    trip을 넘기면 트립 시작/종료 Time 행은 다운샘플링으로 누락되지 않도록 강제로 포함한다.
    """
    columns = [column for column in columns if column in df.columns]
    indices = set(_downsample_indices(len(df), max_points)) | _trip_boundary_indices(df, trip)
    subset = df.iloc[sorted(indices)][["Time", *columns]]
    series = []
    for row in subset.itertuples(index=False):
        record = {"time": _to_native(row[0])}
        for column, value in zip(columns, row[1:]):
            record[column] = _to_native(value)
        series.append(record)
    return series


def build_result(
    df: pd.DataFrame,
    columns: list[str],
    verdict: dict,
    trip: dict,
    baseline: dict,
    quality: dict | None = None,
    max_points: int = 500,
) -> dict:
    """trip/baseline/quality/verdict 분석 결과와 시계열 데이터를 표준 결과 JSON으로 합친다.

    verdict/trip/baseline/quality는 각각 verdict_engine.analyze_verdict,
    trip_analyzer.analyze_trip, baseline_analyzer.analyze_baseline,
    data_quality_checker(ANA-005)가 만든 결과 dict를 그대로 전달받는다.
    data_quality_checker(ANA-005)가 아직 없는 상태에서도 파이프라인이 동작할 수 있도록
    quality는 선택값이며, 생략하면 품질 이슈가 없는 것으로 간주한다 (verdict_engine과 동일한 패턴).
    """
    if quality is None:
        quality = {"missing": 0, "outliers": 0}
    return {
        **verdict,
        "trip": trip,
        "baseline": baseline,
        "quality": quality,
        "series": build_series(df, columns, max_points, trip=trip),
    }
