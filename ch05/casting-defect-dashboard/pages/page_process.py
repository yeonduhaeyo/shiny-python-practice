from shiny import ui, module, render
import pandas as pd
import plotly.express as px

from shinywidgets import output_widget, render_widget

from shared import df_raw


# 공정 단계별 변수 사전
PROCESS_VARS = {
    "① 용탕 준비 및 가열": [
        ("molten_temp", "용탕 온도 (℃)", "float", "용탕의 온도"),
        ("molten_volume", "용탕 부피", "float", "투입 용탕의 양(부피)"),
    ],
    "② 반고체 슬러리 제조": [
        ("sleeve_temperature", "슬리브 온도 (℃)", "float", "슬리브(슬러리 형성 구간)의 온도"),
        ("EMS_operation_time", "EMS 작동시간", "category", "전자기 교반(EMS) 작동 시간(범주형)"),
    ],
    "③ 사출 & 금형 충전": [
        ("cast_pressure", "주조 압력 (bar)", "float", "사출 시 가해지는 압력"),
        ("low_section_speed", "저속 구간 속도", "float", "저속 구간 사출 속도"),
        ("high_section_speed", "고속 구간 속도", "float", "고속 구간 사출 속도"),
        ("physical_strength", "형체력", "float", "금형 체결력(형체력)"),
        ("biscuit_thickness", "비스킷 두께", "float", "비스킷 두께"),
    ],
    "④ 응고 · 냉각": [
        ("upper_mold_temp1", "상형 온도1 (℃)", "float", "상형 온도(센서1)"),
        ("upper_mold_temp2", "상형 온도2 (℃)", "float", "상형 온도(센서2)"),
        ("lower_mold_temp1", "하형 온도1 (℃)", "float", "하형 온도(센서1)"),
        ("lower_mold_temp2", "하형 온도2 (℃)", "float", "하형 온도(센서2)"),
        ("Coolant_temperature", "냉각수 온도 (℃)", "float", "냉각수 온도"),
    ],
    "⑤ 기타": [
        ("mold_code", "금형 코드", "category", "금형 식별 코드"),
        ("working", "작업 여부", "category", "설비 가동 상태(가동/정지 등)"),
        ("tryshot_signal", "트라이샷 신호", "category", "트라이샷 여부를 나타내는 신호"),
        ("count", "생산 횟수", "int", "누적 생산 카운트"),
        ("facility_operation_cycleTime", "설비 가동 사이클타임", "float", "설비 가동 사이클 시간"),
        ("production_cycletime", "생산 사이클타임", "float", "실제 생산 사이클 시간"),
    ],
}


# 전역 메타(한글명/타입) 매핑
VAR_META = {}
for proc_name, rows in PROCESS_VARS.items():
    for col, kr, vtype, desc in rows:
        VAR_META[col] = {"kr": kr, "type": vtype, "process": proc_name, "desc": desc}


def build_dict_df(process_name: str) -> pd.DataFrame:
    rows = PROCESS_VARS.get(process_name, [])
    return pd.DataFrame(rows, columns=["변수명(영문)", "변수명(한글)", "타입", "설명"])


# Plotly 분포 그래프
#    - 범주형: 전체 범주 빈도 막대
#    - 수치형: 히스토그램
#    - 스타일: 흰 배경 + 축 표시
def plot_distribution_plotly(df: pd.DataFrame, col: str):
    kr = VAR_META.get(col, {}).get("kr", col)
    vtype = VAR_META.get(col, {}).get("type", "float")

    def _apply_style(fig):
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(l=10, r=10, t=45, b=10),
            height=330,
            title=dict(x=0.0, xanchor="left"),
        )
        fig.update_xaxes(showline=True, linewidth=1, linecolor="black", ticks="outside")
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black", ticks="outside")
        return fig

    if col not in df.columns:
        fig = px.scatter(title=f"{kr} 빈도")
        fig.add_annotation(text="컬럼이 데이터에 없습니다.", showarrow=False)
        return _apply_style(fig)

    s = df[col].copy()

    if vtype == "category":
        vc = (
            s.astype("string")
            .fillna("NA")
            .value_counts(dropna=False)
            .reset_index()
        )
        vc.columns = ["범주", "건수"]

        fig = px.bar(vc, x="범주", y="건수", title=f"{kr} 빈도")
        fig.update_xaxes(tickangle=45)
        return _apply_style(fig)

    s_num = pd.to_numeric(s, errors="coerce").dropna()
    d = pd.DataFrame({kr: s_num})
    fig = px.histogram(d, x=kr, nbins=30, title=f"{kr} 히스토그램")
    return _apply_style(fig)


# UI helper: 공정 탭 1개 생성
def process_panel(process_name: str, select_id: str):
    choices = {col: kr for col, kr, _, _ in PROCESS_VARS[process_name]}

    return ui.nav_panel(
        process_name,

        ui.card(
            ui.card_header("변수 사전"),
            ui.output_data_frame(f"dict_{select_id}"),
            class_="mb-3",
        ),

        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("변수 선택"),
                ui.input_select(select_id, "변수", choices=choices),
            ),
            ui.card(
                ui.card_header("원본 데이터 분포"),
                output_widget(f"plot_{select_id}"),
            ),
        ),
    )


@module.ui
def page_process_ui():
    return ui.nav_panel(
        "공정 설명",
        ui.page_fluid(
            ui.h3("공정 설명"),
            ui.p("공정 단계별 변수 사전과 원본 데이터 분포를 확인합니다."),

            ui.navset_tab(
                process_panel("① 용탕 준비 및 가열", "molten"),
                process_panel("② 반고체 슬러리 제조", "slurry"),
                process_panel("③ 사출 & 금형 충전", "inject"),
                process_panel("④ 응고 · 냉각", "solid"),
                process_panel("⑤ 기타", "etc"),
                id="process_nav",
            ),
        ),
    )


@module.server
def page_process_server(input, output, session):

    @render.data_frame
    def dict_molten():
        df = build_dict_df("① 용탕 준비 및 가열")
        return render.DataGrid(df, width="100%", height=260, summary=False, filters=False, selection_mode="none")

    @render_widget
    def plot_molten():
        return plot_distribution_plotly(df_raw, input.molten())

    @render.data_frame
    def dict_slurry():
        df = build_dict_df("② 반고체 슬러리 제조")
        return render.DataGrid(df, width="100%", height=260, summary=False, filters=False, selection_mode="none")

    @render_widget
    def plot_slurry():
        return plot_distribution_plotly(df_raw, input.slurry())

    @render.data_frame
    def dict_inject():
        df = build_dict_df("③ 사출 & 금형 충전")
        return render.DataGrid(df, width="100%", height=260, summary=False, filters=False, selection_mode="none")

    @render_widget
    def plot_inject():
        return plot_distribution_plotly(df_raw, input.inject())

    @render.data_frame
    def dict_solid():
        df = build_dict_df("④ 응고 · 냉각")
        return render.DataGrid(df, width="100%", height=260, summary=False, filters=False, selection_mode="none")

    @render_widget
    def plot_solid():
        return plot_distribution_plotly(df_raw, input.solid())

    @render.data_frame
    def dict_etc():
        df = build_dict_df("⑤ 기타")
        return render.DataGrid(df, width="100%", height=260, summary=False, filters=False, selection_mode="none")

    @render_widget
    def plot_etc():
        return plot_distribution_plotly(df_raw, input.etc())
