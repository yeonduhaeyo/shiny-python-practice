from shiny import App, ui

app_ui = ui.page_navbar(
    ui.nav_panel(
        "대시보드",
        ui.h2("대시보드 메인"),
        ui.p("여기에 주요 지표 / 그래프가 올 예정입니다."),
    ),
    ui.nav_panel(
        "리포트",
        ui.h2("리포트 페이지"),
        ui.p("월간/주간 리포트 내용을 배치할 수 있습니다."),
    ),
    ui.nav_panel(
        "도움말",
        ui.h2("도움말"),
        ui.p("앱 사용 방법 및 설명을 정리합니다."),
    ),
    title="레이아웃 기초 - page_navbar 예제",
)

def server(input, output, session):
    pass

app = App(app_ui, server)
