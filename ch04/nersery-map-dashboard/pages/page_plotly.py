from shiny import ui, module

@module.ui
def page_plotly_ui():
    return ui.nav_panel(
        "Plotly",
        ui.h3("Plotly"),
        ui.p("인터랙티브 마커/Choropleth 지도를 구현합니다."),
    )

@module.server
def page_plotly_server(input, output, session):
    pass