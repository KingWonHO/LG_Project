"""엔지니어/관리자 페이지.

ADM-001 방어적 권한 확인: 직접 URL 접근 등으로 들어와도 비엔지니어는 차단.
실제 기능(ENG-001~006)은 추후 구현.
"""

from __future__ import annotations

import streamlit as st

# --- 권한 가드 (defense-in-depth) ---
if st.session_state.get("role") != "engineer":
    st.error("엔지니어 권한이 필요합니다. 사이드바에서 엔지니어 로그인 후 이용하세요.")
    st.stop()

st.title("엔지니어 관리")
st.caption("Trip Code · 정상 기준(baseline) · Rule · Prompt 등록/수정 및 DB 반영")

tab_data, tab_trip, tab_baseline, tab_rule, tab_prompt = st.tabs(
    ["정상 데이터", "Trip Code", "정상 기준", "Rule JSON", "Prompt"]
)

with tab_data:
    st.subheader("정상 데이터 업로드 (ENG-001)")
    st.file_uploader("baseline 생성용 정상 데이터", type=["csv", "xlsx"])
    st.info("추후 baseline_manager 연동 예정")

with tab_trip:
    st.subheader("Trip Code 등록/수정 (ENG-002)")
    st.info("추후 rule_manager 연동 예정")

with tab_baseline:
    st.subheader("정상 기준 등록/수정 (ENG-003)")
    st.info("추후 baseline_manager 연동 예정")

with tab_rule:
    st.subheader("Rule JSON 등록/수정 (ENG-004)")
    st.info("추후 rule_manager 연동 예정")

with tab_prompt:
    st.subheader("Prompt 등록/수정 (ENG-005)")
    st.info("추후 prompt_manager 연동 예정")

st.divider()
if st.button("DB 반영 (ENG-006)", type="primary"):
    st.warning("DB 반영 기능은 추후 db_manager 연동 후 활성화됩니다.")
