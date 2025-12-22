from shiny import App, ui, render
import pandas as pd
import matplotlib.pyplot as plt

# 그래프 한글 폰트 설정
plt.rcParams["font.family"] = "Malgun Gothic"  # 환경에 맞게 수정 가능
plt.rcParams["axes.unicode_minus"] = False

# 간단한 예제 데이터(설명용)
df = pd.DataFrame(
    {"월": ["1월", "2월", "3월", "4월"], "매출": [120, 150, 90, 180]}
)

app_ui = ui.page_fluid(
    ui.h2("예제 2 - 컬럼/그리드 배치"),

    ui.h3("1) layout_columns: 그래프(왼쪽) + 테이블(오른쪽)"),

    # layout_columns: 한 행을 12칸으로 보고, col_widths로 비율을 정합니다.
    ui.layout_columns(
        ui.card(
            ui.h4("왼쪽: 그래프"),
            # output_plot은 '출력 자리'만 잡아두는 역할
            ui.output_plot("sales_plot"),
        ),
        ui.card(
            ui.h4("오른쪽: 테이블"),
            ui.output_data_frame("sales_table"),
        ),
        # (8,4) = 왼쪽 8칸, 오른쪽 4칸 비율
        col_widths=(8, 4),
        gap="1rem",
    ),

    ui.hr(),

    ui.h3("2) layout_column_wrap: 카드 타일(자동 줄바꿈)"),

    # layout_column_wrap: width 기준으로 카드가 자동 줄바꿈됩니다.
    ui.layout_column_wrap(
        ui.card(ui.h4("요약 1"), ui.p("짧은 설명")),
        ui.card(ui.h4("요약 2"), ui.p("짧은 설명")),
        ui.card(ui.h4("요약 3"), ui.p("짧은 설명")),
        ui.card(ui.h4("요약 4"), ui.p("짧은 설명")),
        # width="240px": 각 카드의 최소 폭(화면이 좁으면 줄바꿈)
        width="240px",
        gap="1rem",
    ),
)

def server(input, output, session):
    # 왼쪽 그래프: output_plot("sales_plot")에 대응하는 렌더러
    @render.plot(alt="월별 매출 그래프")
    def sales_plot():
        fig, ax = plt.subplots()
        ax.bar(df["월"], df["매출"])
        ax.set_title("월별 매출(예시)")
        ax.set_ylabel("매출")
        return fig

    # 오른쪽 테이블: output_data_frame("sales_table")에 대응하는 렌더러
    @render.data_frame
    def sales_table():
        # DataTable은 data_frame 출력의 옵션(높이/필터/요약 등)을 제어합니다.
        return render.DataTable(
            df,
            width="100%",
            height="220px",
            filters=False,
            summary=True,
            selection_mode="none",
        )

app = App(app_ui, server)
