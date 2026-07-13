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

[엔지니어 분석 규칙 — 해석기준 (판단/해석의 핵심 근거. 반드시 참고할 것)]
__ENGINEER_RULES__

■ 위 [엔지니어 분석 규칙 — 해석기준]을 판단과 해석의 핵심 근거로 반드시 참고하여 '## 판정'·'## 분석'·'## 조치'를 작성한다.
   (해석기준이 설명하는 판단 논리·정상/이상 패턴·필요조치를 근거로 삼는다.)
   단, 규칙 안의 조건문·후보 코드·기호 조건(예: "Trip=6 or 7 or 5", "MtoC=홀수로 변경")은 그대로 옮기지 말고,
   trip_events의 실제 발생 코드/시간으로 바꿔 서술한다.
   trip_events에 없는 내부 신호 수치(MtoC 등)는 단정하지 말고 정성적으로만 언급한다.

너는 반드시 아래 4개 섹션만, 아래 순서로 작성한다. 섹션 이름을 바꾸거나 추가하지 마라.

## 결과
- PASS / 관리필요 / FAIL 중 하나만 사용한다.
- 형식: AI 분석결과 "{PASS/FAIL/관리필요}" 입니다.
- 판정 기준:
  PASS: Trip 발생이 없고 주요 이상 운전 구간이 없으며 정상으로 판단되는 경우
  FAIL: Trip 발생, 명확한 보호동작, 또는 심각한 비정상 운전 구간이 확인된 경우
  관리필요: Trip은 없지만 비정상 경향/제어성능 저하/기동 약화/추가 검토가 필요한 경우

## 판정
- 총 발생 건수 + 실제 발생한 Trip 코드별 횟수만 쓴다.
- ★발생 횟수가 0인 Trip 코드는 절대 쓰지 않는다 ("7번 …0회" 금지). trip_events에 실제 있는 코드만 쓴다.
- 비정상 운전구간은 데이터에 실제 근거가 있을 때만 쓰고, 없으면 언급하지 않는다. 원인·조치 표현 금지.
- 예) AI 분석결과 트립 발생 10건이 확인되었습니다. 6번 과전류 Trip 10회.

## 분석
- trip_events의 발생마다 번호를 붙여 개별로 모두 나열한다 (묶거나 생략하지 않는다).
- 각 항목 = {실제 시점}초 구간에서 {N}번 {트립명} Trip이 확인되었습니다. + {현상 설명(현상정의/RAG 기반)} + 예상원인은 {룰의 예상원인} 가능성이 있습니다.
- ★시점·Trip 코드는 trip_events의 실제 값만 쓴다. 없는 시간/코드는 만들지 않는다.
- ★조치/점검/보고/개선/확인 필요 같은 조치 문구는 분석에 절대 넣지 않는다 (조치는 '## 조치'에만).
- 형식:
  1. {시점}초 구간에서 {N}번 {트립명} Trip이 확인되었습니다. {현상 설명}. 예상원인은 {예상원인} 가능성이 있습니다.

## 조치
- 분석과 동일한 번호·순서로, 각 발생에 대해 엔지니어 룰의 "필요조치"를 반영해 작성한다.
- 룰에 "필요조치: Comp SW 담당자에게 보고한다"가 있으면 → "Comp SW 담당자에게 보고 필요합니다."처럼 그 조치를 쓴다. 임의의 일반 문구로 대체하지 않는다.
- 형식:
  1. {시점}초 구간의 {N}번 {트립명} Trip에 대해서는 {룰의 필요조치}.

작성 규칙:
1. 반드시 "## 결과", "## 판정", "## 분석", "## 조치" 네 섹션만 출력한다.
2. "판정"에는 실제 발생한 Trip 코드별 횟수만 쓴다. 0회 코드·원인·조치는 금지.
3. "분석"에는 시점+현상+예상원인만 쓴다. 조치·점검·보고·개선·확인 필요 표현 금지.
4. "조치"에는 엔지니어 룰의 필요조치(및 RAG 조치)만 쓴다. 분석 내용과 중복하지 않는다.
5. 원인은 "분석"에, 조치는 "조치"에 분리한다. 한 문장에 원인과 조치를 섞지 않는다.
6. RAG/룰에 없는 원인·조치를 지어내지 않는다. 분석 JSON에 없는 Trip 횟수를 만들지 않는다.
7. Trip 발생이 0회면 "Trip 발생은 0회입니다"라고 쓰고, 분석·조치는 정상 관점으로 서술한다.
8. Imag는 정량 판단에 쓰지 않고 "높음/낮음/급증/불안정" 정성 신호로만 언급한다.
9. IPM 온도는 절대값 단정 대신 경향성으로 설명한다.
10. 트립이 많아도 trip_events 발생 수만큼 개별로 모두 나열한다 (묶거나 생략 금지).
11. 시점·구간·Trip 코드는 trip_events의 실제 값만 쓰고 지어내지 않는다.
12. 엔지니어 룰의 해석기준·현상정의·예상원인·필요조치를 근거로 삼되, 조건문/후보 코드/기호 조건(MtoC=홀수, Trip=6 or 7 등)은 그대로 복사하지 말고 실제 발생 코드로 바꿔 쓴다.
13. trip_events에 없는 내부 신호 수치(MtoC 등)는 단정하지 말고 정성적으로만 언급한다.

