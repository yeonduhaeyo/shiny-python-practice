from shiny import App, ui, render

app_ui = ui.page_fluid(
    ui.h2("예제 1 - 내부 탭(navset_tab)"),

    # (A) 현재 선택된 탭을 바로 보여주는 출력(확인용)
    ui.p("현재 선택된 탭:"),
    ui.output_text("active_tab"),

    ui.hr(),

    # (B) 내부 탭 컨테이너
    ui.navset_tab(
        # 각 nav_panel이 탭 1개(섹션 1개)를 의미합니다.
        ui.nav_panel(
            "요약",
            ui.h3("요약 탭"),
            ui.p("핵심 KPI 요약/공지사항 등 '한눈에 보는 영역'을 둡니다."),
        ),
        ui.nav_panel(
            "상세 분석",
            ui.h3("상세 분석 탭"),
            ui.p("그래프/테이블을 배치하여 분석 내용을 보여줍니다."),
        ),
        ui.nav_panel(
            "원본 데이터",
            ui.h3("원본 데이터 탭"),
            ui.p("데이터 설명/컬럼 정의/샘플 등을 정리합니다."),
        ),
        # id: 서버에서 현재 탭 선택 상태를 input.tabset_main()으로 읽기 위해 사용
        id="tabset_main",
    ),
)

def server(input, output, session):
    # input.tabset_main(): 현재 선택된 탭(제목 또는 value)을 반환합니다.
    @render.text
    def active_tab():
        return str(input.tabset_main())

app = App(app_ui, server)