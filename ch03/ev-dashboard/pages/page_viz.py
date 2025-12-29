from shiny import ui, module

@module.ui
def page_viz_ui():
    return ui.nav_panel(
        "시각화",
        ui.h3("시각화"),
        ui.layout_columns(
            ui.card(
                ui.card_header("정적 그래프"),
                ui.p("Matplotlib·Seaborn 그래프 출력 위치"),
            ),
            ui.card(
                ui.card_header("동적 그래프"),
                ui.p("Plotly 그래프 출력 위치"),
            ),
            col_widths=(6, 6),
        ),
    )

@module.server
def page_viz_server(input, output, session):
    pass