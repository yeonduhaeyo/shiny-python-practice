import pandas as pd  # 추가
import matplotlib.pyplot as plt  # 추가
import seaborn as sns
from faicons import icon_svg

# Import data from shared.py
from shared import app_dir, df

from shiny import App, reactive, render, ui

# (추가) Matplotlib 한글 폰트 설정
# - 축/제목 한글 깨짐 방지
# - 마이너스 기호 깨짐 방지
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# (추가) 색상/정렬 상수: 그래프 일관성 유지
# - SPECIES_PALETTE: 종별 색상을 항상 동일하게 고정
# - SPECIES_ORDER: 범례/정렬 순서 고정
# - ISLAND_ORDER: 섬 정렬 순서 고정
SPECIES_PALETTE = {
    "Adelie": "#1f77b4",
    "Chinstrap": "#ff7f0e",
    "Gentoo": "#2ca02c",
}
SPECIES_ORDER = ["Adelie", "Chinstrap", "Gentoo"]
ISLAND_ORDER = ["Biscoe", "Dream", "Torgersen"]

# (추가) 표 컬럼명 한국어 매핑: DataGrid 가독성 개선
COL_MAP_KR = {
    "species": "종(species)",
    "island": "섬(island)",
    "bill_length_mm": "부리 길이(mm)",
    "bill_depth_mm": "부리 깊이(mm)",
    "flipper_length_mm": "날개 길이(mm)",
    "body_mass_g": "몸무게(g)",
    "sex": "성별(sex)",
}


def rename_cols_kr(d: pd.DataFrame) -> pd.DataFrame:
    """(추가) DataFrame 컬럼명을 한국어 라벨로 변환한다."""
    return d.rename(columns={c: COL_MAP_KR.get(c, c) for c in d.columns})


