from shiny import App, ui, render
import pandas as pd
import matplotlib.pyplot as plt

# 한글 폰트 설정 (환경에 맞게 변경 가능)
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# 예제 2: 할 일 데이터
todos_df = pd.DataFrame(
    {
        "업무": ["데이터 정리", "Shiny 강의 작성", "리포트 작성", "코드 리뷰"],
        "상태": ["진행중", "진행중", "대기", "완료"],
        "우선순위": ["높음", "보통", "낮음", "보통"],
    }
)

# 예제 3: 월별 방문자 데이터
visitors_df = pd.DataFrame(
    {
        "월": ["1월", "2월", "3월", "4월", "5월", "6월"],
        "방문자수": [120, 150, 180, 160, 200, 220],
    }
)

# 1) UI 정의
app_ui = ui.page_fluid(
    ui.h2("리액티브 기초"),

    # 예제 1
    ui.h3("예제 1. 오늘 공부 계획 문장"),

    ui.input_text(
        "topic",
        "오늘 공부할 주제",
        placeholder="예: Shiny, pandas, 머신러닝",
    ),

    ui.input_slider(
        "hours",
        "공부 시간 (시간)",
        min=1,
        max=8,
        value=2,
    ),

    ui.br(),
    ui.h4("공부 계획 요약"),
    ui.output_text("study_plan"),

    ui.hr(),

    # 예제 2
    ui.h3("예제 2. 할 일 목록 필터링"),

    ui.input_select(
        "status_filter",
        "상태 필터",
        choices=["전체", "대기", "진행중", "완료"],
        selected="전체",
    ),

    ui.input_checkbox(
        "only_high_priority",
        "우선순위 '높음'만 보기",
        value=False,
    ),

    ui.output_data_frame("todo_table"),

    ui.hr(),

    # 예제 3
    ui.h3("예제 3. 월별 방문자 수 (기간 선택)"),

    ui.input_radio_buttons(
        "period",
        "보고 싶은 기간",
        choices=["1~3월만 보기", "1~6월 전체 보기"],
        selected="1~6월 전체 보기",
        inline=True,
    ),

    ui.output_plot("visitors_plot"),
)


# 2) 서버 로직
def server(input, output, session):

    # 예제 1
    @render.text
    def study_plan():
        topic = input.topic() or "아직 정하지 않은 주제"
        hours = input.hours()
        return f"오늘은 '{topic}'를(을) {hours}시간 공부할 계획입니다."

    # 예제 2
    @render.data_frame
    def todo_table():
        status = input.status_filter()
        only_high = input.only_high_priority()

        df = todos_df.copy()

        if status != "전체":
            df = df[df["상태"] == status]

        if only_high:
            df = df[df["우선순위"] == "높음"]

        return render.DataTable(
            df,
            filters=False,
            selection_mode="none",
            summary=True,
            height=None,
        )

    # 예제 3
    @render.plot(alt="월별 방문자 수 (기간 선택)")
    def visitors_plot():
        period = input.period()

        if period == "1~3월만 보기":
            df = visitors_df.iloc[:3]
        else:
            df = visitors_df

        fig, ax = plt.subplots()
        ax.bar(df["월"], df["방문자수"])

        ax.set_ylabel("방문자 수")
        ax.set_title(f"{period}")
        ax.set_ylim(0, max(visitors_df["방문자수"]) + 20)
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        ax.tick_params(axis="x", rotation=15)

        return fig


# 3) 앱 객체
app = App(app_ui, server)
