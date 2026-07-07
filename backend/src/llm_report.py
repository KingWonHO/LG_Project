"""
LLM-001: 분석 요약 생성 모듈

분석 JSON과 RAG 검색 결과를 바탕으로
Compressor 제어검증 결과 요약문을 생성한다.
출력 형식: 결과 / 판정 / 분석 / 조치 4개 섹션 (## 마크다운 헤더).

담당: 김진용
"""

import os
import re
from typing import Any

import ollama


DEFAULT_LOCAL_MODEL = "gemma3:4b"

AVAILABLE_LOCAL_MODELS = {
    "gemma3:4b": {"priority": 1, "description": "기본 추천 모델. 한국어 요약 품질이 가장 좋음."},
    "qwen2.5:3b": {"priority": 2, "description": "대체 모델. 한국어 준수, 비교적 가벼움."},
    "llama3.2": {"priority": 3, "description": "경량 대체 모델. 빠르지만 중복 가능성."},
}


def get_local_model_name(model_name: str | None = None) -> str:
    """사용할 로컬 LLM 모델명을 결정한다 (인자 > 환경변수 > 기본값)."""
    return model_name or os.getenv("LOCAL_LLM_MODEL", DEFAULT_LOCAL_MODEL)


def build_summary_prompt(
    analysis_json: dict[str, Any],
    rag_results: list[str] | None = None,
) -> str:
    """분석 JSON + RAG 근거 → 결과/판정/분석/조치 4섹션 요약 프롬프트."""
    rag_results = rag_results or []

    prompt = """
너는 Compressor Raw Data 분석 결과를 엔지니어가 이해하기 쉽게 정리하는 AI 분석 Agent이다.

아래 분석 결과 JSON과 RAG 검색 근거를 바탕으로,
사용자가 빠르게 이해할 수 있도록 최종 분석 문장을 작성한다.

[분석 결과 JSON]
__ANALYSIS_JSON__

[RAG 검색 근거]
__RAG_RESULTS__

너는 반드시 아래 4개 섹션만, 아래 순서로 작성한다. 섹션 이름을 바꾸거나 추가하지 마라.

## 결과
- PASS / 관리필요 / FAIL 중 하나만 사용한다.
- 형식: AI 분석결과 "{PASS/FAIL/관리필요}" 입니다.
- 판정 기준:
  PASS: Trip 발생이 없고 주요 이상 운전 구간이 없으며 정상으로 판단되는 경우
  FAIL: Trip 발생, 명확한 보호동작, 또는 심각한 비정상 운전 구간이 확인된 경우
  관리필요: Trip은 없지만 비정상 경향/제어성능 저하/기동 약화/추가 검토가 필요한 경우

## 판정
- 전체 이벤트 요약만 작성한다. (Trip 발생 여부, 발생 횟수, Trip 종류별 횟수, 비정상 운전구간 수)
- 원인/해석/점검/조치 표현은 절대 쓰지 않는다.
- 예) AI 분석결과 트립 발생 3건이 확인되었습니다. 6번 과전류 Trip 2회, 7번 FO/IPM 보호 Trip 1회가 발생하였으며, 비정상 운전구간 1구간이 확인되었습니다.
- Trip이 없으면: AI 분석결과 Trip 발생은 0회입니다. (필요 시 비정상 의심구간 언급)

## 분석
- 시간 순서대로 번호를 붙여 작성한다. 각 항목에 발생 시점/현상/간략 해석을 포함한다.
- ★발생 시점/구간과 Trip 코드는 반드시 [분석 결과 JSON]의 trip_events(각 항목 start~end초, codes) 또는 trip_ranges의 실제 값만 사용한다. 목록에 없는 시간·구간·코드를 절대 만들지 마라. trip_events가 비어 있으면(트립 0회) 시점을 언급하지 말고 정상 관점으로 서술한다.
- 점검/확인/조치/개선 같은 조치 방법은 여기 쓰지 않는다. CSV로 확인 불가한 내부 신호는 단정하지 않는다.
- 형식:
  1. {시간}초 구간에서 {현상}이 확인되었습니다. {간략 해석}
  2. {시간}초 구간에서 {현상}이 확인되었습니다. {간략 해석}

## 조치
- 분석 항목과 동일한 번호로, 각 구간별 점검/조치 방향을 짧게 작성한다.
- 원인은 단정하지 말고 "가능성", "의심", "확인 필요"로 표현한다. 필요 시 "Comp SW 담당자 확인 필요"를 포함한다.
- 형식:
  1. {시간}초 구간의 {현상}에 대해서는 {점검 항목} 확인이 필요합니다.
  2. {시간}초 구간의 {현상}에 대해서는 {조치 방향} 검토가 필요합니다.

작성 규칙:
1. 반드시 "## 결과", "## 판정", "## 분석", "## 조치" 네 섹션만 출력한다.
2. "판정"에는 Trip 발생 여부/횟수/종류/비정상 구간 수만 쓴다. 원인·조치 금지.
3. "분석"에는 RAG 기반 원인/의미만 쓴다. 점검·확인·조치·개선 표현 금지.
4. "조치"에는 RAG 기반 조치 방법·우선 점검 항목만 쓴다.
5. RAG 문장에 원인과 조치가 함께 있어도 원인은 "분석"에, 조치는 "조치"에 분리한다.
6. RAG에 없는 원인/조치를 임의로 만들지 않는다. 분석 JSON에 없는 Trip 횟수를 지어내지 않는다.
7. Trip 발생 횟수가 0이면 "Trip 발생은 0회입니다"라고 명확히 쓴다.
8. Imag는 실제 전류값이 아니므로 정량 판단에 쓰지 않고 "높음/낮음/급증/불안정" 정성 신호로만 언급한다.
9. Current Trip Level(4.2A/4.3A)을 Imag와 직접 비교하지 않는다.
10. IPM 온도는 PCB별 정확도 차이가 있어 절대값 단정 대신 경향성으로 설명한다.
11. 엔지니어가 바로 읽도록 짧고 명확하게. 장황한 배경 설명은 생략한다.
12. 시점/구간/Trip 코드는 분석 JSON의 trip_events·trip_ranges에 있는 실제 Time 값만 사용하고 지어내지 않는다. trip_events가 비어 있으면 분석·조치에서 시점을 언급하지 않는다.

이제 위 형식대로만 답변한다.
"""
    return (
        prompt.replace("__ANALYSIS_JSON__", str(analysis_json))
        .replace("__RAG_RESULTS__", str(rag_results))
        .strip()
    )


