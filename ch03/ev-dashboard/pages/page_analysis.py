from shiny import ui, module, reactive, render
from shared import df

# 1-1) 차량유형 리스트 정의
TYPE_COLS = ["승용", "승합", "화물", "특수"]

# 2-1) 선택지 유틸 함수
def _choices(col: str):
    return sorted(df[col].dropna().unique().tolist())


@module.ui
def page_analysis_ui():
    return ui.nav_panel(
        "조건별 분석",
        ui.layout_sidebar(

            # 1-2) 사이드바 입력 컴포넌트 추가
            ui.sidebar(
                ui.h4("조건 선택"),

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

                title="입력",
            ),

            ui.h3("조건별 분석"),

            ui.layout_columns(
                ui.card(
                    ui.card_header("KPI 영역"),

                    # 4) KPI value_box 출력 자리 추가
                    ui.layout_columns(
                        ui.value_box(
                            title="필터 후 행 수",
                            value=ui.output_text("kpi_rows"),
                        ),
                        ui.value_box(
                            title="선택합 총합",
                            value=ui.output_text("kpi_sum_selected"),
                        ),
                        col_widths=(6, 6),
                    ),
                ),
                ui.card(
                    ui.card_header("그래프 영역"),
                    ui.p("Plotly 그래프 출력 위치"),
                ),
                col_widths=(6, 6),
            ),
            ui.card(
                ui.card_header("테이블 영역"),
                ui.p("DataGrid 출력 위치"),
            ),
        ),
    )


@module.server
def page_analysis_server(input, output, session):

    # 2-1) 선택지 초기화(시도, 용도별)
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

    # 2-2) 시도 선택 시 시군구 선택지 갱신(종속)
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

    # 3) filtered_df() 구현(초기값 포함 + 버튼 클릭 시 갱신)
    @reactive.calc
    @reactive.event(input.apply, ignore_none=False)
    def filtered_df():
        dat = df

        if input.sido() and input.sido() != "전체":
            dat = dat[dat["시도"] == input.sido()]

        if input.sigungu() and input.sigungu() != "전체":
            dat = dat[dat["시군구"] == input.sigungu()]

        if input.purpose() and input.purpose() != "전체":
            dat = dat[dat["용도별"] == input.purpose()]

        selected = list(input.vtypes() or TYPE_COLS)

        dat = dat.copy()
        dat["선택합"] = dat[selected].sum(axis=1)

        return dat.reset_index(drop=True)

    # 4) 검증용 KPI 출력
    @output
    @render.text
    def kpi_rows():
        return f"{len(filtered_df()):,}"

    @output
    @render.text
    def kpi_sum_selected():
        return f"{filtered_df()['선택합'].sum():,}"
