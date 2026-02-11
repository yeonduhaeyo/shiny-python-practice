from shiny import App, ui, render

# 탭 1) 대시보드: 탭 내부에서만 Sidebar + Main 구조 적용(layout_sidebar)
dashboard_page = ui.nav_panel(
    "대시보드",
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4("필터"),
            ui.input_select(
                "category",
                "카테고리",
                choices=["전체", "A", "B", "C"],
                selected="전체",
            ),
        ),
        ui.card(
            ui.h3("대시보드 메인"),
            ui.p("대시보드 탭 전용 분석 영역입니다."),
            ui.br(),
            ui.h4("대시보드용 카테고리 설명"),
            ui.output_text("dashboard_category_desc"),
        ),
    ),
)

# 탭 2) 도움말: 기본 페이지(사이드바 없음)
help_page = ui.nav_panel(
    "도움말",
    ui.card(
        ui.h2("도움말"),
        ui.p("각 탭과 Sidebar 필터의 역할을 설명하는 공간입니다."),
    ),
)

# 전체 앱: page_navbar로 상위 탭(페이지) 구성
app_ui = ui.page_navbar(
    dashboard_page,
    help_page,
    title="레이아웃 기초 - layout_sidebar in page_navbar",
)

# 서버 로직
def server(input, output, session):
    # 대시보드 탭: Sidebar 선택에 따라 설명 텍스트 변경
    @render.text
    def dashboard_category_desc():
        category = input.category()

        if category == "전체":
            return "전체 데이터를 기준으로 대시보드 지표를 요약해서 보여줍니다."
        elif category == "A":
            return "카테고리 A 관련 핵심 지표와 그래프에 초점을 맞춥니다."
        elif category == "B":
            return "카테고리 B에 대한 추세 분석과 이상치 모니터링에 집중합니다."
        elif category == "C":
            return "카테고리 C 전용 상세 지표와 리포트 화면을 강조합니다."
        else:
            return "카테고리를 선택해 주세요."


app = App(app_ui, server)