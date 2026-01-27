# =========================================================
# pages/page_kakao.py
# =========================================================

# =========================================================
# 0. Imports
# =========================================================
import os
import json
import pandas as pd
from html import escape

from shiny import ui, module, reactive, render
from shared import df


# =========================================================
# 1. Kakao JavaScript Key (환경변수)
# =========================================================
KAKAO_APP_KEY = os.getenv("KAKAO_JAVASCRIPT_KEY", "")

# 디버그 메시지(화면 하단 표시) 켜기/끄기
DEBUG = True


# =========================================================
# 2. UI: 사이드바 입력 + 출력 영역
# =========================================================
@module.ui
def page_kakao_ui():
    gu_choices = ["전체"] + sorted(df["시군구"].dropna().astype(str).str.strip().unique())
    status_choices = ["정상", "재개", "휴지"]

    return ui.nav_panel(
        "Kakao",
        ui.h3("Kakao Maps (JS API)"),
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
                ui.card_header("Kakao 지도 마커"),
                ui.output_ui("kakao_map"),
                full_screen=True,
            ),
        ),
    )


# =========================================================
# 3. Server: 필터 데이터 + (페이지 내부) Kakao 지도 렌더링
# =========================================================
@module.server
def page_kakao_server(input, output, session):

    # -----------------------------------------------------
    # 3-1. Server: 필터된 점 데이터 계산(reactive)
    # -----------------------------------------------------
    @reactive.calc
    def base_df() -> pd.DataFrame:
        out = df.copy()

        if input.status():
            out = out[out["운영현황"].isin(list(input.status()))]

        if (input.gu() or "전체") != "전체":
            out = out[out["시군구"] == input.gu()]

        out = out.dropna(subset=["위도", "경도"])

        out["어린이집명"] = out["어린이집명"].astype(str).str.strip()
        out["운영현황"] = out["운영현황"].astype(str).str.strip()
        out["시군구"] = out["시군구"].astype(str).str.strip()

        return out

    # -----------------------------------------------------
    # 3-2. HTML 조립: map div + script (iframe/srcdoc 사용 안 함)
    # -----------------------------------------------------
    def build_inline_map(points: pd.DataFrame, app_key: str, debug: bool = True) -> ui.TagList:
        # 지도 컨테이너 id는 고정(탭 내부에서만 사용)
        map_id = "kakao_map_div"

        # JS로 넘길 마커 데이터(최소 필드)
        markers = []
        for _, r in points.iterrows():
            markers.append(
                {
                    "name": escape(str(r.get("어린이집명", ""))),
                    "status": escape(str(r.get("운영현황", ""))),
                    "gu": escape(str(r.get("시군구", ""))),
                    "lat": float(r["위도"]),
                    "lng": float(r["경도"]),
                }
            )

        markers_json = json.dumps(markers, ensure_ascii=False)

        debug_div = ui.tags.div(
            {"id": "kakao_debug"},
            "debug: start",
            style=(
                "position:fixed; left:12px; bottom:12px; z-index:9999;"
                "background:rgba(0,0,0,.7); color:#fff; padding:6px 8px;"
                "font-size:12px; border-radius:6px; display:" + ("block" if debug else "none") + ";"
            ),
        )

        # 핵심: SDK가 없으면 동적 삽입 → 로드 완료 후 init 실행
        # (autoload=false + kakao.maps.load() 사용)
        script = ui.tags.script(
            f"""
(function() {{
  const markers = {markers_json};
  const mapId = "{map_id}";
  const debugOn = {str(debug).lower()};
  const appKey = "{app_key}";

  function debug(msg) {{
    if (!debugOn) return;
    const el = document.getElementById("kakao_debug");
    if (el) el.textContent = "debug: " + msg;
  }}

  function loadSdk(callback) {{
    if (window.kakao && window.kakao.maps) {{
      debug("SDK already loaded");
      return callback();
    }}

    // 중복 로드 방지
    if (window.__KAKAO_SDK_LOADING__) {{
      debug("SDK loading... wait");
      const t = setInterval(() => {{
        if (window.kakao && window.kakao.maps) {{
          clearInterval(t);
          callback();
        }}
      }}, 50);
      return;
    }}
    window.__KAKAO_SDK_LOADING__ = true;

    debug("inject SDK script");
    const s = document.createElement("script");
    s.src = "https://dapi.kakao.com/v2/maps/sdk.js?appkey=" + appKey + "&autoload=false";
    s.onload = () => {{
      debug("SDK script loaded");
      callback();
    }};
    s.onerror = () => {{
      debug("ERROR: SDK script load failed");
    }};
    document.head.appendChild(s);
  }}

  function initMap() {{
    try {{
      debug("initMap start (markers=" + markers.length + ")");
      const container = document.getElementById(mapId);
      if (!container) {{
        debug("ERROR: container not found");
        return;
      }}

      kakao.maps.load(function() {{
        debug("kakao.maps.load callback");

        const center = markers.length
          ? new kakao.maps.LatLng(markers[0].lat, markers[0].lng)
          : new kakao.maps.LatLng(37.5665, 126.9780);

        const map = new kakao.maps.Map(container, {{
          center: center,
          level: 6
        }});

        const bounds = new kakao.maps.LatLngBounds();

        markers.forEach(m => {{
          const pos = new kakao.maps.LatLng(m.lat, m.lng);
          bounds.extend(pos);

          const marker = new kakao.maps.Marker({{
            map: map,
            position: pos,
            title: m.name
          }});

          const iw = new kakao.maps.InfoWindow({{
            content: `
              <div style="padding:6px 8px; font-size:12px; line-height:1.35;">
                <b>${{m.name}}</b><br/>
                <span>시군구: ${{m.gu}}</span><br/>
                <span>운영현황: ${{m.status}}</span>
              </div>`
          }});

          kakao.maps.event.addListener(marker, "click", function() {{
            iw.open(map, marker);
          }});
        }});

        if (markers.length >= 2) {{
          map.setBounds(bounds);
          debug("bounds fitted");
        }} else {{
          debug("map created");
        }}
      }});
    }} catch (e) {{
      debug("ERROR: " + e.message);
    }}
  }}

  // Shiny가 DOM에 붙인 직후 실행되도록 약간 지연
  setTimeout(() => {{
    loadSdk(initMap);
  }}, 0);
}})();
"""
        )

        return ui.TagList(
            ui.tags.div(id=map_id, style="width:100%; height:720px; background:#eee;"),
            debug_div,
            script,
        )

    # -----------------------------------------------------
    # 4. Shiny 출력: output_ui로 지도 영역 렌더
    # -----------------------------------------------------
    @render.ui
    def kakao_map():
        if not KAKAO_APP_KEY or len(KAKAO_APP_KEY) < 10:
            return ui.div(
                ui.p("KAKAO_JAVASCRIPT_KEY 환경변수가 비어있거나 올바르지 않습니다."),
                ui.p("Kakao Developers에서 JavaScript 키 발급 후 환경변수로 설정하고, 새 터미널에서 다시 실행하세요."),
                ui.p("또한 JavaScript SDK 도메인에 현재 접속 주소(예: http://127.0.0.1:8000)를 등록해야 합니다."),
            )

        return build_inline_map(base_df(), KAKAO_APP_KEY, debug=DEBUG)
