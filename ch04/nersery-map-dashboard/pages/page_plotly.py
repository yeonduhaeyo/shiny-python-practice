# 1. Plotly 탭 파일 확인 (모듈 기본 구조 + import)
import json
import pandas as pd

from shiny import ui, module, reactive
from shinywidgets import output_widget, render_widget

import plotly.express as px
import plotly.graph_objects as go

from shared import df, gdf_sigungu


# 2. Choropleth 연속 팔레트(코랄)
CORAL_SCALE = ["#FFF1EC", "#FFD9CC", "#FFC1AD", "#FFA07E", "#F27D67"]


# 4. 마커 지도 생성 : px.scatter_map
def make_marker_map(points_df: pd.DataFrame):
    # 4-1. 마커 지도 figure 생성
    fig = px.scatter_map(
        points_df,
        lat="위도",
        lon="경도",
        color="운영현황",  # 운영현황만 색으로 구분
        hover_name="어린이집명",
        hover_data={
            "시군구": True,
            "어린이집유형구분": True,  # 유형은 sidebar에서 필터, 지도에선 hover로 확인
            "운영현황": True,
            "위도": False,
            "경도": False,
        },
        zoom=10,
        height=720,
    )

    # 4-2. 마커 크기 키우기
    fig.update_traces(marker=dict(size=14))

    # 4-3. 토큰 없이 동작하는 타일 스타일(실습 안정성 우선)
    fig.update_layout(
        map_style="open-street-map",
        margin=dict(l=0, r=0, t=40, b=0),
        legend_title_text="운영현황",
        title="시설 단위 마커 지도",
    )

    # 4-4. 선택된 데이터 중심으로 화면 센터 이동(구 선택 시 자연스럽게 따라감)
    if len(points_df) > 0:
        fig.update_layout(
            map_center=dict(
                lat=float(points_df["위도"].mean()),
                lon=float(points_df["경도"].mean()),
            )
        )

    return fig


# 5. Choropleth 생성 : px.choropleth_map
def make_choropleth(filtered_df: pd.DataFrame, gdf_sigungu):
    # 5-1. 구별 집계 + 컬럼명 매칭(시군구 -> SIGUNGU_NM)
    counts = (
        filtered_df.groupby("시군구")
        .size()
        .rename("어린이집수")
        .reset_index()
        .rename(columns={"시군구": "SIGUNGU_NM"})
    )

    geojson = json.loads(gdf_sigungu.to_json())

    # 5-2. Choropleth figure 생성
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
        title="시군구 Choropleth",
    )

    # 5-3. 경계 중앙으로 센터 고정(전체 보기)
    minx, miny, maxx, maxy = gdf_sigungu.total_bounds
    fig.update_layout(map_center=dict(lat=(miny + maxy) / 2, lon=(minx + maxx) / 2))

    return fig


# 2. UI 컴포넌트 배치 : 사이드바 입력 + 출력(output_widget) 배치
@module.ui
def page_plotly_ui():
    # 2-1. 선택지 준비(공백/결측 정리)
    gu_choices = ["전체"] + sorted(
        df["시군구"].dropna().astype(str).str.strip().unique().tolist()
    )
    type_choices = ["전체"] + sorted(
        df["어린이집유형구분"].dropna().astype(str).str.strip().unique().tolist()
    )
    status_choices = sorted(
        df["운영현황"].dropna().astype(str).str.strip().unique().tolist()
    )

    # 2-2. UI 배치(입력 + 출력 슬롯)
    return ui.nav_panel(
        "Plotly",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_selectize("gu", "구 선택", choices=gu_choices, selected="전체"),
                ui.input_selectize("ctype", "유형", choices=type_choices, selected="전체"),
                ui.input_checkbox_group(
                    "status", "운영현황", choices=status_choices, selected=status_choices
                ),
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


# 3~6. Server : 필터(reactive) + figure 생성 + Shiny 렌더링
@module.server
def page_plotly_server(input, output, session):

    # 3-1. df_filtered() : 필터만 적용(choropleth 집계용)
    @reactive.calc
    def df_filtered() -> pd.DataFrame:
        out = df.copy()

        # (1) 문자열 정리: 공백/형 변환(필터 매칭 안정화)
        for col in ["시군구", "어린이집유형구분", "운영현황"]:
            out[col] = out[col].astype(str).str.strip()

        # (2) 운영현황: 체크된 항목만 남김
        sel_status = list(input.status() or [])
        if sel_status:
            out = out[out["운영현황"].isin(sel_status)]

        # (3) 구: "전체"면 필터 미적용
        gu = (input.gu() or "전체").strip()
        if gu != "전체":
            out = out[out["시군구"] == gu]

        # (4) 유형: "전체"면 필터 미적용
        ctype = (input.ctype() or "전체").strip()
        if ctype != "전체":
            out = out[out["어린이집유형구분"] == ctype]

        return out

    # 3-2. df_points() : 마커 지도용(좌표 숫자 변환 + 결측 제거)
    @reactive.calc
    def df_points() -> pd.DataFrame:
        out = df_filtered().copy()

        # 좌표를 숫자로 변환: 문자열/이상치가 있으면 NaN 처리
        out["위도"] = pd.to_numeric(out["위도"], errors="coerce")
        out["경도"] = pd.to_numeric(out["경도"], errors="coerce")

        # 지도 표시 불가한 행 제거
        out = out.dropna(subset=["위도", "경도"])

        return out

    # 6. Shiny 출력: output_widget + @render_widget (모드 전환)
    @render_widget
    def map():
        mode = (input.mode() or "마커 지도").strip()

        if mode == "마커 지도":
            fig = make_marker_map(df_points())
        else:
            fig = make_choropleth(df_filtered(), gdf_sigungu)

        return go.FigureWidget(fig)
