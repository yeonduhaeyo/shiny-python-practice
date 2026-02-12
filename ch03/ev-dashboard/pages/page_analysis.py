from datetime import date

from shiny import ui, module, reactive, render
from shared import df

import plotly.express as px
from shinywidgets import output_widget, render_widget

TYPE_COLS = ["승용", "승합", "화물", "특수"]


def _choices(col: str):
    return sorted(df[col].dropna().unique().tolist())


@module.ui
def page_analysis_ui():
    return ui.nav_panel(
        "조건별 분석",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_selectize("sido", "시도", choices=["전체"]),
                ui.input_selectize("sigungu", "시군구", choices=["전체"]),
                ui.input_selectize("purpose", "용도별", choices=["전체"]),
                ui.hr(),
                ui.input_checkbox_group(
                    "vtypes",
                    "차량유형(합계에 포함)",
                    choices=TYPE_COLS,
                    selected=TYPE_COLS,
                    inline=True,
                ),
                ui.input_action_button("apply", "조건 적용", class_="btn-primary", width="100%"),

                ui.download_button(
                    "download_csv",
                    "CSV 다운로드",
                    class_="btn-outline-secondary",
                    width="100%",
                ),

                title="입력",
            ),
            ui.layout_columns(
                ui.card(
                    ui.layout_columns(
                        ui.value_box("필터 후 행 수", ui.output_text("kpi_rows")),
                        ui.value_box("선택합 총합", ui.output_text("kpi_sum_selected")),
                        col_widths=(6, 6),
                    ),
                ),
                ui.card(
                    # (3-8) 1) 그래프 영역에 Plotly 출력 연결
                    output_widget("p_type_bar", height="420px"),
                ),
                col_widths=(6, 6),
            ),
            ui.card(
                # (3-8) 2) 테이블 영역에 DataGrid 출력 연결
                ui.output_data_frame("tbl_filtered"),
            ),
        ),
    )


@module.server
def page_analysis_server(input, output, session):

    @reactive.effect
    def _init_choices():
        ui.update_selectize(
            "sido",
            choices=["전체"] + _choices("시도"),
            selected="전체",
            session=session,
        )
        ui.update_selectize(
            "purpose",
            choices=["전체"] + _choices("용도별"),
            selected="전체",
            session=session,
        )

    @reactive.effect
    def _sync_sigungu_choices():
        sido = input.sido()

        if (sido is None) or (sido == "전체"):
            sigungu_choices = ["전체"] + _choices("시군구")
        else:
            sigungu_choices = ["전체"] + sorted(
                df.loc[df["시도"] == sido, "시군구"].dropna().unique().tolist()
            )

        ui.update_selectize(
            "sigungu",
            choices=sigungu_choices,
            selected="전체",
            session=session,
        )

    @reactive.calc
    @reactive.event(input.apply, ignore_none=False)
    def filtered_df():
        with reactive.isolate():
            sido = input.sido()
            sigungu = input.sigungu()
            purpose = input.purpose()
            selected = list(input.vtypes() or TYPE_COLS)

        dat = df

        if sido and sido != "전체":
            dat = dat[dat["시도"] == sido]

        if sigungu and sigungu != "전체":
            dat = dat[dat["시군구"] == sigungu]

        if purpose and purpose != "전체":
            dat = dat[dat["용도별"] == purpose]

        base_cols = ["시도", "시군구", "연료별", "용도별"]
        keep_cols = [c for c in base_cols if c in dat.columns]
        type_cols = [c for c in selected if c in dat.columns]

        dat = dat[keep_cols + type_cols].copy()
        dat["선택합"] = dat[type_cols].sum(axis=1) if type_cols else 0

        return dat.reset_index(drop=True)

    @render.text
    def kpi_rows():
        return f"{len(filtered_df()):,}"

    @render.text
    def kpi_sum_selected():
        return f"{filtered_df()['선택합'].sum():,}"

    @render_widget
    def p_type_bar():
        dat = filtered_df()

        type_cols = [c for c in TYPE_COLS if c in dat.columns]
        totals = dat[type_cols].sum().reset_index()
        totals.columns = ["차량유형", "등록대수"]

        fig = px.bar(
            totals,
            x="차량유형",
            y="등록대수",
            color="차량유형",
            title="차량유형별 등록대수(선택 항목만)",
        )
        fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), showlegend=False)
        return fig

    @render.data_frame
    def tbl_filtered():
        return render.DataGrid(
            filtered_df(),
            width="100%",
            height="420px",
            filters=True,
        )

    @render.download(
        filename=lambda: f"filtered_{date.today().isoformat()}.csv",
        encoding="utf-8-sig",
    )
    def download_csv():
        yield filtered_df().to_csv(index=False)