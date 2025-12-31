# pages/page_viz.py
from shiny import ui, module, render

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns

from shared import df

# 2) 한글 폰트 기본 설정 추가
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


# 3) 축 숫자 콤마 포맷 유틸 함수 추가
def fmt_comma(ax, axis="x"):
    f = mtick.StrMethodFormatter("{x:,.0f}")
    (ax.xaxis if axis == "x" else ax.yaxis).set_major_formatter(f)


# 1) 베이스 UI 만들기(카드 위치 배치)
@module.ui
def page_viz_ui():
    return ui.nav_panel(
        "시각화",
        ui.h3("시각화"),

        # 1-1) 그래프 카드 3개를 한 줄에 배치
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
                ui.output_plot("p_vehicle_pie", height="520px"),
            ),
            width=1/3,
        ),

        ui.hr(),

        # 1-2) 다음 레슨(Plotly) 영역 자리만 미리 확보
        ui.card(
            ui.card_header("동적 그래프(Plotly) — 다음 레슨"),
            ui.p("다음 레슨에서 Plotly 그래프를 이 섹션에 추가해 ‘시각화’ 탭을 완성합니다."),
        ),
    )


@module.server
def page_viz_server(input, output, session):

    # 4) 막대그래프(시도 Top 10) 구현
    @render.plot
    def p_sido_top10():
        fig, ax = plt.subplots(figsize=(7.2, 4.8), constrained_layout=True)

        top10 = (
            df.groupby("시도")["계"].sum()
            .sort_values(ascending=False).head(10)
            .sort_values()  # barh에서 아래→위로 커지게
        )

        ax.barh(top10.index, top10.values)
        ax.set_title("시도별 총 등록대수 Top 10", pad=10)
        ax.set_xlabel("총 등록대수(계)")
        ax.set_ylabel("시도")
        fmt_comma(ax, "x")
        return fig

    # 5) 박스플롯(용도별 분포) 구현
    @render.plot
    def p_use_box():
        fig, ax = plt.subplots(figsize=(7.2, 4.8), constrained_layout=True)

        sns.boxplot(data=df, x="용도별", y="계", ax=ax)
        ax.set_title("용도별 총 등록대수(계) 분포", pad=10)
        ax.set_xlabel("용도별")
        ax.set_ylabel("총 등록대수(계)")
        fmt_comma(ax, "y")

        # 카드 안에서 x축 라벨이 잘릴 때 대비(최소한만)
        fig.subplots_adjust(bottom=0.22)
        return fig

    # 6) 파이차트(차종 비중 + 범례 분리) 구현
    @render.plot
    def p_vehicle_pie():
        fig, ax = plt.subplots(figsize=(7.2, 5.8), constrained_layout=True)

        cols = ["승용", "화물", "승합", "특수"]
        totals = df[cols].sum().sort_values(ascending=False)

        # 작은 조각은 퍼센트 표기 생략(겹침 방지)
        def autopct_hide_small(pct):
            return f"{pct:.1f}%" if pct >= 2 else ""

        wedges, *_ = ax.pie(
            totals.values,
            labels=None,                 # 라벨은 범례로 처리
            autopct=autopct_hide_small,  # 퍼센트만 표시
            startangle=90,
            counterclock=False,
            pctdistance=0.70,
        )

        ax.set_title("전체 차종 비중", pad=14)
        ax.axis("equal")

        # 범례: 항목명 + 퍼센트
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

        # 범례 자리 확보
        fig.subplots_adjust(right=0.80)
        return fig
