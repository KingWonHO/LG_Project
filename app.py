"""메인 엔트리 / 화면 분리 (ADM-001).

일반 사용자: 분석·리포트·이력 화면만 접근.
엔지니어: 접근 코드 인증 후 관리(엔지니어) 화면까지 접근.

st.navigation 으로 역할에 따라 노출 페이지를 제어한다.
(st.navigation 사용 시 Streamlit은 pages/ 자동 네비게이션 대신 이 정의를 사용한다.)

※ 프론트 목업 단계: 백엔드(src) 미연동.
실행: streamlit run app.py  (또는 uv run streamlit run app.py)
"""

from __future__ import annotations

import streamlit as st

# 목업용 접근 코드. 실제 연동 시 settings.engineer_access_code 로 교체.
MOCK_ACCESS_CODE = "1234"

st.set_page_config(page_title="LG Comp 확인 에이전트", layout="wide")


def _init_state() -> None:
    st.session_state.setdefault("role", "user")  # "user" | "engineer"


def _render_sidebar_auth() -> None:
    """사이드바: 현재 역할 표시 + 엔지니어 로그인/로그아웃 (ADM-001)."""
    with st.sidebar:
        st.markdown("### 접근 권한")

        if st.session_state.role == "engineer":
            st.success("엔지니어 모드")
            if st.button("로그아웃", use_container_width=True):
                st.session_state.role = "user"
                st.rerun()
        else:
            st.info("일반 사용자 모드")
            with st.expander("엔지니어 로그인"):
                code = st.text_input("접근 코드", type="password", key="eng_code")
                if st.button("로그인", use_container_width=True):
                    if code and code == MOCK_ACCESS_CODE:
                        st.session_state.role = "engineer"
                        st.rerun()
                    else:
                        st.error("접근 코드가 올바르지 않습니다.")


def main() -> None:
    _init_state()
    _render_sidebar_auth()

    user_pages = [
        st.Page("pages/user_analysis.py", title="사용자 분석",
                icon=":material/analytics:", default=True),
        st.Page("pages/report.py", title="리포트", icon=":material/description:"),
        st.Page("pages/history.py", title="분석 이력", icon=":material/history:"),
    ]
    engineer_pages = [
        st.Page("pages/engineer_admin.py", title="엔지니어 관리",
                icon=":material/build:"),
    ]

    groups = {"분석": user_pages}
    if st.session_state.role == "engineer":
        groups["관리"] = engineer_pages

    st.navigation(groups).run()


main()
