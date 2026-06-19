"""column_mapper 모듈: 컬럼 자동 매핑 (ANA-002).

업로드 파일마다 다른 컬럼명을 표준 컬럼명으로 매핑한다.
표준 컬럼명은 trip_analyzer/baseline_analyzer/result_builder 등 후속 모듈이 공통으로 사용한다.
"""

from __future__ import annotations

# 표준 컬럼명 -> 별칭(다양한 원본 표기) 매핑 테이블.
# 별칭은 정규화(소문자, 공백/언더스코어/하이픈 제거) 후 비교한다.
STANDARD_COLUMN_ALIASES: dict[str, list[str]] = {
    "Trip_Code": ["trip_code", "tripcode", "trip code", "트립코드", "트립 코드"],
    "컴프전류": ["컴프전류", "컴프 전류", "comp_current", "compcurrent"],
    "전압": ["전압", "voltage", "volt"],
    "Iqe": ["iqe"],
    "CoolingPower": ["coolingpower", "cooling_power", "cooling power"],
    "Initial_Delay": ["initial_delay", "initialdelay", "initial delay"],
    "RT": ["rt"],
}
