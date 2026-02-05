from shiny import App, ui
from pages import page_predict, page_process, page_appendix

import shinyswatch

from shared import app_dir

app_ui = ui.page_navbar(
    ui.head_content(ui.include_css(app_dir / "www" / "style.css")),

    page_predict.page_predict_ui("predict"),
    page_process.page_process_ui("process"),
    page_appendix.page_appendix_ui("appendix"),
    title="주조공정 불량 예측 대시보드",
    theme=shinyswatch.theme.flatly,
)

def server(input, output, session):
    page_predict.page_predict_server("predict")
    page_process.page_process_server("process")
    page_appendix.page_appendix_server("appendix")

app = App(app_ui, server)
