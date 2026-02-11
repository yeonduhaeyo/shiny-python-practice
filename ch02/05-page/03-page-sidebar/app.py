from shiny import App, ui, render

# page_sidebar: 앱 전체를 Sidebar(필터) + Main(결과)로 나누는 컨테이너
app_ui = ui.page_sidebar(
    # 1) Sidebar 영역
    ui.sidebar(
        ui.h4("필터"),
        ui.input_select(
            "category",
            "카테고리",
            choices=["전체", "A", "B", "C"],
            selected="전체",
        ),
    ),

    # 2) 메인 영역
    ui.card(
        ui.h3("메인 분석 영역"),
        ui.p("선택한 카테고리에 따라 아래 내용이 달라집니다."),
        ui.br(),
        ui.h4("카테고리별 설명"),
        ui.output_text("category_desc"),
    ),

    title="레이아웃 기초 – page_sidebar 예제",
)


def server(input, output, session):
    # Sidebar의 카테고리 선택에 따라 메인 카드 내용 변경
    @render.text
    def category_desc():
        category = input.category()

        if category == "전체":
            return "전체 데이터를 기준으로 요약 지표와 그래프를 보여줍니다."
        elif category == "A":
            return "카테고리 A에 해당하는 데이터만 필터링하여 분석합니다."
        elif category == "B":
            return "카테고리 B에 집중하여 추세와 이상치를 살펴봅니다."
        elif category == "C":
            return "카테고리 C에 특화된 지표와 상세 리포트를 제공합니다."
        else:
            return "카테고리를 선택해 주세요."


app = App(app_ui, server)
