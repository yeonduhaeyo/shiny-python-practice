# 1. GeoPandas 탭 파일 확인 (모듈 기본 구조 + import)
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable

import pandas as pd
from shiny import ui, module, reactive, render

from shared import df, gdf_sigungu


# 2. 기본 설정 추가 (한글 폰트 / 컬러맵)
ACCENT = "#F08A5D"   # 강조 코랄
FADE = "#D6D6D6"     # 비선택 회색

CMAP = LinearSegmentedColormap.from_list(
    "nursery_coral",
    ["#FFF7F3", "#FBD3C6", "#F6A88F", ACCENT]
)

def set_korean_font():
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False


# 3. 사이드바 및 입력 컴포넌트 추가 (UI)
@module.ui
def page_geopandas_ui():
    if "SIGUNGU_NM" not in gdf_sigungu.columns:
        raise KeyError("gdf_sigungu에 'SIGUNGU_NM' 컬럼이 필요합니다.")

    gu_list = (
        gdf_sigungu["SIGUNGU_NM"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
    choices = ["전체"] + sorted(gu_list)

    return ui.nav_panel(
        "GeoPandas",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_selectize("gu", "구 선택", choices=choices, selected="전체"),
                width=320,
            ),
            ui.card(
                ui.card_header("서울시 행정구역별 어린이집 수"),
                ui.output_plot("map", height="620px"),
                ui.hr(),
                ui.output_plot("bar", height="460px"),
            ),
        ),
    )


# 4~7. Server (집계/조인/지도/막대)
@module.server
def page_geopandas_server(input, output, session):

    # 4. 시군구별 어린이집 수 집계
    @reactive.calc
    def sgg_counts() -> pd.DataFrame:
        tmp = df[["시군구"]].copy()
        tmp["시군구"] = tmp["시군구"].astype(str).str.strip()

        out = (
            tmp.groupby("시군구")
            .size()
            .rename("어린이집수")
            .reset_index()
        )
        return out

    # 5. GeoJSON↔CSV 이름 기준 조인
    @reactive.calc
    def joined():
        g = gdf_sigungu.copy()
        g["SIGUNGU_NM"] = g["SIGUNGU_NM"].astype(str).str.strip()

        cnt = sgg_counts()

        j = g.merge(cnt, how="left", left_on="SIGUNGU_NM", right_on="시군구")
        j["어린이집수"] = j["어린이집수"].fillna(0).astype(int)
        return j

    # 6. Choropleth 지도 출력(전체/선택 분기)
    @render.plot
    def map():
        # 6-1. 입력/데이터 준비
        set_korean_font()
        g = joined()
        sel = (input.gu() or "전체").strip()

        # 6-2. Figure/축 준비(지도 + 컬러바 2축 구성)
        fig, (ax, cax) = plt.subplots(
            1, 2, figsize=(10, 8),
            gridspec_kw={"width_ratios": [24, 1]}
        )
        fig.subplots_adjust(wspace=0.05)
        ax.set_aspect("equal", adjustable="box")
        ax.set_anchor("C")

        # 6-3. 전체/선택 분기(표현 정책)
        if sel == "전체":
            # 6-3-1. 전체 모드: 전체를 그리고 라벨도 전체 표시
            g.plot(
                ax=ax, column="어린이집수", cmap=CMAP,
                edgecolor="white", linewidth=0.6, alpha=1.0, legend=False
            )

            for _, row in g.iterrows():
                pt = row.geometry.representative_point()
                ax.text(pt.x, pt.y, row["SIGUNGU_NM"], ha="center", va="center", fontsize=8)

            title = "서울 시군구별 어린이집 수"

            # 6-4-1. Zoom(전체 bounds)
            minx, miny, maxx, maxy = g.total_bounds
            padx = (maxx - minx) * 0.05
            pady = (maxy - miny) * 0.05
            ax.set_xlim(minx - padx, maxx + padx)
            ax.set_ylim(miny - pady, maxy + pady)

        else:
            # 6-3-2. 선택 모드: 비선택 페이드 + 선택 구 강조
            non_sel = g[g["SIGUNGU_NM"] != sel]
            sel_gdf = g[g["SIGUNGU_NM"] == sel]

            if len(non_sel) > 0:
                non_sel.plot(
                    ax=ax, column="어린이집수", cmap=CMAP,
                    edgecolor="white", linewidth=0.6, alpha=0.18, legend=False
                )

            if len(sel_gdf) > 0:
                sel_gdf.plot(
                    ax=ax, column="어린이집수", cmap=CMAP,
                    edgecolor="black", linewidth=2.6, alpha=1.0, legend=False
                )

                row = sel_gdf.iloc[0]
                pt = row.geometry.representative_point()
                ax.text(
                    pt.x, pt.y, row["SIGUNGU_NM"],
                    ha="center", va="center", fontsize=12, fontweight="bold"
                )

                # 6-4-2. Zoom(선택 bounds)
                minx, miny, maxx, maxy = sel_gdf.total_bounds
                padx = (maxx - minx) * 0.18
                pady = (maxy - miny) * 0.18
                ax.set_xlim(minx - padx, maxx + padx)
                ax.set_ylim(miny - pady, maxy + pady)

            title = f"{sel} 어린이집 수"

        # 6-5. 컬러바 설정 + 마무리
        vmax = max(int(g["어린이집수"].max()), 1)
        sm = ScalarMappable(norm=Normalize(0, vmax), cmap=CMAP)
        sm.set_array([])

        cbar = fig.colorbar(sm, cax=cax)
        cbar.set_label("어린이집 수")
        cax.yaxis.set_ticks_position("right")

        ax.set_axis_off()
        ax.set_title(title, pad=10)
        return fig

    # 7. 세로 막대그래프 출력(전체 구 + 선택 강조)
    @render.plot
    def bar():
        # 7-1. 데이터 준비/정렬
        set_korean_font()
        g = joined()
        sel = (input.gu() or "전체").strip()

        b = (
            g[["SIGUNGU_NM", "어린이집수"]]
            .drop_duplicates()
            .sort_values("어린이집수", ascending=False)
        )

        # 7-2. 색상 리스트 만들기(선택만 강조)
        names = b["SIGUNGU_NM"].tolist()
        vals = b["어린이집수"].tolist()

        if sel == "전체":
            colors = [ACCENT] * len(names)
        else:
            colors = [ACCENT if n == sel else FADE for n in names]

        # 7-3. 막대 그래프 출력
        fig, ax = plt.subplots(figsize=(10, 4.8))
        fig.subplots_adjust(bottom=0.28)

        ax.bar(names, vals, color=colors)
        ax.set_ylabel("어린이집 수")
        ax.set_title(
            "서울 전체 구 어린이집 수" + (" (선택 구 강조)" if sel != "전체" else ""),
            pad=8
        )
        ax.tick_params(axis="x", labelrotation=45)

        return fig