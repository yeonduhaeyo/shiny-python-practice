from shiny import ui, module, render

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns

# (3-6 추가) Plotly + Shiny 연결(위젯 출력)
import plotly.express as px
from shinywidgets import output_widget, render_widget

from shared import df

# Matplotlib 기본 설정
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


def fmt_comma(ax, axis="x"):
    """축 숫자를 20,000 형태로 표시"""
    f = mtick.StrMethodFormatter("{x:,.0f}")
    (ax.xaxis if axis == "x" else ax.yaxis).set_major_formatter(f)


@module.ui
def page_viz_ui():
    return ui.nav_panel(
        "시각화",

        # (3-5) 정적 그래프 3종
        ui.layout_column_wrap(
            ui.card(
                ui.card_header("시도별 총 등록대수 Top 10 (막대)"),
                ui.output_plot("p_sido_top10", height="480px"),
            ),
            ui.card(
                ui.card_header("용도별 총 등록대수 분포 (박스플롯)"),
                ui.output_plot("p_use_box", height="480px"),
            ),
            ui.card(
                ui.card_header("전체 차종 비중 (파이)"),
                ui.output_plot("p_vehicle_pie", height="480px"),
            ),
            width=1/3,
        ),

        ui.hr(),

        # -----------------------------
        # (3-6 추가) Plotly 섹션: 카드 2개로 배치(동적 그래프)
        # - output_widget(): Plotly Figure를 넣을 "출력 자리"
        # -----------------------------
        ui.layout_columns(
            ui.card(
                ui.card_header("시군구별 총 등록대수 Top 20"),
                output_widget("px_sigungu_bar"),
            ),
            ui.card(
                ui.card_header("시도별 용도 구성 비중(%)"),
                output_widget("px_sido_use_ratio"),
            ),
            col_widths=(6, 6),
        ),
    )


@module.server
def page_viz_server(input, output, session):

    # (3-5) 막대그래프: 시도 Top 10
    @render.plot
    def p_sido_top10():
        fig, ax = plt.subplots(figsize=(7.2, 4.8))

        top10 = (
            df.groupby("시도")["계"].sum()
            .sort_values(ascending=False).head(10)
            .sort_values()
        )

        ax.barh(top10.index, top10.values)
        ax.set_title("시도별 총 등록대수 Top 10", pad=10)
        ax.set_xlabel("총 등록대수(계)")
        ax.set_ylabel("시도")
        fmt_comma(ax, "x")

        fig.tight_layout()
        return fig

    # (3-5) 박스플롯: 용도별 분포
    @render.plot
    def p_use_box():
        fig, ax = plt.subplots(figsize=(7.2, 4.8))

        sns.boxplot(data=df, x="용도별", y="계", ax=ax)
        ax.set_title("용도별 총 등록대수(계) 분포", pad=10)
        ax.set_xlabel("용도별")
        ax.set_ylabel("총 등록대수(계)")
        fmt_comma(ax, "y")

        # 카드 안에서 x축 라벨이 잘릴 때 대비
        fig.subplots_adjust(bottom=0.22)
        return fig

    # (3-5) 파이차트: 차종 비중 + 범례 분리
    @render.plot
    def p_vehicle_pie():
        fig, ax = plt.subplots(figsize=(7.2, 5.8))

        cols = ["승용", "화물", "승합", "특수"]
        totals = df[cols].sum().sort_values(ascending=False)

        def autopct_hide_small(pct):
            return f"{pct:.1f}%" if pct >= 2 else ""

        wedges, *_ = ax.pie(
            totals.values,
            labels=None,
            autopct=autopct_hide_small,
            startangle=90,
            counterclock=False,
            pctdistance=0.70,
        )

        ax.set_title("전체 차종 비중", pad=14)
        ax.axis("equal")

        pct = (totals / totals.sum() * 100).round(1)
        legend_labels = [f"{k} ({v:.1f}%)" for k, v in pct.items()]

        ax.legend(
            wedges,
            legend_labels,
            title="차종",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
        )

        fig.subplots_adjust(right=0.80)
        return fig

    # ============================================================
    # (3-6 추가) Plotly 그래프 2종
    # - @render_widget: Plotly Figure를 Shiny "위젯"으로 렌더링
    # - output_widget("...")와 id를 맞춰야 화면에 출력됨
    # ============================================================

    # (3-6 추가) 1) 시도+시군구별 총 등록대수 Top 20 (동적 막대)
    @render_widget
    def px_sigungu_bar():
        # 1) 시군구명 중복을 피하려고 '시도 + 시군구' 라벨 생성
        d = df.copy()
        d["지역(시도-시군구)"] = d["시도"].astype(str) + " " + d["시군구"].astype(str)

        # 2) 지역 라벨별 합계 → Top 20
        g = (
            d.groupby("지역(시도-시군구)", as_index=False)["계"]
            .sum()
            .sort_values("계", ascending=False)
            .head(20)
            .sort_values("계", ascending=True)  # 가로막대: 아래→위로 커지게
        )

        # 3) Plotly Express로 막대그래프 생성
        # - hover_data: 툴팁에 보여줄 컬럼/포맷 지정
        fig = px.bar(
            g,
            x="계",
            y="지역(시도-시군구)",
            orientation="h",
            title="시군구별 총 등록대수 Top 20",
            hover_data={"계": ":,d"},
        )

        # 4) 레이아웃 정리(축 제목/여백)
        fig.update_layout(
            xaxis_title="총 등록대수(계)",
            yaxis_title="지역(시도-시군구)",
            margin=dict(l=140, r=30, t=60, b=40),
        )
        return fig

    # (3-6 추가) 2) 시도별 용도 구성 비중(%) 100% 누적 막대
    @render_widget
    def px_sido_use_ratio():
        # 1) 시도-용도별 합계 집계
        g = df.groupby(["시도", "용도별"], as_index=False)["계"].sum()

        # 2) 시도 내부에서 구성비(%) 계산
        g["비중(%)"] = g["계"] / g.groupby("시도")["계"].transform("sum") * 100

        # 3) Plotly Express로 누적 막대(구성비 비교)
        fig = px.bar(
            g,
            x="시도",
            y="비중(%)",
            color="용도별",
            title="시도별 용도 구성 비중(%)",
            text=g["비중(%)"].round(1),
        )

        # 4) 0~100 스케일 고정 + 누적막대 설정
        fig.update_layout(
            barmode="stack",
            yaxis_title="비중(%)",
            xaxis_title="시도",
            yaxis=dict(range=[0, 100]),
            margin=dict(l=50, r=30, t=60, b=60),
            legend_title_text="용도별",
        )

        # 텍스트 겹침을 줄이기 위해 막대 내부에 배치
        fig.update_traces(textposition="inside")
        return fig
