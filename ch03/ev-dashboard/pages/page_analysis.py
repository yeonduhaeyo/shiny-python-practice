from shiny import ui, module

@module.ui
def page_analysis_ui():
    return ui.nav_panel(
        "조건별 분석",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("조건 선택"),
                ui.p("용도/차종/지역 입력 위젯이 들어갈 예정입니다."),
                title="입력",
            ),
            ui.h3("조건별 분석"),
            ui.layout_columns(
                ui.card(
                    ui.card_header("KPI 영역"),
                    ui.p("합계/비중 등 핵심 숫자 출력 위치"),
                ),
                ui.card(
                    ui.card_header("그래프 영역"),
                    ui.p("Plotly 그래프 출력 위치"),
                ),
                col_widths=(6, 6),
            ),
            ui.card(
                ui.card_header("테이블 영역(3-8에서 구현)"),
                ui.p("DataGrid 출력 위치"),
            ),
        ),
    )

@module.server
def page_analysis_server(input, output, session):
    pass