# # app.py
# from __future__ import annotations

# import io
# import pandas as pd

# import matplotlib.pyplot as plt
# import seaborn as sns
# import plotly.express as px

# from shiny import App, ui, render, reactive
# from shiny.render import DataGrid
# from shinywidgets import output_widget, render_widget


# # -----------------------------
# # 1) 샘플 데이터(임의 생성)
# # -----------------------------
# def make_sample_df() -> pd.DataFrame:
#     # "전국 전기차 차종별/용도별 등록대수" 느낌을 살린 예시
#     rows = [
#         ("서울특별시", "강남구", "비사업용", 18000, 220, 1500, 20),
#         ("서울특별시", "강남구", "사업용",   1200,  60,  900, 10),
#         ("서울특별시", "송파구", "비사업용", 16000, 210, 1400, 15),
#         ("서울특별시", "송파구", "사업용",    900,  55,  820,  8),

#         ("부산광역시", "해운대구", "비사업용", 9000, 120, 900, 10),
#         ("부산광역시", "해운대구", "사업용",   700,  40, 650,  7),
#         ("부산광역시", "사하구",   "비사업용", 8200, 110, 850,  9),
#         ("부산광역시", "사하구",   "사업용",   650,  38, 620,  6),

#         ("대구광역시", "수성구", "비사업용", 7800, 90, 820, 8),
#         ("대구광역시", "수성구", "사업용",    620, 35, 600, 5),
#         ("대구광역시", "달서구", "비사업용", 7100, 85, 780, 7),
#         ("대구광역시", "달서구", "사업용",    590, 33, 580, 5),

#         ("경기도", "성남시", "비사업용", 14000, 180, 2400, 18),
#         ("경기도", "성남시", "사업용",    1100,  70, 1600, 12),
#         ("경기도", "수원시", "비사업용", 15000, 190, 2600, 20),
#         ("경기도", "수원시", "사업용",    1200,  75, 1700, 13),

#         ("인천광역시", "연수구", "비사업용", 8600, 100, 980, 9),
#         ("인천광역시", "연수구", "사업용",    680,  42, 720, 6),
#     ]

#     df = pd.DataFrame(
#         rows,
#         columns=["시도", "시군구", "용도별", "승용", "승합", "화물", "특수"],
#     )
#     df["연료별"] = "전기"
#     df["계"] = df[["승용", "승합", "화물", "특수"]].sum(axis=1)

#     # 화면 표준 컬럼(실데이터 들어오면 rename으로 이 형태 맞추면 됨)
#     df["지역"] = df["시도"] + " " + df["시군구"]
#     df = df[["지역", "시도", "시군구", "연료별", "용도별", "승용", "승합", "화물", "특수", "계"]]

#     return df


# df_clean = make_sample_df()
# df_long = df_clean.melt(
#     id_vars=["지역", "시도", "시군구", "연료별", "용도별"],
#     value_vars=["승용", "승합", "화물", "특수"],
#     var_name="차종",
#     value_name="등록대수",
# )


# # -----------------------------
# # 2) UI
# # -----------------------------
# app_ui = ui.page_navbar(
#     ui.nav_panel(
#         "데이터",
#         ui.layout_columns(
#             ui.card(
#                 ui.card_header("데이터 요약"),
#                 ui.output_text("meta_summary"),
#             ),
#             ui.card(
#                 ui.card_header("DataFrame info()"),
#                 ui.output_text_verbatim("df_info"),
#             ),
#             col_widths=(6, 6),
#         ),
#         ui.card(
#             ui.card_header("미리보기 (상위 20행)"),
#             ui.output_data_frame("df_head"),
#         ),
#     ),

