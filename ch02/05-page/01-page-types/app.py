from shiny import App, ui

# 1) 모든 page_*에서 공통으로 사용할 콘텐츠
content = ui.TagList(
    ui.h2("페이지 컨테이너 비교 예제"),
    ui.p(
        "내부 UI는 그대로 두고, page_* 함수만 바꿔서 "
        "레이아웃 변화를 확인해 보겠습니다."
    ),
    ui.br(),
    ui.p("아래 두 카드의 폭과 배치가 브라우저 크기에 따라 어떻게 달라지는지 살펴보세요."),
    ui.layout_columns(
        ui.card(
            ui.h4("왼쪽 카드"),
            ui.p("여기에 그래프나 KPI가 올 수 있습니다."),
        ),
        ui.card(
            ui.h4("오른쪽 카드"),
            ui.p("여기에 테이블이나 설명 블록이 올 수 있습니다."),
        ),
    ),
)

# 2) 여기에서 page_* 만 바꿔가며 테스트
# (1) 기본: page_fluid
# app_ui = ui.page_fluid(content)

# (2) page_fixed 로 바꿔보기
# app_ui = ui.page_fixed(content)

# (3) page_fillable 로 바꿔보기
app_ui = ui.page_fillable(content)

def server(input, output, session):
    pass

app = App(app_ui, server)
