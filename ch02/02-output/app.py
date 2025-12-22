import pandas as pd
import matplotlib.pyplot as plt

from shiny import App, ui, render

# (선택) 그래프 한글 폰트 설정
plt.rcParams["font.family"] = "Malgun Gothic"  # 환경에 맞게 수정 가능
plt.rcParams["axes.unicode_minus"] = False

# 예제 데이터
courses_df = pd.DataFrame(
    {
        "레슨": ["2-1 입력 기초", "2-2 출력 기초", "2-3 리액티브 기초"],
        "진도율(%)": [100, 50, 0],
        "난이도": ["하", "하", "중"],
    }
)

# 1) UI 정의
app_ui = ui.page_fluid(
    ui.h2("출력 컴포넌트 기초"),

    # 1. 텍스트 출력
    ui.h3("한 줄 텍스트 출력"),
    ui.output_text("hello_text"),

    ui.br(),
    ui.h3("여러 줄 텍스트 출력"),
    ui.output_text_verbatim("multi_line_text"),

    # 2. 데이터프레임 출력
    ui.br(),
    ui.h3("DataGrid로 데이터프레임 출력"),
    ui.output_data_frame("lesson_grid"),

    ui.br(),
    ui.h3("DataTable로 데이터프레임 출력"),
    ui.output_data_frame("lesson_table"),

    # 3. 그래프 출력
    ui.br(),
    ui.h3("matplotlib 그래프 출력"),
    ui.output_plot("progress_plot"),
)

# 2) 서버 로직
def server(input, output, session):
    # 한 줄 텍스트 출력
    @render.text
    def hello_text():
        return "안녕하세요, Shiny 출력 컴포넌트 레슨입니다."

    # 여러 줄 텍스트 출력
    @render.text
    def multi_line_text():
        return (
            "이 영역은 output_text_verbatim으로 출력됩니다.\n"
            "줄바꿈과 공백이 유지되어 보입니다.\n"
            "로그, 요약 정보, 디버그 텍스트 등에 활용할 수 있습니다."
        )

    # DataGrid 스타일 데이터프레임 출력
    @render.data_frame
    def lesson_grid():
        return render.DataGrid(
            courses_df,
            filters=True,
            selection_mode="rows",
        )

    # DataTable 스타일 데이터프레임 출력
    @render.data_frame
    def lesson_table():
        return render.DataTable(
            courses_df,
            filters=False,
            selection_mode="none",
            height=None, # 출력 편의를 위해 추가 
        )

    # 그래프 출력
    @render.plot(alt="레슨별 진도율 막대 그래프")
    def progress_plot():
        fig, ax = plt.subplots()

        ax.bar(courses_df["레슨"], courses_df["진도율(%)"])
        ax.set_ylim(0, 100)
        ax.set_ylabel("진도율(%)")
        ax.set_title("레슨별 진도율(예시)")
        ax.tick_params(axis="x", rotation=15)
        ax.grid(axis="y", linestyle="--", alpha=0.3)

        return fig

# 3) 앱 객체
app = App(app_ui, server)