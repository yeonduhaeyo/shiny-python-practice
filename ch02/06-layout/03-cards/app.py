from shiny import App, ui, render
import pandas as pd
import matplotlib.pyplot as plt

df = pd.DataFrame({"월": ["1월", "2월", "3월", "4월"], "매출": [120, 150, 90, 180]})

app_ui = ui.page_fluid(
    ui.h2("예제 3 - 상단 KPI(Value Box) + 하단 분석 카드"),

    # 입력(필터)
    ui.card(
        ui.h4("필터"),
        ui.input_slider("x", "스케일", min=1, max=5, value=3),
        ui.p("슬라이더 값에 따라 KPI가 갱신됩니다."),
    ),

    ui.hr(),

    # (1) 상단 KPI 영역
    ui.h3("KPI 요약(상단)"),

    ui.layout_column_wrap(
        # A) 값만 갱신: value_box UI는 고정, 값 자리만 output_text
        ui.value_box(
            "A. 값만 갱신",
            ui.output_text("kpi_text"),  # 값 텍스트만 갱신
            "박스는 고정, 값만 바뀝니다.",
        ),

        # B) 박스 전체 갱신: output_ui 자리 + render.ui에서 value_box 생성
        ui.output_ui("kpi_box"),        # 박스 자체가 갱신됨

        width="300px",
        gap="1rem",
    ),

    ui.hr(),

    # (2) 하단 분석 영역
    ui.h3("분석 영역(하단)"),

    ui.card(
        ui.h4("분석 카드: 요약 문장"),
        ui.output_text("summary_text"),
    ),

)

def server(input, output, session):

    # A) 값만 갱신 (render.text)
    @render.text
    def kpi_text():
        # KPI 값만 텍스트로 바뀌는 상황에 가장 단순한 방식입니다.
        return f"{input.x() * 1000:,}"

    # B) 박스 전체 갱신 (render.ui)
    @render.ui
    def kpi_box():
        x = input.x()
        theme = "success" if x >= 4 else "primary"
        desc = "x ≥ 4이면 테마가 바뀝니다." if x >= 4 else "기본 테마로 표시합니다."

        return ui.value_box(
            "B. 박스 전체 갱신",
            f"{x * 1000:,}",
            desc,
            theme=theme,  # UI 속성(테마)까지 바꿔야 할 때 render.ui가 필요합니다.
        )

    # 하단 카드 출력
    @render.text
    def summary_text():
        return f"현재 스케일은 {input.x()} 입니다. KPI와 그래프는 이 값에 반응합니다."

app = App(app_ui, server)
