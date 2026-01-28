from shiny import ui, module

@module.ui
def page_predict_ui():
    return ui.nav_panel(
        "불량 예측",
        ui.h3("불량 예측"),
        ui.p("공정 조건을 입력하고 불량 확률을 예측합니다(이후 레슨에서 구현)."),
    )

@module.server
def page_predict_server(input, output, session):
    # 이후 레슨에서 예측 로직/출력 연결
    pass
