# 1. Plotly 탭 모듈 파일 생성 (모듈 기본 구조 + import)
import json
import pandas as pd

from shiny import ui, module, reactive
from shinywidgets import output_widget, render_widget

import plotly.express as px
import plotly.graph_objects as go

from shared import df, gdf_sigungu


# 2. 공통 설정 (폰트/팔레트)
FONT_FAMILY = "Malgun Gothic, AppleGothic, sans-serif"
CORAL_SCALE = ["#FFF1EC", "#FFD9CC", "#FFC1AD", "#FFA07E", "#F27D67"]


# 4. 마커 지도 생성: px.scatter_map
def make_marker_map(points_df: pd.DataFrame):
    # 4-1. 유형 -> size로 단순 표현(symbol 대체)
    types = points_df["어린이집유형구분"].dropna().astype(str).unique().tolist()
    size_steps = [9, 11, 13, 15]
    type_to_size = {t: size_steps[i % len(size_steps)] for i, t in enumerate(sorted(types))}

    tmp = points_df.copy()
    tmp["유형크기"] = tmp["어린이집유형구분"].map(type_to_size)

    # 4-2. 마커 지도 생성
    fig = px.scatter_map(
        tmp,
        lat="위도",
        lon="경도",
        color="운영현황",
        size="유형크기",
        size_max=18,
        hover_name="어린이집명",
        hover_data={
            "시군구": True,
            "어린이집유형구분": True,
            "운영현황": True,
            "위도": False,
            "경도": False,
        },
        zoom=10,
        height=720,
    )

    # 4-3. 스타일/폰트
    fig.update_layout(
        map_style="open-street-map",
        margin=dict(l=0, r=0, t=40, b=0),
        legend_title_text="운영현황",
        font=dict(family=FONT_FAMILY),
    )

    # 4-4. 데이터 중심으로 센터 이동
    if len(tmp) > 0:
        fig.update_layout(
            map_center=dict(lat=float(tmp["위도"].mean()), lon=float(tmp["경도"].mean()))
        )

    return fig


# 5. (선택) choropleth 생성: px.choropleth_map
def make_choropleth(filtered_df: pd.DataFrame):
    # 5-1. 구별 집계 + 컬럼명 매칭(시군구 -> SIGUNGU_NM)
    counts = (
        filtered_df.groupby("시군구")
        .size()
        .rename("어린이집수")
        .reset_index()
        .rename(columns={"시군구": "SIGUNGU_NM"})
    )

    geojson = json.loads(gdf_sigungu.to_json())

    # 5-2. choropleth 생성
    fig = px.choropleth_map(
        counts,
        geojson=geojson,
        locations="SIGUNGU_NM",
        featureidkey="properties.SIGUNGU_NM",
        color="어린이집수",
        color_continuous_scale=CORAL_SCALE,
        opacity=0.85,
        zoom=10,
        height=720,
    )

    fig.update_layout(
        map_style="open-street-map",
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(title="어린이집수"),
        font=dict(family=FONT_FAMILY),
    )

    # 5-3. 경계 중앙으로 센터 고정
    minx, miny, maxx, maxy = gdf_sigungu.total_bounds
    fig.update_layout(map_center=dict(lat=(miny + maxy) / 2, lon=(minx + maxx) / 2))

    return fig


# 2. UI: 사이드바 입력 + 출력(output_widget) 배치
@module.ui
def page_plotly_ui():
    # 2-1. 선택지 준비
    gu_choices = ["전체"] + sorted(df["시군구"].dropna().astype(str).str.strip().unique().tolist())
    type_choices = ["전체"] + sorted(df["어린이집유형구분"].dropna().astype(str).str.strip().unique().tolist())
    status_choices = sorted(df["운영현황"].dropna().astype(str).str.strip().unique().tolist())

    # 2-2. UI 배치
    return ui.nav_panel(
        "Plotly",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_selectize("gu", "구 선택", choices=gu_choices, selected="전체"),
                ui.input_selectize("ctype", "유형", choices=type_choices, selected="전체"),
                ui.input_checkbox_group("status", "운영현황", choices=status_choices, selected=status_choices),
                ui.hr(),
                ui.input_radio_buttons(
                    "mode",
                    "지도 모드",
                    choices=["마커 지도", "시군구 Choropleth(선택)"],
                    selected="마커 지도",
                ),
                width=320,
            ),
            ui.card(
                ui.card_header("Plotly 지도"),
                # 6. Shiny 출력 슬롯
                output_widget("map"),
                full_screen=True,
            ),
        ),
    )


# 3~6. Server: 필터(reactive) + figure 생성 + Shiny 렌더링
@module.server
def page_plotly_server(input, output, session):

    # 3. 필터 데이터 계산(reactive)
    @reactive.calc
    def df_filtered() -> pd.DataFrame:
        out = df.copy()

        for col in ["시군구", "어린이집유형구분", "운영현황"]:
            out[col] = out[col].astype(str).str.strip()

        sel_status = list(input.status() or [])
        if sel_status:
            out = out[out["운영현황"].isin(sel_status)]

        if (input.gu() or "전체") != "전체":
            out = out[out["시군구"] == input.gu().strip()]

        if (input.ctype() or "전체") != "전체":
            out = out[out["어린이집유형구분"] == input.ctype().strip()]

        return out

    @reactive.calc
    def df_points() -> pd.DataFrame:
        out = df_filtered().copy()
        out["위도"] = pd.to_numeric(out["위도"], errors="coerce")
        out["경도"] = pd.to_numeric(out["경도"], errors="coerce")
        out = out.dropna(subset=["위도", "경도"])
        return out

    # 6. Shiny 출력: output_widget + @render_widget
    @render_widget
    def map():
        mode = (input.mode() or "마커 지도").strip()

        if mode == "마커 지도":
            fig = make_marker_map(df_points())
        else:
            fig = make_choropleth(df_filtered())

        return go.FigureWidget(fig)
