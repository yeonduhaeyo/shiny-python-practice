from shiny.express import ui, input, render

ui.h2("Express 스타일 예제")
ui.input_text("name", "이름을 입력하세요")

@render.text
def greeting():
    return f"안녕하세요, {input.name()} 님!"