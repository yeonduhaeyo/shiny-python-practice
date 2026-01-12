from shiny import ui, module

@module.ui
def page_kakao_ui():
    return ui.nav_panel(
        "Kakao",
        ui.h3("Kakao"),
        ui.p("Kakao 지도 API 연동을 구현합니다."),
    )

@module.server
def page_kakao_server(input, output, session):
    pass