# ---------------------------------------------------------------------------
# 섹션 파싱/정규화 (## 결과 / ## 판정 / ## 분석(=해석) / ## 조치)
# ---------------------------------------------------------------------------
_SECTION_ALIAS = {"결과": "결과", "판정": "판정", "분석": "분석", "해석": "분석", "조치": "조치"}


def _match_header(line: str) -> tuple[str, str] | None:
    """줄이 섹션 헤더면 (표준키, 나머지텍스트) 반환. '## 결과', '**결과**', '결과:', '3. 해석:' 등 허용.
    본문의 번호 항목('1. 1230초 …')은 헤더로 오인하지 않는다(키워드로 시작할 때만 인정)."""
    s = line.strip()
    m = re.match(r"^(?:#{1,6}\s*|\*{2}\s*)?(?:\d+\s*[.)]\s*)?(결과|판정|분석|해석|조치)\**\s*[:：]?\s*(.*)$", s)
    if not m:
        return None
    key, rest = m.group(1), m.group(2)
    is_md = s.startswith("#") or s.startswith("**")
    has_colon = bool(re.match(rf"^(?:\d+\s*[.)]\s*)?{key}\s*[:：]", s))
    only_key = re.sub(r"^(?:\d+\s*[.)]\s*)?", "", s).strip().rstrip("*") == key
    if is_md or has_colon or only_key:
        return _SECTION_ALIAS[key], rest.strip()
    return None


def _parse_sections(text: str) -> dict[str, str]:
    """LLM 출력에서 결과/판정/분석/조치 섹션 본문을 추출한다 (멀티라인 보존)."""
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        h = _match_header(line)
        if h:
            if current:
                sections[current] = "\n".join(buf).strip()
            current, first = h
            buf = [first] if first else []
        elif current is not None:
            buf.append(line)
    if current:
        sections[current] = "\n".join(buf).strip()
    return sections


def normalize_summary_format(
    summary: str,
    analysis_json: dict[str, Any],
    rag_results: list[str] | None = None,
) -> str:
    """LLM 출력을 결과/판정/분석/조치 4섹션(## 헤더)으로 정규화한다.
    필수 섹션이 빠지면 rule-based 요약으로 대체한다."""
    rag_results = rag_results or []
    sec = _parse_sections(summary)

    result = sec.get("결과")
    judgement = sec.get("판정")
    analysis = sec.get("분석")
    action = sec.get("조치") or build_action_line(analysis_json, rag_results)

    if result and judgement and analysis and action:
        return (
            f"## 결과\n{result}\n\n"
            f"## 판정\n{judgement}\n\n"
            f"## 분석\n{analysis}\n\n"
            f"## 조치\n{action}"
        )
    return generate_rule_based_summary(analysis_json, rag_results)


