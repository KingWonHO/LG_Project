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

[실측 데이터 (백엔드가 DATA_REQUEST에 답한 실제 수치. 있으면 이 값만 사용)]
__FETCHED__

■ 실제 수치가 필요하면(예: 특정 시점의 MtoC/Power/Real_Hz 값) 답변을 쓰지 말고, 먼저 아래 한 줄만 출력한다:
DATA_REQUEST: [15@<초>, 7@<초>]
   - 컬럼은 룰 태그 [번호|이름]의 번호를 쓴다 (예: [15|MtoC]→15, [7|Power]→7, [5|Real_Hz]→5, [20|Trip]→20).
   - 시점(초)은 반드시 trip_events의 실제 start/end 값을 쓴다. [실측 데이터]에 값이 이미 있으면 그 값만 쓰고 DATA_REQUEST를 다시 내지 않는다.

■ 엔지니어 분석 규칙의 조건/코드/수치(예: "Trip=6 or 7 or 5", "MtoC=홀수로 변경")는 판단 기준일 뿐이다.
   그 문장을 그대로 옮기지 말고, trip_events의 실제 발생 코드/시간과 [실측 데이터]의 실제 수치로만 서술한다.
   룰에 나열된 후보 코드/조건을 그대로 나열하지 마라.

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
13. 엔지니어 룰의 조건문/후보 코드/기호 조건(MtoC=홀수 등)을 그대로 복사하지 않는다. 실제 발생 코드(trip_events)와 [실측 데이터]의 실제 수치로 바꿔 쓴다.
14. MtoC 등 특정 시점의 실제 값이 필요하면 DATA_REQUEST로 요청해 받은 [실측 데이터] 값만 사용한다. 값이 없으면 그 수치를 단정하지 않는다.

이제 위 형식대로만 답변한다.
"""
    fetched = analysis_json.get("fetched_values") if isinstance(analysis_json, dict) else None
    fetched_text = str(fetched) if fetched else "(아직 없음 — 필요하면 DATA_REQUEST로 요청)"
    return (
        prompt.replace("__ANALYSIS_JSON__", str(analysis_json))
        .replace("__RAG_RESULTS__", str(rag_results))
        .replace("__FETCHED__", fetched_text)
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


def _call_llm(prompt: str, model: str) -> str:
    """단일 LLM 호출 → content 문자열 반환."""
    response = ollama.chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "너는 Compressor 제어검증 분석 결과를 한국어로 요약하는 전문 AI Agent이다. "
                    "반드시 '## 결과', '## 판정', '## 분석', '## 조치' 네 섹션만 출력하라. "
                    "판정에는 발생 여부와 횟수만 쓰고, 원인은 분석에, 조치는 조치 섹션에만 작성하라. "
                    "엔지니어 룰의 조건/후보 코드를 그대로 복사하지 말고 실제 발생값(trip_events)과 실측 데이터만 사용하라. "
                    "필요한 실제 수치가 있으면 'DATA_REQUEST: [지표@초]' 한 줄만 먼저 출력하라."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0.1, "num_predict": 512},
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
    """Ollama 로컬 LLM 기반 요약 (결과/판정/분석/조치 4섹션).

    data_fetcher: LLM이 DATA_REQUEST로 실제 수치를 요청하면, 그 목록(list[str])을 받아
    실측값(dict)을 돌려주는 콜백(main.py가 df 접근해 제공). None이면 요청 기능 비활성.
    """
    rag_results = rag_results or []
    if not rag_results and isinstance(analysis_json, dict):
        rc = analysis_json.get("rag_context")
        if rc:
            rag_results = [rc] if isinstance(rc, str) else list(rc)

    model = get_local_model_name(model_name)
    try:
        # 1차: 답변 또는 DATA_REQUEST
        content = _call_llm(build_summary_prompt(analysis_json, rag_results), model)

        # LLM이 실제 수치를 요청했고 콜백이 있으면 → 백엔드에서 받아 2차 생성
        reqs = _parse_data_request(content)
        if reqs and data_fetcher is not None:
            try:
                fetched = data_fetcher(reqs)
            except Exception:
                fetched = {}
            if fetched:
                aj2 = {**analysis_json, "fetched_values": fetched}
                content = _call_llm(build_summary_prompt(aj2, rag_results), model)

        content = _strip_data_request(content)
        if not content:
            fb = generate_rule_based_summary(analysis_json, rag_results)
            return f"[로컬 LLM 응답이 비어 있어 rule-based 요약을 반환합니다]\n사용 모델: {model}\n\n{fb}"

        return normalize_summary_format(content, analysis_json, rag_results)

    except Exception as exc:
        fb = generate_rule_based_summary(analysis_json, rag_results)
        return f"[로컬 LLM 호출 실패로 rule-based 요약을 반환합니다]\n사용 모델: {model}\n오류 내용: {exc}\n\n{fb}"
