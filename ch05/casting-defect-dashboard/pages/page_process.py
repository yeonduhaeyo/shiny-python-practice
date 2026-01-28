from shiny import ui, module

@module.ui
def page_process_ui():
    return ui.nav_panel(
        "공정 설명",
        ui.h3("공정 설명"),
        ui.p("공정 단계별 변수 사전(공정 맵)을 제공합니다(이후 레슨에서 구현)."),
    )

@module.server
def page_process_server(input, output, session):
    # 이후 레슨에서 공정별 변수 테이블/검색/필터 구현
    pass
