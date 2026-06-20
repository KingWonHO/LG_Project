"""verdict_engine 모듈: 최종 판정 생성 (ANA-006).

Trip(ANA-003), baseline(ANA-004), 데이터 품질(ANA-005) 분석 결과를 종합하여
PASS/관리필요/FAIL을 결정한다. 각 분석 모듈의 결과 dict만 입력으로 받는
순수 함수로 작성하여 trip_analyzer/baseline_analyzer/data_quality_checker의
구체 구현에 의존하지 않는다.

입력 형식 (각 분석 모듈의 표준 결과):
    trip: {"count": int, "ranges": [[start, end], ...]}       (trip_analyzer.analyze_trip)
    baseline: {"out_of_range": [str, ...]}                    (baseline_analyzer.analyze_baseline)
    quality: {"missing": int, "outliers": int}                (data_quality_checker, ANA-005)
"""

from __future__ import annotations

PASS = "PASS"
NEEDS_ATTENTION = "관리필요"
FAIL = "FAIL"

# Trip이 이 횟수 이상 반복되면 단순 관리 필요가 아닌 FAIL로 판단한다.
# 실제 운영 기준값은 rule_manager(ENG-004)의 Rule JSON에서 정해지므로 기본값일 뿐이며,
# decide_trip_verdict/analyze_verdict 호출 시 fail_threshold로 덮어쓸 수 있다.
TRIP_FAIL_COUNT_THRESHOLD = 5


def decide_trip_verdict(trip: dict, fail_threshold: int = TRIP_FAIL_COUNT_THRESHOLD) -> str:
    """Trip 발생 횟수를 기준으로 부분 판정을 내린다.

    ANA-003 결과(count)만 사용한다. 발생 횟수가 fail_threshold 이상이면 반복적인
    보호동작으로 보고 FAIL, 1회 이상이면 관리필요, 0회면 PASS로 본다.
    """
    count = trip["count"]
    if count >= fail_threshold:
        return FAIL
    if count > 0:
        return NEEDS_ATTENTION
    return PASS


def decide_baseline_verdict(baseline: dict) -> str:
    """baseline 이탈 항목 여부로 부분 판정을 내린다.

    ANA-004 설명("정상 baseline 대비 이탈 → 관리 필요 여부 판단")에 따라
    baseline 이탈은 FAIL이 아니라 관리필요까지만 영향을 준다.
    """
    return NEEDS_ATTENTION if baseline["out_of_range"] else PASS


def decide_quality_verdict(quality: dict) -> str:
    """데이터 품질 결과(누락값/이상치 개수)로 부분 판정을 내린다.

    데이터품질이상은 USR-004에 따라 verdict_engine 밖(ANA-005/result_builder)에서
    별도로 표시되는 상태이므로, 이 함수는 PASS/관리필요 두 단계만 다룬다.
    """
    return NEEDS_ATTENTION if quality["missing"] > 0 or quality["outliers"] > 0 else PASS


_SEVERITY_ORDER = {PASS: 0, NEEDS_ATTENTION: 1, FAIL: 2}


def combine_verdicts(verdicts: list[str]) -> str:
    """여러 부분 판정 중 가장 심각한 단계(PASS < 관리필요 < FAIL)를 최종 판정으로 선택한다."""
    return max(verdicts, key=lambda v: _SEVERITY_ORDER[v])


def analyze_verdict(trip: dict, baseline: dict, quality: dict) -> dict:
    """Trip/baseline/품질 결과를 종합하여 최종 판정 결과를 생성한다 (result_builder에서 사용)."""
    verdict = combine_verdicts(
        [
            decide_trip_verdict(trip),
            decide_baseline_verdict(baseline),
            decide_quality_verdict(quality),
        ]
    )
    return {"verdict": verdict}
