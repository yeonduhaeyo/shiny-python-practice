from shiny import App, ui, render

# 1) UI 정의
app_ui = ui.page_fluid(
    ui.h2("입력 컴포넌트 기초 - 미니 설문"),

    # 텍스트 입력
    ui.input_text("name", "이름을 입력하세요", placeholder="홍길동"),

    # 숫자 입력
    ui.input_numeric("age", "나이", value=25, min=0, max=120),

    # 라디오 버튼
    ui.input_radio_buttons(
        "level",
        "파이썬 경험 수준",
        choices=["입문", "중급", "고급"],
        selected="입문",
    ),

    # 체크박스
    ui.input_checkbox(
        "recommend",
        "이 강의를 다른 사람에게 추천하겠다",
        value=True,
    ),

    # 셀렉트 박스
    ui.input_select(
        "topic",
        "가장 관심 있는 주제",
        choices=["데이터 분석", "지도 시각화", "머신러닝 예측"],
        selected="데이터 분석",
    ),

    # 슬라이더
    ui.input_slider(
        "score",
        "강의 기대 점수 (1~10)",
        min=1,
        max=10,
        value=7,
    ),

    # 날짜 입력
    ui.input_date(
        "date",
        "수강 날짜",
        value="2025-01-01",
        min="2024-01-01",
        max="2025-12-31",
    ),

    ui.hr(),
    ui.h4("입력 요약"),
    ui.output_text_verbatim("summary"),
)

# 2) 서버 로직
def server(input, output, session):

    @render.text
    def summary():
        name = input.name() or "(이름 미입력)"
        age = input.age() if input.age() is not None else "(나이 미입력)"
        level = input.level()
        recommend = "예" if input.recommend() else "아니오"
        topic = input.topic()
        score = input.score()
        date = input.date() or "(날짜 미선택)"

        return (
            f"이름: {name}\n"
            f"나이: {age}\n"
            f"파이썬 경험 수준: {level}\n"
            f"추천 의향: {recommend}\n"
            f"관심 주제: {topic}\n"
            f"강의 기대 점수: {score}\n"
            f"수강 날짜: {date}"
        )

# 3) 앱 객체
app = App(app_ui, server)
