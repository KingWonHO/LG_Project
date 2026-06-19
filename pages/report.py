"""리포트 페이지 (RPT-001) — UI 목업.

※ 프론트 목업 단계: 백엔드 미연동. 더미 텍스트로 리포트 레이아웃만 구성.
"""

from __future__ import annotations

import streamlit as st

st.title("리포트")
st.caption("분석 요약 · Trip 분석 · 이상 항목 · 원인 후보 · 조치 권고 (목업)")

if st.session_state.get("analysis_result") is None:
    st.info("'사용자 분석'에서 분석을 실행하면 리포트가 생성됩니다. (아래는 목업 예시)")

st.subheader("분석 요약")
st.write(
    "업로드 데이터에서 Trip 3회(구간 150~172)가 감지되었고, CoolingPower가 "
    "정상 baseline 상한을 초과하여 **관리필요**로 판정되었습니다."
)

col1, col2, col3 = st.columns(3)
col1.metric("최종 판정", "관리필요")
col2.metric("Trip 발생", "3회")
col3.metric("이상 항목", "2건")

st.subheader("원인 후보 (LLM-002)")
st.markdown(
    "- 냉매 부족 가능성 — CoolingPower 저하 패턴\n"
    "- 컴프 과부하 — Trip 구간 전류 급증\n"
    "- 센서 노이즈 — 일부 구간 이상치"
)

st.subheader("조치 권고 (LLM-003)")
st.markdown(
    "- 냉매 충전량 점검\n"
    "- 컴프 전류 파형 재측정\n"
    "- 해당 RT 센서 캘리브레이션"
)

st.divider()
st.download_button(
    "리포트 다운로드 (목업)",
    data=b"%PDF-1.4 mockup report",
    file_name="analysis_report.pdf",
)
