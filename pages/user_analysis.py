"""사용자 분석 페이지 — UI 목업.

※ 프론트 목업 단계: 백엔드(src/*) 모듈을 호출하지 않고 더미 데이터로
   화면 레이아웃과 인터랙션만 구성한다. 실제 분석 로직 연동은 추후.

레이아웃(와이어프레임 기준):
- 상단 탭: [분석] / [학습]
- 좌측: CSV 업로드 → (실행버튼 | 컴프/전압/RT 드롭 + 컬럼선택) → 그래프
- 우측: 평압/차압 → Pass/Fail → 분석결과 → 리포트 출력
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# 목업용 가짜 Trip 발생 구간 (그래프 하이라이트 데모)
MOCK_TRIP_RANGE = (150, 172)


# ----------------------------------------------------------------------------
# 목업 데이터 / 상태
# ----------------------------------------------------------------------------
def _mock_timeseries(n: int = 300) -> pd.DataFrame:
    t = np.arange(n)
    rng = np.random.default_rng(42)
    comp = 50 + 5 * np.sin(t / 15) + rng.normal(0, 0.6, n)
    volt = 220 + 3 * np.sin(t / 40) + rng.normal(0, 1.0, n)
    rt = 25 + 2 * np.sin(t / 50) + rng.normal(0, 0.3, n)
    # 가짜 Trip 구간 (이상치 주입)
    a, b = MOCK_TRIP_RANGE
    comp[a:b] += 18
    return pd.DataFrame({"Time": t, "컴프전류": comp, "전압": volt, "RT": rt})


def _mock_result() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "항목": ["Trip 발생", "baseline 이탈", "데이터 품질", "최종 판정"],
            "결과": ["3회 (구간 150~172)", "CoolingPower 초과", "이상치 2건", "관리필요"],
        }
    )


def _init_state() -> None:
    defaults = {"raw_df": None, "analysis_result": None, "verdict": None, "report_bytes": None}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


# ----------------------------------------------------------------------------
# 분석 탭
# ----------------------------------------------------------------------------
def _render_analysis_tab() -> None:
    left, right = st.columns([3, 2], gap="medium")

    # ===================== 좌측 =====================
    with left:
        # --- CSV 파일 업로드 ---
        st.subheader("CSV 파일 업로드")
        up_col, sample_col = st.columns([3, 1])
        with up_col:
            uploaded = st.file_uploader(
                "분석할 CSV/XLSX 파일", type=["csv", "xlsx"], label_visibility="collapsed"
            )
        with sample_col:
            if st.button("샘플 불러오기", use_container_width=True):
                st.session_state.raw_df = _mock_timeseries()

        if uploaded is not None:
            try:
                # 목업: 미리보기용 직접 읽기 (실제 파싱은 추후 file_parser 연동)
                if uploaded.name.endswith(".xlsx"):
                    st.session_state.raw_df = pd.read_excel(uploaded)
                else:
                    st.session_state.raw_df = pd.read_csv(uploaded)
            except Exception as e:
                st.error(f"미리보기 실패: {e}")

        df = st.session_state.raw_df
        if df is not None:
            st.caption(f"불러온 행 수: {len(df):,}  ·  컬럼: {len(df.columns)}")

        st.divider()

        # --- 실행버튼 | 드롭다운 + 컬럼선택 ---
        run_col, opt_col = st.columns([1, 2], gap="small")
        with run_col:
            run = st.button("실행", type="primary", use_container_width=True)
        with opt_col:
            d1, d2, d3 = st.columns(3)
            d1.selectbox("컴프", ["전체", "ON", "OFF"], key="comp_sel")
            d2.selectbox("전압", ["전체", "정격", "저전압", "고전압"], key="volt_sel")
            d3.selectbox("RT", ["전체", "RT1", "RT2", "RT3"], key="rt_sel")

            col_options = list(df.columns) if df is not None else []
            st.multiselect(
                "컬럼선택",
                options=col_options,
                default=[c for c in ["컴프전류", "전압"] if c in col_options],
                key="col_sel",
            )

        if run:
            if df is None:
                st.warning("먼저 파일을 업로드하거나 '샘플 불러오기'를 누르세요.")
            else:
                # 목업: 고정된 더미 결과 생성
                st.session_state.analysis_result = _mock_result()
                st.session_state.verdict = "관리필요"
                st.success("분석 완료 (목업 결과)")

        st.divider()

        # --- 그래프 ---
        st.subheader("그래프")
        if df is None:
            st.info("실행 전: 파일 업로드 후 그래프가 표시됩니다.")
        else:
            cols = st.session_state.get("col_sel") or [c for c in df.columns if c != "Time"]
            x = df["Time"] if "Time" in df.columns else df.index
            fig = go.Figure()
            for c in cols:
                if c in df.columns and c != "Time":
                    fig.add_trace(go.Scatter(x=x, y=df[c], mode="lines", name=c))
            # 이상 구간(USR-006) 하이라이트 — 목업
            if st.session_state.verdict is not None:
                a, b = MOCK_TRIP_RANGE
                fig.add_vrect(x0=a, x1=b, fillcolor="red", opacity=0.15,
                              line_width=0, annotation_text="Trip 구간")
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10),
                              legend=dict(orientation="h"))
            st.plotly_chart(fig, use_container_width=True)

    # ===================== 우측 =====================
    with right:
        # --- 평압/차압 ---
        st.subheader("평압 / 차압")
        st.radio("분석 모드", ["평압", "차압"], horizontal=True,
                 label_visibility="collapsed", key="pressure_mode")

        # --- Pass / Fail ---
        verdict = st.session_state.verdict
        if verdict == "PASS":
            st.success("PASS")
        elif verdict == "FAIL":
            st.error("FAIL")
        elif verdict == "관리필요":
            st.warning("관리필요")
        else:
            st.metric("Pass / Fail", "-")

        st.divider()

        # --- 분석결과 ---
        st.subheader("분석결과")
        result = st.session_state.analysis_result
        if result is None:
            st.caption("아직 분석 결과가 없습니다.")
        else:
            st.dataframe(result, use_container_width=True, hide_index=True)

        st.divider()

        # --- 리포트 출력 ---
        st.subheader("리포트 출력")
        if st.button("리포트 생성", use_container_width=True):
            if result is None:
                st.warning("먼저 분석을 실행하세요.")
            else:
                st.session_state.report_bytes = b"%PDF-1.4 mockup report"
                st.success("리포트 생성 완료 (목업)")
        if st.session_state.report_bytes is not None:
            st.download_button(
                "리포트 다운로드",
                data=st.session_state.report_bytes,
                file_name="analysis_report.pdf",
                use_container_width=True,
            )


# ----------------------------------------------------------------------------
# 학습 탭
# ----------------------------------------------------------------------------
def _render_learning_tab() -> None:
    st.subheader("학습")
    st.info("학습 기능은 목업 단계입니다. (추후 baseline/rule 학습 연동 예정)")


# ----------------------------------------------------------------------------
# 엔트리 (set_page_config 는 app.py 에서 호출)
# ----------------------------------------------------------------------------
def main() -> None:
    _init_state()
    tab_analysis, tab_learning = st.tabs(["분석", "학습"])
    with tab_analysis:
        _render_analysis_tab()
    with tab_learning:
        _render_learning_tab()


main()
