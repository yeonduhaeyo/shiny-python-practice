from shiny import ui, module

@module.ui
def page_geopandas_ui():
    return ui.nav_panel(
        "GeoPandas",
        ui.h3("GeoPandas"),
        ui.p("정적 Choropleth 지도를 구현합니다."),
    )

@module.server
def page_geopandas_server(input, output, session):
    pass