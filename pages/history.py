"""분석 이력 페이지 (ADM-002) — UI 목업.

※ 프론트 목업 단계: 백엔드 미연동. 더미 이력 데이터로 표 레이아웃만 구성.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

st.title("분석 이력")
st.caption("과거 업로드 파일과 분석 결과를 조회합니다. (ADM-002, 목업 데이터)")

_mock_history = pd.DataFrame(
    {
        "일시": ["2026-06-18 09:12", "2026-06-17 16:40", "2026-06-17 10:05"],
        "파일명": ["comp_A_0618.csv", "comp_B_0617.xlsx", "comp_A_0617.csv"],
        "행 수": [1820, 2400, 1755],
        "판정": ["관리필요", "PASS", "FAIL"],
    }
)

# 판정 필터
opt = st.multiselect("판정 필터", ["PASS", "관리필요", "FAIL"], default=[])
view = _mock_history[_mock_history["판정"].isin(opt)] if opt else _mock_history

st.dataframe(view, use_container_width=True, hide_index=True)

selected = st.selectbox("재열람할 분석 선택", _mock_history["파일명"])
if st.button("다시 보기"):
    st.info(f"'{selected}' 결과 재열람 — 추후 db_manager 연동 예정")
