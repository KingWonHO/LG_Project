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
    """

    rag_results = rag_results or []

    prompt = f"""
너는 Compressor 제어검증 데이터를 분석하는 AI Agent이다.

아래 분석 결과 JSON과 RAG 검색 근거를 바탕으로,
비전문가도 이해할 수 있는 한국어 분석 요약문을 작성하라.

[분석 결과 JSON]
{analysis_json}

[RAG 검색 근거]
{rag_results}

작성 조건:
1. 최종 판정을 첫 문장에 명확히 제시한다.
2. Trip 발생 여부와 발생 횟수를 설명한다.
3. 주요 이상 항목을 요약한다.
4. baseline 이탈 항목이 있으면 어떤 항목이 문제인지 설명한다.
5. RAG 검색 근거를 바탕으로 가능한 원인 후보를 제시한다.
6. 원인은 단정하지 말고 "가능성이 있다", "추정된다"와 같이 표현한다.
7. 마지막에는 우선 점검해야 할 개선 Action을 제시한다.
8. 전체 분량은 5~7문장 이내로 작성한다.
9. JSON이나 마크다운 표가 아니라 일반 문단으로 작성한다.
10. 분석 결과에 없는 내용을 임의로 추가하지 않는다.
"""
    return prompt.strip()


def generate_rule_based_summary(
    analysis_json: dict[str, Any],
    rag_results: list[str] | None = None,
) -> str:
    """
    로컬 LLM 호출 실패 시 사용할 수 있는 기본 rule-based 요약 생성 함수.
    """

    rag_results = rag_results or []

    final_judgement = analysis_json.get("final_judgement", "UNKNOWN")
    trip_count = analysis_json.get("trip_count", 0)
    abnormal_items = analysis_json.get("abnormal_items", [])
    baseline_deviation = analysis_json.get("baseline_deviation", [])
    data_quality = analysis_json.get("data_quality", "확인 필요")
    root_causes = analysis_json.get("root_cause_candidates", [])
    actions = analysis_json.get("recommended_actions", [])

    summary_parts: list[str] = []

    summary_parts.append(f"최종 분석 결과는 {final_judgement}로 판단됩니다.")

    if isinstance(trip_count, (int, float)) and trip_count > 0:
        summary_parts.append(f"분석 구간에서 Trip이 {trip_count}회 발생했습니다.")
    else:
        summary_parts.append("분석 구간에서 Trip 발생은 확인되지 않았습니다.")

    if abnormal_items:
        abnormal_text = ", ".join(map(str, abnormal_items))
        summary_parts.append(f"주요 이상 항목은 {abnormal_text}입니다.")
    else:
        summary_parts.append("뚜렷한 주요 이상 항목은 확인되지 않았습니다.")

    if baseline_deviation:
        deviation_texts = []

        for item in baseline_deviation:
            if isinstance(item, dict):
                column = item.get("column", "알 수 없는 항목")
                description = item.get("description", "baseline 이탈이 확인됨")
                deviation_texts.append(f"{column}: {description}")
            else:
                deviation_texts.append(str(item))

        summary_parts.append(
            "Baseline 이탈 항목은 "
            + "; ".join(deviation_texts)
            + "입니다."
        )

    summary_parts.append(f"데이터 품질 상태는 {data_quality}입니다.")

    if rag_results:
        evidence_text = " ".join(map(str, rag_results[:2]))
        summary_parts.append(f"관련 사례 및 근거에 따르면, {evidence_text}")

    if root_causes:
        root_cause_text = ", ".join(map(str, root_causes))
        summary_parts.append(
            f"가능한 원인 후보로는 {root_cause_text} 등이 추정됩니다."
        )

    if actions:
        action_text = ", ".join(map(str, actions))
        summary_parts.append(
            f"따라서 우선적으로 {action_text}을 수행하는 것이 필요합니다."
        )
    else:
        summary_parts.append(
            "따라서 Trip 발생 구간, 주요 센서값 변화, baseline 이탈 항목을 우선 점검하는 것이 필요합니다."
        )

    return " ".join(summary_parts)


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
                        "추론 과정은 출력하지 말고 최종 요약문만 작성하라."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            options={
                "temperature": 0.2,
                "num_predict": 512,
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

        return content

    except Exception as exc:
        fallback_summary = generate_rule_based_summary(analysis_json, rag_results)
        return (
            "[로컬 LLM 호출 실패로 rule-based 요약을 반환합니다]\n"
            f"사용 모델: {model}\n"
            f"오류 내용: {exc}\n\n"
            f"{fallback_summary}"
        )