#     ui.nav_panel(
#         "시각화",
#         ui.h4("정적 그래프 (Matplotlib·Seaborn)"),
#         ui.layout_columns(
#             ui.card(
#                 ui.card_header("전체 등록대수(계) 분포"),
#                 ui.output_plot("plt_hist_total"),
#             ),
#             ui.card(
#                 ui.card_header("용도별 등록대수(계) 비교"),
#                 ui.output_plot("plt_box_purpose"),
#             ),
#             col_widths=(6, 6),
#         ),
#         ui.card(
#             ui.card_header("산점도: 승용 vs 화물 (용도별)"),
#             ui.output_plot("plt_scatter_passenger_cargo"),
#         ),
#         ui.hr(),
#         ui.h4("동적 그래프 (Plotly)"),
#         ui.layout_columns(
#             ui.card(
#                 ui.card_header("지역 Top 10 (계 기준)"),
#                 output_widget("w_top_regions"),
#             ),
#             ui.card(
#                 ui.card_header("차종 구성(Top 8 지역, 100% 누적)"),
#                 output_widget("w_composition"),
#             ),
#             col_widths=(6, 6),
#         ),
#     ),

#     ui.nav_panel(
#         "조건별 분석",
#         ui.layout_sidebar(
#             ui.sidebar(
#                 ui.input_selectize(
#                     "purpose",
#                     "용도별",
#                     choices=["전체"] + sorted(df_clean["용도별"].unique().tolist()),
#                     selected="전체",
#                 ),
#                 ui.input_selectize(
#                     "vehicle",
#                     "집계 기준",
#                     choices=["계", "승용", "승합", "화물", "특수"],
#                     selected="계",
#                 ),
#                 ui.input_slider("top_n", "Top N (지역)", min=5, max=20, value=10),
#                 ui.input_text("region_kw", "지역 검색(포함)", placeholder="예: 강남, 수원, 해운대"),
#                 title="조건 선택",
#             ),
#             ui.layout_columns(
#                 ui.value_box("선택 조건 총합", ui.output_text("kpi_total")),
#                 ui.value_box("사업용 비중", ui.output_text("kpi_business_share")),
#                 col_widths=(6, 6),
#             ),
#             ui.layout_columns(
#                 ui.card(ui.card_header("지역 Top-N"), output_widget("w_bar_topn")),
#                 ui.card(ui.card_header("산점도: 승용 vs 화물"), output_widget("w_scatter")),
#                 col_widths=(6, 6),
#             ),
#             ui.card(
#                 ui.card_header("상세 데이터(지역 집계)"),
#                 ui.output_data_frame("grid_table"),
#             ),
#         ),
#     ),

#     title="전국 전기차 등록대수 대시보드 (샘플)",
# )


# # -----------------------------
# # 3) Server
# # -----------------------------
# def server(input, output, session):
#     # ---- 데이터 탭 ----
#     @render.text
#     def meta_summary():
#         n_rows, n_cols = df_clean.shape
#         sido_n = df_clean["시도"].nunique()
#         sigungu_n = df_clean["시군구"].nunique()
#         purpose_n = df_clean["용도별"].nunique()
#         total_sum = int(df_clean["계"].sum())

#         lines = [
#             f"- 행/열: {n_rows:,} × {n_cols:,}",
#             f"- 시도 수: {sido_n}",
#             f"- 시군구 수: {sigungu_n}",
#             f"- 용도 구분 수: {purpose_n}",
#             f"- 전체 등록대수 합계(계): {total_sum:,}",
#         ]
#         return "\n".join(lines)

#     @render.text
#     def df_info():
#         buf = io.StringIO()
#         df_clean.info(buf=buf)
#         return buf.getvalue()

#     @render.data_frame
#     def df_head():
#         return DataGrid(df_clean.head(20), height="360px")

#     # ---- 시각화 탭(정적) ----
#     @render.plot
#     def plt_hist_total():
#         fig, ax = plt.subplots()
#         sns.histplot(df_clean["계"], bins=20, ax=ax)
#         ax.set_xlabel("등록대수(계)")
#         ax.set_ylabel("빈도")
#         return fig

#     @render.plot
#     def plt_box_purpose():
#         fig, ax = plt.subplots()
#         sns.boxplot(data=df_clean, x="용도별", y="계", ax=ax)
#         ax.set_xlabel("용도별")
#         ax.set_ylabel("등록대수(계)")
#         return fig