이제 위 형식대로만 답변한다.
"""
    engineer_rules_text = ""
    if isinstance(analysis_json, dict):
        engineer_rules_text = analysis_json.get("engineer_rules") or ""
    if not str(engineer_rules_text).strip():
        engineer_rules_text = "(적용되는 엔지니어 분석 규칙 없음)"
    return (
        prompt.replace("__ANALYSIS_JSON__", str(analysis_json))
        .replace("__RAG_RESULTS__", str(rag_results))
        .replace("__ENGINEER_RULES__", str(engineer_rules_text))
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


def _drop_zero_count_clauses(text: str | None) -> str | None:
    """결과/판정에서 발생하지 않은 Trip 언급('…0회' 조각)을 제거한다 (예: '7번 …0회')."""
    if not text:
        return text
    segs = re.split(r",\s*", text)
    # 숫자 0인 '0회'만 제거 (앞에 숫자가 있으면 10회·20회 등이므로 유지)
    kept = [seg for seg in segs if not re.search(r"(?<!\d)0\s*회", seg)]
    out = ", ".join(kept)
    out = re.sub(r"(가|이) 발생하였으며\s*,?\s*", "", out)
    out = re.sub(r"\s{2,}", " ", out).strip().rstrip(",").strip()
    return out


def normalize_summary_format(
    summary: str,
    analysis_json: dict[str, Any],
    rag_results: list[str] | None = None,
) -> str:
    """LLM 출력을 결과/판정/분석/조치 4섹션(## 헤더)으로 정규화한다.
    필수 섹션이 빠지면 rule-based 요약으로 대체한다."""
    rag_results = rag_results or []
    sec = _parse_sections(summary)

    result = _drop_zero_count_clauses(sec.get("결과"))
    judgement = _drop_zero_count_clauses(sec.get("판정"))
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


def _call_llm(prompt: str, model: str, num_predict: int = 512) -> str:
    """단일 LLM 호출 → content 문자열 반환. num_predict=출력 최대 토큰(트립 수에 따라 확대)."""
    response = ollama.chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "너는 Compressor 제어검증 분석 결과를 한국어로 요약하는 전문 AI Agent이다. "
                    "반드시 '## 결과', '## 판정', '## 분석', '## 조치' 네 섹션만 출력하라. "
                    "판정에는 발생 여부와 횟수만 쓰고, 원인은 분석에, 조치는 조치 섹션에만 작성하라. "
                    "엔지니어 룰의 조건/후보 코드를 그대로 복사하지 말고 실제 발생값(trip_events)만 사용하라."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0.1, "num_predict": num_predict, "num_ctx": 8192},
    )
    return (response["message"]["content"] or "").strip()


def _parse_data_request(content: str) -> list[str]:
    """LLM 출력에서 'DATA_REQUEST: [MtoC@6118, Power@6118]' 를 파싱해 ['MtoC@6118', ...] 반환."""
    m = re.search(r"DATA_REQUEST\s*:\s*\[?([^\]\n]+)\]?", content, re.IGNORECASE)
    if not m:
        return []
    items = [x.strip() for x in m.group(1).split(",") if "@" in x]
    return items[:12]


def _strip_data_request(content: str) -> str:
    """최종 출력에서 DATA_REQUEST 줄을 제거한다."""
    return "\n".join(
        ln for ln in content.splitlines() if not ln.strip().upper().startswith("DATA_REQUEST")
    ).strip()


def generate_llm_summary(
    analysis_json: dict[str, Any],
    rag_results: list[str] | None = None,
    model_name: str | None = None,
    data_fetcher=None,
) -> str:
    """Ollama 로컬 LLM 기반 요약 (결과/판정/분석/조치 4섹션, 단일 패스).

    trip_events(실제 발생 코드/구간)는 analysis_json에 이미 포함되어 프롬프트로 주입된다.
    data_fetcher: 하위호환용 파라미터(현재 미사용).
    """
    rag_results = rag_results or []
    if not rag_results and isinstance(analysis_json, dict):
        rc = analysis_json.get("rag_context")
        if rc:
            rag_results = [rc] if isinstance(rc, str) else list(rc)

    model = get_local_model_name(model_name)
    # 트립이 많으면 출력이 길어지므로 출력 토큰 상한을 발생 수에 비례해 늘린다 (5회에서 잘리던 문제 해결).
    n_trips = 0
    if isinstance(analysis_json, dict):
        n_trips = max(int(analysis_json.get("trip_count") or 0), len(analysis_json.get("trip_events") or []))
    num_predict = min(2048, 640 + n_trips * 120)
    try:
        content = _call_llm(build_summary_prompt(analysis_json, rag_results), model, num_predict=num_predict)
        content = _strip_data_request(content)  # 혹시 모를 잔여 라인 방어적 제거
        if not content:
            fb = generate_rule_based_summary(analysis_json, rag_results)
            return f"[로컬 LLM 응답이 비어 있어 rule-based 요약을 반환합니다]\n사용 모델: {model}\n\n{fb}"
        return normalize_summary_format(content, analysis_json, rag_results)
    except Exception as exc:
        fb = generate_rule_based_summary(analysis_json, rag_results)
        return f"[로컬 LLM 호출 실패로 rule-based 요약을 반환합니다]\n사용 모델: {model}\n오류 내용: {exc}\n\n{fb}"