def build_action_line(analysis_json: dict[str, Any], rag_results: list[str] | None = None) -> str:
    """조치 섹션이 누락됐을 때 analysis_json/RAG 근거로 조치 본문을 생성한다."""
    rag_results = rag_results or []
    recommended = analysis_json.get("recommended_actions") or []
    if recommended:
        return "\n".join(f"{i}. {a}" for i, a in enumerate(recommended, 1))
    if rag_results:
        rag_text = " ".join(map(str, rag_results[:2]))
        return f"1. RAG 근거({rag_text}) 기준으로 우선 점검이 필요하며, Comp SW 담당자 확인이 필요합니다."
    return "1. RAG 기반 조치 근거가 없어 담당 엔지니어의 추가 확인이 필요합니다."


def generate_rule_based_summary(
    analysis_json: dict[str, Any],
    rag_results: list[str] | None = None,
) -> str:
    """로컬 LLM 실패/형식오류 시 사용할 rule-based 요약 (## 4섹션 형식)."""
    rag_results = rag_results or []

    final_judgement = analysis_json.get("final_judgement", "UNKNOWN")
    trip_count = analysis_json.get("trip_count", 0)
    abnormal_items = analysis_json.get("abnormal_items", [])
    trip_items = analysis_json.get("trip_items", [])
    root_causes = analysis_json.get("root_cause_candidates", [])

    issue_items = trip_items or abnormal_items
    issue_text = ", ".join(map(str, issue_items)) if issue_items else "주요 이상 항목 없음"

    result_body = f'AI 분석결과 "{final_judgement}" 입니다.'

    if isinstance(trip_count, (int, float)) and trip_count > 0:
        judgement_body = f"AI 분석결과 트립 발생 {int(trip_count)}건이 확인되었습니다. 주요 항목은 {issue_text}입니다."
    elif isinstance(trip_count, (int, float)):
        judgement_body = f"AI 분석결과 Trip 발생은 0회입니다. 주요 확인 항목은 {issue_text}입니다."
    else:
        judgement_body = f"Trip 발생 횟수는 확인이 필요하며, 주요 확인 항목은 {issue_text}입니다."

    if rag_results:
        rag_text = " ".join(map(str, rag_results[:2]))
        analysis_body = f"1. RAG 기준으로 {rag_text}"
    elif root_causes:
        analysis_body = f"1. 가능한 원인 후보는 {', '.join(map(str, root_causes))}로 추정됩니다."
    else:
        analysis_body = "1. RAG 근거 또는 원인 후보가 없어 추가 확인이 필요합니다."

    action_body = build_action_line(analysis_json, rag_results)

    return (
        f"## 결과\n{result_body}\n\n"
        f"## 판정\n{judgement_body}\n\n"
        f"## 분석\n{analysis_body}\n\n"
        f"## 조치\n{action_body}"
    )


def generate_llm_summary(
    analysis_json: dict[str, Any],
    rag_results: list[str] | None = None,
    model_name: str | None = None,
) -> str:
    """Ollama 로컬 LLM 기반 분석 요약 생성 (결과/판정/분석/조치 4섹션)."""
    rag_results = rag_results or []
    # main.py는 rag_results를 따로 넘기지 않고 analysis_json 안에 rag_context로 넣는다 → 프롬프트 근거로 승격
    if not rag_results and isinstance(analysis_json, dict):
        rc = analysis_json.get("rag_context")
        if rc:
            rag_results = [rc] if isinstance(rc, str) else list(rc)

    model = get_local_model_name(model_name)
    prompt = build_summary_prompt(analysis_json, rag_results)

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "너는 Compressor 제어검증 분석 결과를 한국어로 요약하는 전문 AI Agent이다. "
                        "반드시 '## 결과', '## 판정', '## 분석', '## 조치' 네 섹션만 출력하라. "
                        "판정에는 발생 여부와 횟수만 쓰고, 원인은 분석에, 조치는 조치 섹션에만 작성하라. "
                        "RAG에 없는 내용을 지어내지 마라."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            options={"temperature": 0.1, "num_predict": 512},
        )

        content = response["message"]["content"].strip()
        if not content:
            fallback = generate_rule_based_summary(analysis_json, rag_results)
            return f"[로컬 LLM 응답이 비어 있어 rule-based 요약을 반환합니다]\n사용 모델: {model}\n\n{fallback}"

        return normalize_summary_format(content, analysis_json, rag_results)

    except Exception as exc:
        fallback = generate_rule_based_summary(analysis_json, rag_results)
        return f"[로컬 LLM 호출 실패로 rule-based 요약을 반환합니다]\n사용 모델: {model}\n오류 내용: {exc}\n\n{fallback}"
