import json
import pandas as pd

from shiny import ui, module, reactive, render
from shared import df, KAKAO_APP_KEY

@module.ui
def page_kakao_ui():
    # 구/운영현황 선택지 구성
    gu_choices = ["전체"] + sorted(df["시군구"].dropna().astype(str).str.strip().unique())
    status_choices = ["정상", "재개", "휴지"]

    return ui.nav_panel(
        "Kakao",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_selectize("gu", "구 선택", choices=gu_choices, selected="전체"),
                ui.input_checkbox_group(
                    "status", "운영현황",
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

@module.server
def page_kakao_server(input, output, session):

    # (A) points(): 지도에 찍을 데이터 준비
    @reactive.calc
    def points() -> pd.DataFrame:
        out = df.copy()

        # 1) 운영현황 필터
        sts = list(input.status() or [])
        if sts:
            out = out[out["운영현황"].isin(sts)]

        # 2) 구 필터
        gu = (input.gu() or "전체").strip()
        if gu != "전체":
            out = out[out["시군구"].astype(str).str.strip() == gu]

        # 3) 좌표 숫자화 + 결측 제거
        out["위도"] = pd.to_numeric(out["위도"], errors="coerce")
        out["경도"] = pd.to_numeric(out["경도"], errors="coerce")
        out = out.dropna(subset=["위도", "경도"])

        # 4) 팝업에 필요한 컬럼 확보(없으면 빈값)
        need_cols = [
            "어린이집명", "시군구", "운영현황",
            "어린이집유형구분", "주소", "어린이집전화번호",
            "위도", "경도"
        ]
        for c in need_cols:
            if c not in out.columns:
                out[c] = ""

        # 5) 문자열 정리(표시 안정성)
        for c in ["어린이집명", "시군구", "운영현황", "어린이집유형구분", "주소", "어린이집전화번호"]:
            out[c] = out[c].astype(str).str.strip()

        return out[need_cols]

    # (B) build_kakao_html(): HTML + JS 생성
    def build_kakao_html(points_df: pd.DataFrame, app_key: str) -> str:
        # 1) Python DataFrame -> JSON payload
        payload = [
            {
                "name": r.get("어린이집명", ""),
                "gu": r.get("시군구", ""),
                "status": r.get("운영현황", ""),
                "type": r.get("어린이집유형구분", ""),
                "addr": r.get("주소", ""),
                "tel": r.get("어린이집전화번호", ""),
                "lat": float(r["위도"]),
                "lng": float(r["경도"]),
            }
            for _, r in points_df.iterrows()
        ]
        payload_json = json.dumps(payload, ensure_ascii=False)

        # 2) HTML 템플릿 반환
        #    - libraries=clusterer : 클러스터러 기능 사용
        #    - autoload=false      : kakao.maps.load() 안에서 시작
        #    - JSON은 별도 script 태그에 넣고, JS에서 JSON.parse로 읽음(깨짐 방지)
        return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    html, body {{ height:100%; margin:0; }}
    #map {{ width:100%; height:720px; }}
  </style>

  <!-- Kakao Maps SDK (clusterer 포함) -->
  <script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={app_key}&autoload=false&libraries=clusterer"></script>
</head>
<body>
  <div id="map"></div>

  <!-- JSON payload: 따옴표/특수문자 때문에 JS가 깨지는 문제를 줄이기 위해 데이터만 따로 넣음 -->
  <script id="markers-json" type="application/json">{payload_json}</script>

  <script>
    // (1) 팝업 HTML 안전 처리용 escape
    function esc(s) {{
      return String(s ?? "")
        .replace(/&/g,"&amp;")
        .replace(/</g,"&lt;")
        .replace(/>/g,"&gt;");
    }}

    // (2) JSON 읽기(파싱 실패 시 빈 배열)
    function getData() {{
      try {{
        const raw = document.getElementById("markers-json").textContent || "[]";
        return JSON.parse(raw);
      }} catch(e) {{
        console.error("markers JSON parse failed:", e);
        return [];
      }}
    }}

    // (3) SDK 로딩 완료 후 지도 생성
    kakao.maps.load(function () {{
      const data = getData();
      const container = document.getElementById("map");

      // 데이터가 없을 때도 지도를 띄우기 위한 fallback(서울)
      const fallback = new kakao.maps.LatLng(37.5665, 126.9780);

      // 데이터가 있으면 첫 포인트 기준으로 center
      const center = data.length
        ? new kakao.maps.LatLng(data[0].lat, data[0].lng)
        : fallback;

      // 지도 생성
      const map = new kakao.maps.Map(container, {{ center: center, level: 7 }});
      const bounds = new kakao.maps.LatLngBounds();

      // InfoWindow는 1개만 재사용(팝업 누적 방지)
      const iw = new kakao.maps.InfoWindow({{ removable: true }});

      // (4) 마커 생성 (clusterer에 넣을 거라 map 지정은 생략)
      const markers = data.map(m => {{
        const pos = new kakao.maps.LatLng(m.lat, m.lng);
        bounds.extend(pos);

        const marker = new kakao.maps.Marker({{
          position: pos,
          title: m.name || ""
        }});

        // (5) 클릭 이벤트: 상세 팝업(요구사항)
        kakao.maps.event.addListener(marker, "click", function() {{
          const html =
            '<div style="padding:8px 10px; font-size:12px; line-height:1.45; max-width:360px;">' +
              '<div style="font-weight:700; margin-bottom:6px;">' + esc(m.name) + '</div>' +
              '<div>시군구: ' + esc(m.gu) + '</div>' +
              '<div>운영현황: ' + esc(m.status) + '</div>' +
              (m.type ? '<div>유형: ' + esc(m.type) + '</div>' : '') +
              (m.addr ? '<div>주소: ' + esc(m.addr) + '</div>' : '') +
              (m.tel ? '<div>전화: ' + esc(m.tel) + '</div>' : '') +
            '</div>';

          iw.setContent(html);
          iw.open(map, marker);
        }});

        return marker;
      }});

      // (6) 클러스터링 적용(렉 완화)
      const clusterer = new kakao.maps.MarkerClusterer({{
        map: map,
        averageCenter: true,
        minLevel: 6,
        disableClickZoom: false
      }});
      clusterer.addMarkers(markers);

      // (7) 화면 맞추기
      if (data.length >= 2) map.setBounds(bounds);
      else map.setCenter(center);
    }});
  </script>
</body>
</html>"""

    # (C) Shiny 출력: iframe(srcdoc)
    @render.ui
    def kakao_map():
        # 키가 없으면 지도를 만들 수 없으니 안내문 출력
        if not KAKAO_APP_KEY:
            return ui.div(
                ui.p("Kakao JavaScript Key가 설정되지 않았습니다."),
                ui.p("data/config_api.py에 KAKAO_JAVASCRIPT_KEY를 저장한 뒤 다시 실행하세요."),
                ui.p("또한 Kakao Developers에서 Web 도메인 등록이 되어 있어야 합니다.")
            )

        # points() -> payload(JSON) -> HTML -> iframe(srcdoc)
        html = build_kakao_html(points(), KAKAO_APP_KEY)
        return ui.tags.iframe(
            srcdoc=html,
            style="width:100%; height:720px; border:0;",
            loading="lazy",
        )