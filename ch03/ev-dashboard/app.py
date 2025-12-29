# app.py
from shiny import App, ui
from pages import page_data, page_viz, page_analysis

app_ui = ui.page_navbar(
    page_data.page_data_ui("data"),
    page_viz.page_viz_ui("viz"),
    page_analysis.page_analysis_ui("analysis"),
    title="전기차 등록대수 대시보드",
)

def server(input, output, session):
    # 각 페이지(탭) 서버 연결
    page_data.page_data_server("data")
    page_viz.page_viz_server("viz")
    page_analysis.page_analysis_server("analysis")

app = App(app_ui, server)