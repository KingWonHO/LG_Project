"""llm_chat 모듈: 분석 결과 컨텍스트 기반 로컬 LLM 대화 (LLM 확장).

리포트 요약(llm_report)과 달리 다중 턴 대화를 지원한다.
컨텍스트(파라미터/MtoC/규칙/RAG)는 main.py에서 조립해 넘긴다.
"""

from __future__ import annotations

import ollama

from src.llm_report import get_local_model_name


def chat(context: str, messages: list[dict], model_name: str | None = None) -> str:
    """분석 컨텍스트 + 대화 히스토리 → 로컬 LLM 답변.

    Args:
        context: 분석 근거 텍스트 (판정/파라미터/MtoC/규칙/RAG 등)
        messages: [{"role": "user"|"assistant", "content": str}, ...]
        model_name: 사용할 모델 (기본: 환경/기본값)
    Returns:
        assistant 답변 텍스트 (실패 시 안내 문구)
    """
    model = get_local_model_name(model_name)
    system = (
        "너는 Compressor 제어검증 데이터를 분석하는 한국어 AI 어시스턴트다. "
        "아래 [분석 컨텍스트]와 RAG 근거만을 사용해 답한다.\n"
        "답변 원칙 (리포트 요약과 동일 기준):\n"
        "- 컨텍스트/RAG에 없는 원인·조치·수치(예: Trip 발생 횟수)를 임의로 만들지 않는다. 없으면 '추가 확인 필요'로 표현한다.\n"
        "- 원인/의미는 '해석'에, 점검·조치 방법은 '조치'에 분리해서 설명한다. 원인은 단정하지 말고 '가능성/추정'으로 쓴다.\n"
        "- 마크다운 표·bullet·번호목록·JSON은 쓰지 않고 간결한 한국어 문장으로 답한다.\n"
        "- 사용자가 '전체 판정/요약'을 요청하면 아래 4개 항목만으로 답한다(항목명 변경·추가 금지):\n"
        "  결과: PASS/관리필요/FAIL 중 하나\n"
        "  판정: Trip 발생 여부·횟수·종류·주요 이상 항목만 (원인·조치는 쓰지 않음)\n"
        "  해석: RAG 기반 원인·의미만\n"
        "  조치: RAG 기반 조치 방법·우선 점검 항목만\n"
        "- 특정 항목만 묻는 질문에는 위 형식에 얽매이지 말고 해당 부분만 정확히 답한다.\n\n"
        "[분석 컨텍스트]\n" + (context or "(컨텍스트 없음)")
    )
    msgs = [{"role": "system", "content": system}]
    for m in messages:
        role = m.get("role", "user")
        if role not in ("user", "assistant"):
            role = "user"
        msgs.append({"role": role, "content": str(m.get("content", ""))})

    try:
        resp = ollama.chat(model=model, messages=msgs, options={"temperature": 0.3, "num_predict": 600})
        content = resp["message"]["content"].strip()
        return content or "[빈 응답]"
    except Exception as exc:
        return f"[로컬 LLM 호출 실패: {exc}] Ollama 실행 여부를 확인하세요."
