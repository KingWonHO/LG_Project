"""
LLM-001: 분석 요약 생성 모듈

분석 JSON과 RAG 검색 결과를 바탕으로
Compressor 제어검증 결과 요약문을 생성한다.

담당: 김진용
"""

import os
from typing import Any

import ollama


DEFAULT_LOCAL_MODEL = "gemma3:4b"

AVAILABLE_LOCAL_MODELS = {
    "gemma3:4b": {
        "priority": 1,
        "description": "기본 추천 모델. 한국어 요약 품질과 보고서 문장 안정성이 가장 좋음.",
    },
    "qwen2.5:3b": {
        "priority": 2,
        "description": "Qwen 계열 대체 모델. 한국어 요약 품질이 준수하고 비교적 가벼움.",
    },
    "llama3.2": {
        "priority": 3,
        "description": "경량 대체 모델. 실행 속도는 빠르지만 요약 중복 가능성이 있음.",
    },
}


def get_local_model_name(model_name: str | None = None) -> str:
    """
    사용할 로컬 LLM 모델명을 결정한다.

    우선순위:
    1. 함수 인자로 전달된 model_name
    2. 환경변수 LOCAL_LLM_MODEL
    3. DEFAULT_LOCAL_MODEL
    """

    return model_name or os.getenv("LOCAL_LLM_MODEL", DEFAULT_LOCAL_MODEL)


def build_summary_prompt(
    analysis_json: dict[str, Any],
    rag_results: list[str] | None = None,
) -> str:
    """
    분석 JSON과 RAG 검색 결과를 바탕으로 로컬 LLM 요약 프롬프트를 생성한다.
    출력 형식을 결과/판정/해석/조치 4개 항목으로 제한한다.
    """

    rag_results = rag_results or []

    prompt = f"""
너는 Compressor 제어검증 데이터를 분석하는 AI Agent이다.

아래 분석 결과 JSON과 RAG 검색 근거를 바탕으로,
사용자가 빠르게 이해할 수 있도록 핵심만 요약하라.

[분석 결과 JSON]
{analysis_json}

[RAG 검색 근거]
{rag_results}

출력 형식은 반드시 아래 4개 항목만 사용한다.
항목 이름을 바꾸거나 추가하지 마라.

결과: <PASS / 관리필요 / FAIL 중 하나>

판정: <Trip 발생 여부, 발생 횟수, 발생한 Trip 종류 또는 주요 이상 항목만 작성>

해석: <RAG 검색 근거에서 확인되는 원인 또는 의미만 짧게 작성>

조치: <RAG 검색 근거에서 확인되는 조치 방법 또는 우선 점검 항목만 짧게 작성>

작성 규칙:
1. 반드시 "결과:", "판정:", "해석:", "조치:" 네 항목만 출력한다.
2. 전체 출력은 6문장을 넘기지 않는다.
3. "판정:"에는 원인, 추정 원인, 가능성, 점검 방향, 개선 Action을 절대 쓰지 않는다.
4. "판정:"에는 Trip 발생 여부, 발생 횟수, 발생한 Trip 종류, 주요 이상 항목만 쓴다.
5. "해석:"에는 RAG 기반 원인, 의미만 쓴다.
6. "해석:"에는 점검, 확인, 조치, 개선, 수행 같은 조치 방법을 쓰지 않는다.
7. "조치:"에는 RAG 기반 조치 방법, 우선 점검 항목만 쓴다.
8. RAG 문장에 원인과 조치가 함께 있더라도 원인은 "해석:"에, 조치는 "조치:"에 분리해서 작성한다.
9. RAG에 없는 원인이나 조치 방법을 임의로 추가하지 않는다.
10. 분석 JSON에 없는 Trip 발생 횟수를 만들어내지 않는다.
11. Trip 발생 횟수가 0이면 "Trip 발생은 0회입니다"라고 명확히 쓴다.
12. PASS 판정이라도 주요 확인 항목이 있으면 "판정:"에 짧게 언급한다.
13. 마크다운 표, bullet, 번호 목록, JSON 형식은 사용하지 않는다.

좋은 예시:
결과: FAIL
판정: Trip 발생은 2회이며, 주요 Trip 항목은 Vdc 저하, Temperature 상승입니다.
해석: RAG 기준으로 Vdc 저하는 전원 공급 불안정 또는 인버터 입력 전압 문제와 관련될 수 있으며, Temperature 상승은 냉각 조건 불량과 관련될 수 있습니다.
조치: 전원부와 인버터 입력 전압을 우선 점검하고, 냉각 조건과 과부하 운전 여부를 확인해야 합니다.

나쁜 예시:
결과: FAIL
판정: Vdc 저하 및 Temperature 상승 Trip이 2회 발생했습니다. 주요 원인은 전원 공급 불안정 또는 냉각 조건 불량입니다.
해석: 전원부와 냉각 조건을 점검해야 합니다.
조치: 추가 확인이 필요합니다.
"""
    return prompt.strip()


