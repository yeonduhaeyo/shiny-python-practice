from shiny import App, ui, render

# 1) UI 정의
app_ui = ui.page_fluid(
    ui.h2("Core 스타일 예제"),
    ui.input_text("name", "이름을 입력하세요"),
    ui.output_text("greeting"),
)

# 2) 서버 로직 정의
def server(input, output, session):
    
    @render.text
    def greeting():
        return f"안녕하세요, {input.name()} 님!"

# 3) 앱 객체 생성
app = App(app_ui, server)