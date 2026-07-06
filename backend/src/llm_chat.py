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
        "아래 [분석 컨텍스트]를 근거로 사용자의 질문에 답하라. "
        "컨텍스트에 없는 내용은 단정하지 말고 '추정' 또는 '추가 확인 필요'로 표현하라. "
        "간결하고 실무적으로 답한다.\n\n[분석 컨텍스트]\n" + (context or "(컨텍스트 없음)")
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
