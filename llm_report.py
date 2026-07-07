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

    prompt = """
너는 Compressor Raw Data 분석 결과를 엔지니어가 이해하기 쉽게 정리하는 AI 분석 Agent이다.

아래 분석 결과 JSON과 RAG 검색 근거를 바탕으로,
사용자가 빠르게 이해할 수 있도록 최종 분석 문장을 작성하는 것이다.

[분석 결과 JSON]
__ANALYSIS_JSON__

[RAG 검색 근거]
__RAG_RESULTS__

출력 형식은 반드시 아래 4개 항목만 사용한다.
항목 이름을 바꾸거나 추가하지 마라.

너는 반드시 아래 순서로 답변한다.

1.결과
2.판정
3.해석
4.조치

1. 결과: <PASS / 관리필요 / FAIL 중 하나>

결과 작성 규칙

결과에는 최종 판정만 간결하게 작성한다.

결과 값은 반드시 아래 세 가지 중 하나만 사용한다.

PASS
FAIL
관리필요

작성 형식:

AI 분석결과 "{PASS/FAIL/관리필요}" 입니다.

판정 기준:

PASS: Trip 발생이 없고, 주요 이상 운전 구간이 확인되지 않으며, Rule 기준상 정상으로 판단되는 경우
FAIL: Trip 발생, 명확한 보호동작, 또는 심각한 비정상 운전 구간이 확인된 경우
관리필요: Trip은 발생하지 않았지만 비정상 경향, 제어성능 저하, 기동 약화, 기준 근접, 추가 검토가 필요한 경우

2. 판정: <Trip 발생 여부, 발생 횟수, 발생한 Trip 종류 또는 주요 이상 항목만 작성>

판정 작성 규칙

판정에는 전체 이벤트 요약을 작성한다.

반드시 아래 항목을 포함한다.

Trip 발생 여부
Trip 발생 횟수
Trip 종류별 발생 횟수
비정상 운전구간 발생 횟수
관리필요 구간 여부

작성 형식 예시:
1) Trip이 발생한 경우 - AI 분석결과 트립 발생 3건이 확인되었습니다. 
6번 과전류 Trip 2회, 7번 FO/IPM 보호 Trip 1회가 발생하였으며, 비정상 운전구간 1구간이 추가로 확인되었습니다.
2) Trip이 없는 경우 - AI 분석결과 Trip 발생은 확인되지 않았습니다. 
다만 비정상 운전 의심구간 1구간이 확인되어 관리필요로 판단됩니다.
3) 정상인 경우 - AI 분석결과 Trip 발생 및 비정상 운전구간은 확인되지 않았습니다.
주요 운전 신호가 정상 범위 내에서 안정적으로 유지되어 PASS로 판단됩니다.

3. 해석: <RAG 검색 근거와 Rule 분석 결과를 바탕으로 Raw Data에서 확인된 이상현상 발생 시점과 해석을 작성한다.>

해석 작성 규칙:

시간 순서대로 작성한다.
각 항목은 번호를 붙인다.
각 항목에는 발생 시점, 발생 현상, 해석을 포함한다.
너무 길게 쓰지 말고, 엔지니어가 빠르게 이해할 수 있도록 간결하게 작성한다.
CSV로 확인 가능한 근거와 추정 내용을 구분한다.
CSV로 직접 확인할 수 없는 내부 신호는 단정하지 않는다.

작성 형식:
1) {시간}초 구간에서 {현상}이 확인되었습니다. {간략 해석}
2) {시간}초 구간에서 {현상}이 확인되었습니다. {간략 해석}
3) {시간}초 구간에서 {현상}이 확인되었습니다. {간략 해석}

작성 예시:
1) 1230초 구간에서 6번 과전류 Trip이 발생하였습니다. 해당 구간에서는 Trip 직전 운전 부하가 증가한 것으로 보이며, 과부하에 따른 보호동작 가능성이 있습니다.
2) 1590초 구간에서 7번 FO/IPM 보호 Trip이 발생하였습니다. 기동 과정에서 운전 안정성이 저하되었고, 인버터 보호동작이 개입된 것으로 판단됩니다.
3) 2500초 구간에서 비정상 운전구간이 확인되었습니다. Trip으로 이어지지는 않았으나 차압기동 약화 또는 제어성능 저하 가능성이 있어 관리가 필요합니다.

4. 조치: <조치에는 RAG 검색 근거, Trip Case DB, Analysis Rule DB, 엔지니어 피드백 DB에서 확인되는 점검 필요 항목과 조치 방향을 짧게 작성한다.>
조치 작성 규칙:

분석 항목과 동일한 번호를 사용한다.
각 이상 구간별로 조치 또는 점검 항목을 작성한다.
조치가 불확실한 경우 “확인이 필요합니다”라고 표현한다.
원인을 단정하지 말고 “가능성”, “의심”, “확인 필요” 표현을 사용한다.
필요 시 “컴프 SW 담당자 확인 필요” 문구를 포함한다.

작성 형식:
1) {시간}초 구간의 {현상}에 대해서는 {점검 항목} 확인이 필요합니다.
2) {시간}초 구간의 {현상}에 대해서는 {조치 방향} 검토가 필요합니다.
3) {시간}초 구간의 {현상}은 {관리 필요 사유}로 판단되며, 담당자 확인이 필요합니다.

작성 예시:
1) 1230초 구간에서 발생한 6번 과전류 Trip은 과부하 영향 가능성이 있습니다. 사이클 부하, Comp 잠김 가능성, 하네스 연결 상태를 확인할 필요가 있습니다. 추가 조치가 필요한 경우 Comp SW 담당자 확인이 필요합니다.
2) 1590초 구간에서 발생한 7번 FO/IPM 보호 Trip은 기동 시 모터 제어 불안정 또는 탈조 가능성과 연관될 수 있습니다. 기동 조건, 인버터 보호동작, 제어 파라미터 확인이 필요합니다.
3) 2500초 구간에서 차압기동 약화로 의심되는 구간이 확인되었습니다. 기동 실패로 이어지지는 않았지만 제어성능 저하 가능성이 있으므로 Comp SW 담당자 확인 후 PASS/FAIL 최종 판단이 필요합니다.

전체 출력 형식

너는 반드시 아래 형식으로만 답변한다.

## 결과
AI 분석결과 "{PASS/FAIL/관리필요}" 입니다.

## 판정
{Trip 발생 여부, Trip 종류별 발생 횟수, 비정상 운전구간 발생 횟수 요약}

## 분석
1. {발생 시점}초 구간에서 {이상현상}이 확인되었습니다. {간략 해석}
2. {발생 시점}초 구간에서 {이상현상}이 확인되었습니다. {간략 해석}
3. {발생 시점}초 구간에서 {이상현상}이 확인되었습니다. {간략 해석}

## 조치
1. {해당 구간에 대한 점검 항목 및 조치 방향}
2. {해당 구간에 대한 점검 항목 및 조치 방향}
3. {해당 구간에 대한 점검 항목 및 조치 방향}

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
14. Imag는 실제 전류값이 아니므로 정량 판단에 사용하지 않는다.
15. Current Trip Level 4.2A 또는 4.3A를 Imag 값과 직접 비교하지 않는다.
16. Imag는 “높음”, “낮음”, “급증”, “불안정” 같은 정성적 보조 신호로만 언급한다.
17. CSV에 없는 내부 신호는 단정하지 않는다.
18. IPM 온도는 PCB별 정확도 차이가 있으므로 절대값 단정 대신 경향성으로 설명한다.
19. 원인 표현은 단정하지 않고 “가능성”, “의심”, “확인 필요” 중심으로 작성한다.
20. 엔지니어가 바로 읽을 수 있도록 짧고 명확하게 작성한다.
21. 불필요한 이론 설명이나 장황한 배경 설명은 생략한다.

"""
    return (
        prompt.replace("__ANALYSIS_JSON__", str(analysis_json))
        .replace("__RAG_RESULTS__", str(rag_results))
        .strip()
    )


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