def generate_rule_based_summary(
    analysis_json: dict[str, Any],
    rag_results: list[str] | None = None,
) -> str:
    """
    로컬 LLM 호출 실패 시 사용할 수 있는 기본 rule-based 요약 생성 함수.
    결과/판정/해석/조치 4개 항목 형식으로 반환한다.
    """

    rag_results = rag_results or []

    final_judgement = analysis_json.get("final_judgement", "UNKNOWN")
    trip_count = analysis_json.get("trip_count", 0)
    abnormal_items = analysis_json.get("abnormal_items", [])
    trip_items = analysis_json.get("trip_items", [])
    root_causes = analysis_json.get("root_cause_candidates", [])
    recommended_actions = analysis_json.get("recommended_actions", [])

    issue_items = trip_items or abnormal_items

    if issue_items:
        issue_text = ", ".join(map(str, issue_items))
    else:
        issue_text = "주요 이상 항목 없음"

    result_line = f"결과: {final_judgement}"

    if isinstance(trip_count, (int, float)):
        if trip_count > 0:
            judgement_line = (
                f"판정: Trip 발생은 {trip_count}회이며, "
                f"주요 Trip 항목은 {issue_text}입니다."
            )
        else:
            judgement_line = (
                f"판정: Trip 발생은 0회입니다. "
                f"주요 확인 항목은 {issue_text}입니다."
            )
    else:
        judgement_line = (
            f"판정: Trip 발생 횟수는 확인이 필요하며, "
            f"주요 확인 항목은 {issue_text}입니다."
        )

    if rag_results:
        rag_text = " ".join(map(str, rag_results[:2]))
        interpretation_line = f"해석: RAG 기준으로 {rag_text}"
    elif root_causes:
        cause_text = ", ".join(map(str, root_causes))
        interpretation_line = f"해석: 가능한 원인 후보는 {cause_text}로 추정됩니다."
    else:
        interpretation_line = "해석: RAG 근거 또는 원인 후보가 없어 추가 확인이 필요합니다."

    if recommended_actions:
        action_text = ", ".join(map(str, recommended_actions))
        action_line = f"조치: {action_text}을 우선 수행해야 합니다."
    else:
        action_line = "조치: RAG 기반 조치 방법이 없어 담당 엔지니어의 추가 확인이 필요합니다."

    return f"{result_line}\n{judgement_line}\n{interpretation_line}\n{action_line}"


