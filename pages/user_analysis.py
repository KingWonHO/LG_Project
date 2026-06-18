"""사용자 분석 페이지.

와이어프레임 기준 레이아웃:
- 상단 탭: [분석] / [학습]
- 왼쪽 영역: CSV 업로드 → (실행버튼 | 컴프/전압/RT 드롭 + 컬럼선택) → 그래프
- 오른쪽 영역: 평압/차압 → Pass/Fail → 분석결과 → 리포트 출력

NOTE: src 모듈 연동부는 아래 `# TODO(src)` 주석 지점에 실제 함수를 연결하세요.
실제 구현 전에도 단독 실행되도록 안전한 placeholder로 작성되어 있습니다.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

# ----------------------------------------------------------------------------
# src 모듈 import (구현 전에는 ImportError 무시하고 placeholder 사용)
# ----------------------------------------------------------------------------
try:
    from src import (
        file_parser,
        column_mapper,
        trip_analyzer,
        verdict_engine,
        result_builder,
        chart_viewer,
        report_generator,
    )
except Exception:  # 모듈 미구현 단계에서도 페이지가 뜨도록
    file_parser = column_mapper = trip_analyzer = None
    verdict_engine = result_builder = chart_viewer = report_generator = None


# ----------------------------------------------------------------------------
# 세션 상태 초기화
# ----------------------------------------------------------------------------
def _init_state() -> None:
    defaults = {
        "raw_df": None,         # 업로드된 원본 DataFrame
        "analysis_result": None,  # 분석 결과 객체
        "verdict": None,        # Pass/Fail 판정
        "report_bytes": None,   # 생성된 리포트 파일 바이트
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


# ----------------------------------------------------------------------------
# 분석 탭
# ----------------------------------------------------------------------------
def _render_analysis_tab() -> None:
    left, right = st.columns([3, 2], gap="medium")

    # ===================== 왼쪽 영역 =====================
    with left:
        # --- CSV 파일 업로드 ---
        st.subheader("CSV 파일 업로드")
        uploaded = st.file_uploader(
            "분석할 CSV 파일을 올려주세요",
            type=["csv"],
            label_visibility="collapsed",
        )
        if uploaded is not None:
            try:
                if file_parser is not None:
                    st.session_state.raw_df = file_parser.parse(uploaded)  # TODO(src)
                else:
                    st.session_state.raw_df = pd.read_csv(uploaded)
                st.success(f"불러온 행 수: {len(st.session_state.raw_df):,}")
            except Exception as e:
                st.error(f"파일 파싱 실패: {e}")

        st.divider()

        # --- 실행버튼 | 드롭다운 + 컬럼선택 ---
        run_col, opt_col = st.columns([1, 2], gap="small")

        with run_col:
            run = st.button("실행", type="primary", use_container_width=True)

        with opt_col:
            d1, d2, d3 = st.columns(3)
            comp = d1.selectbox("컴프", ["전체", "ON", "OFF"], key="comp_sel")
            volt = d2.selectbox("전압", ["전체", "정격", "저전압", "고전압"], key="volt_sel")
            rt = d3.selectbox("RT", ["전체", "RT1", "RT2", "RT3"], key="rt_sel")

            df = st.session_state.raw_df
            col_options = list(df.columns) if df is not None else []
            selected_cols = st.multiselect(
                "컬럼선택",
                options=col_options,
                default=col_options[: min(3, len(col_options))],
                key="col_sel",
            )

        # --- 실행 로직 ---
        if run:
            _run_analysis(comp, volt, rt, selected_cols)

        st.divider()

        # --- 그래프 ---
        st.subheader("그래프")
        result = st.session_state.analysis_result
        if result is None:
            st.info("실행 버튼을 누르면 그래프가 표시됩니다.")
        else:
            if chart_viewer is not None:
                chart_viewer.render(result)  # TODO(src)
            else:
                df = st.session_state.raw_df
                cols = st.session_state.get("col_sel") or []
                if df is not None and cols:
                    st.line_chart(df[cols])
                else:
                    st.info("표시할 데이터/컬럼이 없습니다.")

    # ===================== 오른쪽 영역 =====================
    with right:
        # --- 평압/차압 ---
        st.subheader("평압 / 차압")
        mode = st.radio(
            "분석 모드",
            ["평압", "차압"],
            horizontal=True,
            label_visibility="collapsed",
            key="pressure_mode",
        )

        # --- Pass / Fail ---
        verdict = st.session_state.verdict
        if verdict == "PASS":
            st.success("PASS")
        elif verdict == "FAIL":
            st.error("FAIL")
        else:
            st.metric("Pass / Fail", "-")

        st.divider()

        # --- 분석결과 ---
        st.subheader("분석결과")
        result = st.session_state.analysis_result
        if result is None:
            st.caption("아직 분석 결과가 없습니다.")
        elif isinstance(result, pd.DataFrame):
            st.dataframe(result, use_container_width=True)
        else:
            st.write(result)

        st.divider()

        # --- 리포트 출력 ---
        st.subheader("리포트 출력")
        gen = st.button("리포트 생성", use_container_width=True)
        if gen:
            _generate_report()
        if st.session_state.report_bytes is not None:
            st.download_button(
                "리포트 다운로드",
                data=st.session_state.report_bytes,
                file_name="analysis_report.pdf",
                use_container_width=True,
            )


def _run_analysis(comp, volt, rt, selected_cols) -> None:
    """실행 버튼 핸들러."""
    df = st.session_state.raw_df
    if df is None:
        st.warning("먼저 CSV 파일을 업로드하세요.")
        return

    options = {"comp": comp, "volt": volt, "rt": rt, "columns": selected_cols,
               "mode": st.session_state.get("pressure_mode", "평압")}

    try:
        if trip_analyzer is not None and result_builder is not None:
            analysis = trip_analyzer.analyze(df, options)        # TODO(src)
            st.session_state.analysis_result = result_builder.build(analysis)  # TODO(src)
            if verdict_engine is not None:
                st.session_state.verdict = verdict_engine.judge(analysis)      # TODO(src)
        else:
            # placeholder: 선택 컬럼 요약 통계
            cols = selected_cols or list(df.columns)
            st.session_state.analysis_result = df[cols].describe()
            st.session_state.verdict = "PASS"
        st.success("분석 완료")
    except Exception as e:
        st.error(f"분석 실패: {e}")


def _generate_report() -> None:
    """리포트 생성 핸들러."""
    result = st.session_state.analysis_result
    if result is None:
        st.warning("먼저 분석을 실행하세요.")
        return
    try:
        if report_generator is not None:
            st.session_state.report_bytes = report_generator.generate(result)  # TODO(src)
        else:
            st.session_state.report_bytes = b"placeholder report"
        st.success("리포트 생성 완료")
    except Exception as e:
        st.error(f"리포트 생성 실패: {e}")


# ----------------------------------------------------------------------------
# 학습 탭
# ----------------------------------------------------------------------------
def _render_learning_tab() -> None:
    st.subheader("학습")
    st.info("학습 기능은 추후 구현 예정입니다. (baseline_manager / rule_manager 연동)")


# ----------------------------------------------------------------------------
# 엔트리
# ----------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="사용자 분석", layout="wide")
    _init_state()

    tab_analysis, tab_learning = st.tabs(["분석", "학습"])
    with tab_analysis:
        _render_analysis_tab()
    with tab_learning:
        _render_learning_tab()


# Streamlit 멀티페이지에서 pages/ 하위 파일은 페이지 진입 시 실행됩니다.
main()
