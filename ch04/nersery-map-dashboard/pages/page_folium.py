import pandas as pd
import folium
from folium.plugins import MarkerCluster
from html import escape

from matplotlib.colors import LinearSegmentedColormap, Normalize, to_hex

from shiny import ui, module, reactive, render
from shared import df, gdf_sigungu


# 4-1. Import, 상수 추가 (SIG_COL / CMAP / STATUS_COLOR)
SIG_COL = "SIGUNGU_NM"

ACCENT = "#F08A5D"
CMAP = LinearSegmentedColormap.from_list(
    "nursery_coral",
    ["#FFF7F3", "#FBD3C6", "#F6A88F", ACCENT]
)

STATUS_COLOR = {"정상": "green", "재개": "orange", "휴지": "red"}


# 2. UI: 사이드바 입력 + 출력 영역 (page_folium_ui)
@module.ui
def page_folium_ui():
    gu_choices = ["전체"] + sorted(df["시군구"].dropna().astype(str).str.strip().unique())
    status_choices = ["정상", "재개", "휴지"]

    return ui.nav_panel(
        "Folium",
        ui.h3("Folium"),
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_selectize("gu", "구 선택", choices=gu_choices, selected="전체"),
                ui.input_checkbox_group(
                    "status",
                    "운영현황",
                    choices=status_choices,
                    selected=status_choices,
                ),
                width=320,
            ),
            ui.card(
                ui.card_header("Folium 지도"),
                ui.output_ui("folium_map"),
            ),
        ),
    )



@module.server
def page_folium_server(input, output, session):
    
    # 3. Server: 공통 필터 데이터 계산(reactive) (base_df)
    @reactive.calc
    def base_df() -> pd.DataFrame:
        out = df.copy()

        # 운영현황 필터
        if input.status():
            out = out[out["운영현황"].isin(list(input.status()))]

        # 좌표 결측 제거(지도 표시 안정성)
        out = out.dropna(subset=["위도", "경도"])

        # 문자열 정리(매칭/표시 안전)
        out["시군구"] = out["시군구"].astype(str).str.strip()
        out["운영현황"] = out["운영현황"].astype(str).str.strip()
        out["어린이집명"] = out["어린이집명"].astype(str).str.strip()

        return out

    # 4-2. 기본 지도 생성 (create_base_map)
    def create_base_map() -> folium.Map:
        try:
            minx, miny, maxx, maxy = gdf_sigungu.total_bounds
            center = [(miny + maxy) / 2, (minx + maxx) / 2]
        except Exception:
            center = [37.5665, 126.9780]

        return folium.Map(
            location=center,
            zoom_start=10,
            tiles="OpenStreetMap",
            control_scale=True,
        )

    # 4-3. 전체(구=전체): Choropleth 추가 (add_choropleth_all)
    def add_choropleth_all(m: folium.Map, points: pd.DataFrame) -> None:
        if SIG_COL not in gdf_sigungu.columns:
            raise KeyError(f"[gdf_sigungu] '{SIG_COL}' not found. columns={list(gdf_sigungu.columns)}")

        agg = points.groupby("시군구", as_index=False).size().rename(columns={"size": "cnt"})
        agg["시군구"] = agg["시군구"].astype(str).str.strip()

        g = gdf_sigungu.copy()
        g[SIG_COL] = g[SIG_COL].astype(str).str.strip()
        g = g.merge(agg, how="left", left_on=SIG_COL, right_on="시군구")
        g["cnt"] = g["cnt"].fillna(0).astype(int)

        vmin, vmax = float(g["cnt"].min()), float(g["cnt"].max())
        norm = Normalize(vmin=vmin, vmax=vmax) if vmax > vmin else Normalize(vmin=0, vmax=1)

        folium.GeoJson(
            g.__geo_interface__,
            name="시군구 단계구분도",
            style_function=lambda f: {
                "fillColor": to_hex(CMAP(norm(float(f["properties"].get("cnt", 0))))),
                "color": "#666666",
                "weight": 1.2,
                "fillOpacity": 0.78,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=[SIG_COL, "cnt"],
                aliases=["시군구", "어린이집 수"],
                localize=True,
                sticky=False,
            ),
        ).add_to(m)

    # 4-4. 특정 구: 폴리곤 강조 + 마커(클러스터/팝업) (add_polygon_and_markers)
    def add_polygon_and_markers(m: folium.Map, points: pd.DataFrame, gu: str) -> None:
        sel = gdf_sigungu[gdf_sigungu[SIG_COL].astype(str).str.strip() == gu]
        if len(sel) > 0:
            folium.GeoJson(
                sel.__geo_interface__,
                name=f"{gu} 경계",
                style_function=lambda _: {"weight": 6, "color": "#B22222", "fillOpacity": 0.15},
                highlight_function=lambda _: {"weight": 8},
            ).add_to(m)
            try:
                minx, miny, maxx, maxy = sel.total_bounds
                m.fit_bounds([[miny, minx], [maxy, maxx]])
            except Exception:
                pass

        pts = points[points["시군구"] == gu]
        cluster = MarkerCluster(name="어린이집(클러스터)").add_to(m)

        has_addr = "주소" in pts.columns
        has_tel = "어린이집전화번호" in pts.columns

        for _, r in pts.iterrows():
            name = escape(str(r.get("어린이집명", "")))
            status = str(r.get("운영현황", "")).strip()
            color = STATUS_COLOR.get(status, "blue")

            addr = escape(str(r.get("주소", ""))) if has_addr else ""
            tel = escape(str(r.get("어린이집전화번호", ""))) if has_tel else ""
            ctype = escape(str(r.get("어린이집유형구분", "")))

            popup = f"""
            <div style="font-size: 13px; line-height: 1.35;">
              <b>{name}</b><br/>
              <span>시군구: {escape(gu)}</span><br/>
              <span>운영현황: {escape(status)}</span><br/>
              <span>유형: {ctype}</span><br/>
              {"<span>주소: " + addr + "</span><br/>" if has_addr and addr else ""}
              {"<span>전화: " + tel + "</span><br/>" if has_tel and tel else ""}
            </div>
            """

            folium.Marker(
                [float(r["위도"]), float(r["경도"])],
                tooltip=name,
                popup=folium.Popup(popup, max_width=360),
                icon=folium.Icon(color=color, icon="info-sign"),
            ).add_to(cluster)

    # 4-5. make_map: 전체 vs 특정 구 분기 담당
    def make_map(points: pd.DataFrame) -> folium.Map:
        gu = input.gu() or "전체"
        m = create_base_map()

        if gu == "전체":
            add_choropleth_all(m, points)
        else:
            add_polygon_and_markers(m, points, gu)

        folium.LayerControl(collapsed=True).add_to(m)
        return m

    # 5. Shiny 출력: iframe(srcdoc)로 Folium HTML 임베드
    @render.ui
    def folium_map():
        m = make_map(base_df())
        return ui.tags.iframe(
            srcdoc=m.get_root().render(),
            style="width: 100%; height: 720px; border: 0;",
            loading="lazy",
        )