def generate_llm_summary(
    analysis_json: dict[str, Any],
    rag_results: list[str] | None = None,
    model_name: str | None = None,
) -> str:
    """
    Ollama 로컬 LLM 기반 분석 요약 생성 함수.

    Args:
        analysis_json: 분석 결과 JSON
        rag_results: RAG 검색 결과 문장 목록
        model_name: 사용할 Ollama 모델명

    Returns:
        자연어 분석 요약문
    """

    rag_results = rag_results or []
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
                        "반드시 결과, 판정, 해석, 조치 네 항목만 출력하라. "
                        "판정에는 발생 여부와 횟수만 쓰고, 원인과 조치 내용은 각각 해석과 조치에만 작성하라."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            options={
                "temperature": 0.1,
                "num_predict": 256,
            },
        )

        content = response["message"]["content"].strip()

        if not content:
            fallback_summary = generate_rule_based_summary(analysis_json, rag_results)
            return (
                "[로컬 LLM 응답이 비어 있어 rule-based 요약을 반환합니다]\n"
                f"사용 모델: {model}\n\n"
                f"{fallback_summary}"
            )

        return normalize_summary_format(content, analysis_json, rag_results)

    except Exception as exc:
        fallback_summary = generate_rule_based_summary(analysis_json, rag_results)
        return (
            "[로컬 LLM 호출 실패로 rule-based 요약을 반환합니다]\n"
            f"사용 모델: {model}\n"
            f"오류 내용: {exc}\n\n"
            f"{fallback_summary}"
        )
        
def normalize_summary_format(
    summary: str,
    analysis_json: dict[str, Any],
    rag_results: list[str] | None = None,
) -> str:
    """
    LLM 출력에서 결과/판정/해석/조치 항목만 유지한다.
    판정 항목에는 원인/해석/점검 표현이 들어가지 않도록 보정한다.
    조치 항목이 누락되면 analysis_json 또는 RAG 근거를 기반으로 자동 생성한다.
    """

    rag_results = rag_results or []
    lines = [line.strip() for line in summary.splitlines() if line.strip()]

    result = None
    judgement = None
    interpretation = None
    action = None

    for line in lines:
        if line.startswith("결과:") and result is None:
            result = line
        elif line.startswith("판정:") and judgement is None:
            judgement = line
        elif line.startswith("해석:") and interpretation is None:
            interpretation = line
        elif line.startswith("조치:") and action is None:
            action = line

    if judgement:
        judgement = clean_judgement_line(judgement)
    
    if interpretation:
        interpretation = clean_interpretation_line(interpretation)

    if action is None:
        action = build_action_line(analysis_json, rag_results)

    if result and judgement and interpretation and action:
        return f"{result}\n{judgement}\n{interpretation}\n{action}"

    return generate_rule_based_summary(analysis_json, rag_results)

def clean_judgement_line(judgement: str) -> str:
    """
    판정 항목에서 원인/해석/점검/조치에 해당하는 문장을 제거한다.
    판정에는 Trip 발생 여부, 횟수, 항목만 남긴다.
    """

    forbidden_markers = [
        "주요 원인은",
        "원인은",
        "원인으로",
        "의심됩니다",
        "가능성이",
        "가능합니다",
        "관련될 수",
        "점검",
        "확인해야",
        "확인 필요",
        "조치",
        "개선",
        "따라서",
        "우선",
        "RAG 기준",
    ]

    sentences = []

    for sentence in judgement.split("."):
        sentence = sentence.strip()

        if not sentence:
            continue

        if any(marker in sentence for marker in forbidden_markers):
            continue

        sentences.append(sentence)

    if not sentences:
        return judgement

    cleaned = ". ".join(sentences)

    if not cleaned.endswith("."):
        cleaned += "."

    return cleaned

def clean_interpretation_line(interpretation: str) -> str:
    """
    해석 항목에서 조치/점검/개선에 해당하는 문장을 제거한다.
    해석에는 RAG 기반 원인과 의미만 남긴다.
    """

    action_markers = [
        "조치",
        "점검",
        "확인",
        "교체",
        "개선",
        "재설정",
        "보정",
        "확보",
        "수행",
        "필요합니다",
        "해야 합니다",
        "우선",
        "따라서",
    ]

    sentences = []
    for sentence in interpretation.split("."):
        sentence = sentence.strip()
        if not sentence:
            continue

        if any(marker in sentence for marker in action_markers):
            continue

        sentences.append(sentence)

    if not sentences:
        return interpretation

    cleaned = ". ".join(sentences)

    if not cleaned.endswith("."):
        cleaned += "."

    return cleaned