from shiny import ui, module, render
from shared import df

@module.ui
def page_data_ui():
    return ui.nav_panel(
        "데이터 요약",
        ui.h3("데이터 요약"),
        ui.card(
            ui.card_header("정제 데이터 미리보기 (head)"),
            ui.output_data_frame("head_tbl"),
        ),
    )

@module.server
def page_data_server(input, output, session):
    @render.data_frame
    def head_tbl():
        return df.head(20)
