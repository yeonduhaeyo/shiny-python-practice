from shiny import App, ui
from pages import page_geopandas, page_plotly, page_folium, page_kakao

app_ui = ui.page_navbar(
    page_geopandas.page_geopandas_ui("geopandas"),
    page_plotly.page_plotly_ui("plotly"),
    page_folium.page_folium_ui("folium"),
    page_kakao.page_kakao_ui("kakao"),
    title="어린이집 지도 대시보드",
)

def server(input, output, session):
    page_geopandas.page_geopandas_server("geopandas")
    page_plotly.page_plotly_server("plotly")
    page_folium.page_folium_server("folium")
    page_kakao.page_kakao_server("kakao")

app = App(app_ui, server)