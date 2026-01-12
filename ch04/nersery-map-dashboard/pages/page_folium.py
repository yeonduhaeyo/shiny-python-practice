from shiny import ui, module

@module.ui
def page_folium_ui():
    return ui.nav_panel(
        "Folium",
        ui.h3("Folium"),
        ui.p("클러스터/팝업 지도를 구현합니다."),
    )

@module.server
def page_folium_server(input, output, session):
    pass