#     @render.plot
#     def plt_scatter_passenger_cargo():
#         fig, ax = plt.subplots()
#         sns.scatterplot(data=df_clean, x="승용", y="화물", hue="용도별", ax=ax)
#         ax.set_xlabel("승용 등록대수")
#         ax.set_ylabel("화물 등록대수")
#         return fig

#     # ---- 시각화 탭(동적) ----
#     @render_widget
#     def w_top_regions():
#         d = (
#             df_clean.groupby("지역", as_index=False)["계"]
#             .sum()
#             .sort_values("계", ascending=False)
#             .head(10)
#         )
#         fig = px.bar(d, x="지역", y="계")
#         fig.update_layout(xaxis_title="지역", yaxis_title="등록대수(계)")
#         return fig

#     @render_widget
#     def w_composition():
#         top_regions = (
#             df_long.groupby("지역", as_index=False)["등록대수"]
#             .sum()
#             .sort_values("등록대수", ascending=False)
#             .head(8)["지역"]
#             .tolist()
#         )
#         d = df_long[df_long["지역"].isin(top_regions)].copy()
#         denom = d.groupby("지역")["등록대수"].transform("sum").replace(0, 1)
#         d["비중"] = d["등록대수"] / denom
#         fig = px.bar(d, x="지역", y="비중", color="차종", barmode="stack")
#         fig.update_layout(xaxis_title="지역", yaxis_title="차종 비중(합=1)")
#         return fig

#     # ---- 조건별 분석 탭 ----
#     @reactive.calc
#     def filtered_df() -> pd.DataFrame:
#         d = df_clean.copy()

#         # 용도별 조건
#         if input.purpose() != "전체":
#             d = d[d["용도별"] == input.purpose()]

#         # 지역 키워드(부분 포함)
#         kw = (input.region_kw() or "").strip()
#         if kw:
#             d = d[d["지역"].astype(str).str.contains(kw, na=False)]

#         return d

#     @reactive.calc
#     def summary_by_region() -> pd.DataFrame:
#         d = filtered_df()
#         target = input.vehicle()
#         if target not in d.columns:
#             target = "계"

#         s = (
#             d.groupby("지역", as_index=False)[target]
#             .sum()
#             .rename(columns={target: "값"})
#             .sort_values("값", ascending=False)
#         )
#         return s

#     @render.text
#     def kpi_total():
#         s = summary_by_region()
#         return f"{int(s['값'].sum()):,}" if not s.empty else "0"

#     @render.text
#     def kpi_business_share():
#         # 현재 '지역 검색' 조건만 반영하여 사업용 비중(계 기준) 표시
#         d = df_clean.copy()
#         kw = (input.region_kw() or "").strip()
#         if kw:
#             d = d[d["지역"].astype(str).str.contains(kw, na=False)]

#         total = d["계"].sum()
#         business = d.loc[d["용도별"] == "사업용", "계"].sum()
#         if total > 0:
#             return f"{business/total:.1%}"
#         return "-"

#     @render_widget
#     def w_bar_topn():
#         s = summary_by_region().head(int(input.top_n()))
#         fig = px.bar(s, x="지역", y="값")
#         fig.update_layout(xaxis_title="지역", yaxis_title="등록대수")
#         return fig

#     @render_widget
#     def w_scatter():
#         d = filtered_df()
#         s = (
#             d.groupby(["지역", "용도별"], as_index=False)[["승용", "화물"]]
#             .sum()
#         )
#         fig = px.scatter(
#             s,
#             x="승용",
#             y="화물",
#             color="용도별",
#             hover_name="지역",
#             size="승용",
#         )
#         fig.update_layout(xaxis_title="승용", yaxis_title="화물")
#         return fig

#     @render.data_frame
#     def grid_table():
#         s = summary_by_region().head(200)
#         return DataGrid(s, height="420px")


# app = App(app_ui, server)