# UI 정의
# - 사이드바: 필터 + 적용 버튼(이벤트 기반 리액티브)
# - 메인: 탭 3개(부리 요약 / 날개·무게 / 섬×종)
app_ui = ui.page_sidebar(
    ui.sidebar(
        # (수정) 라벨 한국어화
        ui.input_slider("mass", "몸무게 상한(g)", 2000, 6000, 6000),
        ui.input_checkbox_group(
            "species",
            "종(species)",
            SPECIES_ORDER, # 순서 오름차순 고정을 위해 변경
            selected=["Adelie", "Chinstrap", "Gentoo"],
        ),

        # (추가) 적용 버튼: 눌렀을 때만 전체 결과 갱신
        ui.hr(),
        ui.input_action_button("apply", "적용"),
        ui.p("필터를 바꿔도 즉시 갱신되지 않습니다. '적용'을 눌러 결과를 업데이트하세요."),

        # (수정) 사이드바 타이틀 한국어화
        title="필터 컨트롤",
    ),

    # (추가) 탭 구조
    ui.navset_tab(
        # Tab 1) 부리 요약 (기존 화면을 탭으로 옮김)
        ui.nav_panel(
            "부리 요약",
            ui.layout_column_wrap(
                ui.value_box("펭귄 수", ui.output_text("count"), showcase=icon_svg("earlybirds")),
                ui.value_box("평균 부리 길이", ui.output_text("bill_length"), showcase=icon_svg("ruler-horizontal")),
                ui.value_box("평균 부리 깊이", ui.output_text("bill_depth"), showcase=icon_svg("ruler-vertical")),
                fill=False,
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("부리 길이 vs 부리 깊이"),
                    ui.output_plot("length_depth"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header("펭귄 데이터(필터 결과)"),
                    ui.output_data_frame("summary_statistics"),
                    full_screen=True,
                ),
            ),
        ),

        # Tab 2) 날개·무게 요약 (새 탭)
        # - KPI: 평균 날개 길이, 평균 몸무게, 상관계수
        # - Plot: 날개 길이 vs 몸무게 산점도
        # - Table: 관련 컬럼 테이블
        ui.nav_panel(
            "날개·무게 요약",
            ui.layout_column_wrap(
                ui.value_box("평균 날개 길이", ui.output_text("avg_flipper"), showcase=icon_svg("ruler")),
                ui.value_box("평균 몸무게", ui.output_text("avg_mass"), showcase=icon_svg("weight-scale")),
                ui.value_box("상관계수(날개-무게)", ui.output_text("corr_flipper_mass"), showcase=icon_svg("chart-line")),
                fill=False,
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("날개 길이 vs 몸무게"),
                    ui.output_plot("flipper_mass"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header("날개·무게 데이터"),
                    ui.output_data_frame("fm_table"),
                    full_screen=True,
                ),
                col_widths=[7, 5],
            ),
        ),

        # Tab 3) 섬×종 요약 (새 탭)
        # - Plot: 섬별 종별 개수 막대그래프
        # - Table: 섬(행)×종(열) 교차표
        ui.nav_panel(
            "섬×종 요약",
            ui.layout_columns(
                ui.card(
                    ui.card_header("섬별 종별 개수"),
                    ui.output_plot("island_species_counts"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header("섬×종 개수 요약표"),
                    ui.output_data_frame("island_species_summary"),
                    full_screen=True,
                ),
                col_widths=[6, 6],
            ),
        ),

        id="tabs",
        selected="부리 요약",
    ),

    ui.include_css(app_dir / "styles.css"),

    # (수정) 페이지 타이틀 한국어화
    title="펭귄 대시보드",
    fillable=True,
)


def server(input, output, session):
    # (수정) 공통 계산값 filtered_df를 "적용 버튼" 기반으로 변경
    # - input.apply 클릭 시점에만 다시 계산됨
    # - ignore_none=False: 앱 최초 로딩 시에도 1회 계산
    @reactive.calc
    @reactive.event(input.apply, ignore_none=False)
    def filtered_df():
        filt_df = df[df["species"].isin(input.species())]
        filt_df = filt_df.loc[filt_df["body_mass_g"] < input.mass()]
        return filt_df

    # Tab 1) 부리 요약 - KPI
    @render.text
    def count():
        # (권장) 사람 읽기 좋게 천 단위 콤마를 넣고 싶으면 f-string 사용 가능
        return f"{filtered_df().shape[0]:,}"

    @render.text
    def bill_length():
        return f"{filtered_df()['bill_length_mm'].mean():.1f} mm"

    @render.text
    def bill_depth():
        return f"{filtered_df()['bill_depth_mm'].mean():.1f} mm"

    # Tab 1) 부리 요약 - 산점도
    # (수정) fig, ax 패턴으로 전환하여:
    # - 축/제목 한국어 적용
    # - 빈 데이터 처리
    # - 종 색상/범례 순서 고정
    @render.plot
    def length_depth():
        fig, ax = plt.subplots()

        d = filtered_df().dropna(subset=["bill_length_mm", "bill_depth_mm", "species"])
        if d.empty:
            ax.set_title("데이터 없음")
            ax.set_xlabel("부리 길이(mm)")
            ax.set_ylabel("부리 깊이(mm)")
            return fig

        present = set(d["species"].unique())
        hue_order_present = [s for s in SPECIES_ORDER if s in present]

        sns.scatterplot(
            data=d,
            x="bill_length_mm",
            y="bill_depth_mm",
            hue="species",
            hue_order=hue_order_present,
            palette=SPECIES_PALETTE,
            ax=ax,
        )
        ax.set_title("부리 길이 vs 부리 깊이")
        ax.set_xlabel("부리 길이(mm)")
        ax.set_ylabel("부리 깊이(mm)")
        ax.legend(title="종(species)")
        return fig

    # Tab 1) 부리 요약 - 표(DataGrid)
    # (수정) 표 컬럼명을 한국어로 출력
    @render.data_frame
    def summary_statistics():
        cols = ["species", "island", "bill_length_mm", "bill_depth_mm", "body_mass_g"]
        view = rename_cols_kr(filtered_df()[cols])
        return render.DataGrid(view, filters=True)

    # Tab 2) 날개·무게 요약 - KPI
    # (설명)
    # - avg_flipper: 날개 길이 평균
    # - avg_mass: 몸무게 평균
    # - corr_flipper_mass: 상관계수(표본 부족 시 N/A)
    @render.text
    def avg_flipper():
        return f"{filtered_df()['flipper_length_mm'].mean():.1f} mm"

    @render.text
    def avg_mass():
        return f"{filtered_df()['body_mass_g'].mean():.0f} g"

    @render.text
    def corr_flipper_mass():
        d = filtered_df().dropna(subset=["flipper_length_mm", "body_mass_g"])
        if d.shape[0] < 2:
            return "N/A"
        return f"{d['flipper_length_mm'].corr(d['body_mass_g']):.3f}"

    # Tab 2) 날개·무게 요약 - 산점도
    # (설명)
    # - 종 색상 고정(SPECIES_PALETTE)
    # - 범례 순서 고정(SPECIES_ORDER)
    # - 빈 데이터 안내
    @render.plot
    def flipper_mass():
        fig, ax = plt.subplots()

        d = filtered_df().dropna(subset=["flipper_length_mm", "body_mass_g", "species"])
        if d.empty:
            ax.set_title("데이터 없음")
            ax.set_xlabel("날개 길이(mm)")
            ax.set_ylabel("몸무게(g)")
            return fig

        present = set(d["species"].unique())
        hue_order_present = [s for s in SPECIES_ORDER if s in present]

        sns.scatterplot(
            data=d,
            x="flipper_length_mm",
            y="body_mass_g",
            hue="species",
            hue_order=hue_order_present,
            palette=SPECIES_PALETTE,
            ax=ax,
        )
        ax.set_title("날개 길이 vs 몸무게")
        ax.set_xlabel("날개 길이(mm)")
        ax.set_ylabel("몸무게(g)")
        ax.legend(title="종(species)")
        return fig

    # Tab 2) 날개·무게 요약 - 표(DataGrid)
    # (설명) 필요한 컬럼만 골라서 + 한국어 컬럼명으로 출력
    @render.data_frame
    def fm_table():
        cols = ["species", "island", "flipper_length_mm", "body_mass_g", "sex"]
        cols = [c for c in cols if c in filtered_df().columns]
        view = rename_cols_kr(filtered_df()[cols])
        return render.DataGrid(view, filters=True)

    # Tab 3) 섬×종 요약 - 막대그래프
    # (설명)
    # - 섬별로 종 개수를 countplot으로 시각화
    # - 섬/종 정렬 순서 고정(ISLAND_ORDER, SPECIES_ORDER)
    # - 종 색상 고정(SPECIES_PALETTE)
    @render.plot
    def island_species_counts():
        fig, ax = plt.subplots()

        d = filtered_df().dropna(subset=["island", "species"])
        if d.empty:
            ax.set_title("데이터 없음")
            ax.set_xlabel("섬(island)")
            ax.set_ylabel("개수")
            return fig

        present_islands = set(d["island"].unique())
        island_order_present = [i for i in ISLAND_ORDER if i in present_islands]

        present_species = set(d["species"].unique())
        species_order_present = [s for s in SPECIES_ORDER if s in present_species]

        sns.countplot(
            data=d,
            x="island",
            order=island_order_present,
            hue="species",
            hue_order=species_order_present,
            palette=SPECIES_PALETTE,
            ax=ax,
        )
        ax.set_title("섬별 종별 개수")
        ax.set_xlabel("섬(island)")
        ax.set_ylabel("개수")
        ax.legend(title="종(species)")
        return fig

    # Tab 3) 섬×종 요약 - 교차표(DataGrid)
    # (설명)
    # - pd.crosstab: 섬(행)×종(열) 개수 집계
    # - reindex(fill_value=0): 없는 조합도 0으로 채워 표 형태 고정
    @render.data_frame
    def island_species_summary():
        d = filtered_df().dropna(subset=["island", "species"])
        if d.empty:
            return render.DataGrid(
                {"안내": ["필터 결과가 없어 피벗 테이블을 만들 수 없습니다."]},
                filters=False,
            )

        pivot = pd.crosstab(d["island"], d["species"])
        pivot = pivot.reindex(index=ISLAND_ORDER, columns=SPECIES_ORDER, fill_value=0)

        out = pivot.reset_index().rename(columns={"island": "섬(island)"})
        return render.DataGrid(out)


app = App(app_ui, server)