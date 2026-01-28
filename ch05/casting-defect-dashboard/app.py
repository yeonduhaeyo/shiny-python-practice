from shiny import App, ui
from pages import page_predict, page_process, page_appendix

app_ui = ui.page_navbar(
    page_predict.page_predict_ui("predict"),
    page_process.page_process_ui("process"),
    page_appendix.page_appendix_ui("appendix"),
    title="주조공정 불량 예측 대시보드",
)

def server(input, output, session):
    page_predict.page_predict_server("predict")
    page_process.page_process_server("process")
    page_appendix.page_appendix_server("appendix")

app = App(app_ui, server)
