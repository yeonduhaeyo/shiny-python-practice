from shiny import ui, module, render
import pandas as pd
from shared import df


@module.ui
def page_data_ui():
    return ui.nav_panel(
        "데이터 요약",
        ui.h3("데이터 요약"),

        # 1) Value Box: 핵심 메타
        ui.layout_column_wrap(
            ui.value_box("행 수", ui.output_text("n_rows")),
            ui.value_box("열 수", ui.output_text("n_cols")),
            ui.value_box("시도 개수", ui.output_text("n_sido")),
            ui.value_box("총 등록대수(계)", ui.output_text("total_cnt")),
            width=1/4,
        ),

        # 2) 데이터 미리보기
        ui.card(
            ui.card_header("데이터 미리보기"),
            ui.output_data_frame("head_tbl"),
        ),

        # 6) 레이아웃 정리: 좌(데이터 사전) / 우(요약 2장 스택)
        ui.layout_columns(
            
            # 3) 데이터 사전
            ui.card(
                ui.card_header("데이터 사전"),
                ui.output_data_frame("dict_tbl"),
            ),
            ui.div(
                # 4) 수치형 요약
                ui.card(
                    ui.card_header("수치형 요약"),
                    ui.output_data_frame("desc_tbl"),
                ),
                
                # 5) 범주형 요약
                ui.card(
                    ui.card_header("범주형 요약"),
                    ui.output_data_frame("cat_summary_tbl"),
                ),
                class_="vstack gap-3",
            ),
            col_widths=[4, 8],
        ),
    )


@module.server
def page_data_server(input, output, session):

    # 1) Value Box 출력
    @render.text
    def n_rows():
        return f"{df.shape[0]:,}"

    @render.text
    def n_cols():
        return f"{df.shape[1]:,}"

    @render.text
    def n_sido():
        return f"{df['시도'].nunique():,}" if "시도" in df.columns else "-"

    @render.text
    def total_cnt():
        return f"{int(df['계'].sum()):,}" if "계" in df.columns else "-"

    # 2) 데이터 미리보기
    @render.data_frame
    def head_tbl():
        out = df.head(10)
        return render.DataGrid(out, width="100%")

    # 3) 데이터 사전
    @render.data_frame
    def dict_tbl():
        col_desc = {
            "시군구별": "원본 지역 문자열(예: '서울 중구')",
            "시도": "시군구별에서 분리한 시도(예: 서울, 경기, 경북)",
            "시군구": "시군구별에서 분리한 시/군/구(예: 중구, 성남시 분당구)",
            "연료별": "연료 구분(예: 전기)",
            "용도별": "용도 구분(사업용/비사업용)",
            "승용": "승용 등록대수",
            "승합": "승합 등록대수",
            "화물": "화물 등록대수",
            "특수": "특수 등록대수",
            "계": "합계(승용+승합+화물+특수)",
        }

        out = pd.DataFrame(
            {
                "컬럼": df.columns,
                "dtype": df.dtypes.astype(str).values,
                "설명": [col_desc.get(c, "") for c in df.columns],
            }
        )
        return render.DataGrid(out, width="100%")

    # 4) 수치형 요약
    @render.data_frame
    def desc_tbl():
        num_df = df.select_dtypes(include="number")
        if num_df.shape[1] == 0:
            return pd.DataFrame({"message": ["수치형 컬럼이 없어 요약 통계가 없습니다."]})

        desc = num_df.describe().T.reset_index().rename(columns={"index": "변수"})
        for c in ["mean", "std"]:
            if c in desc.columns:
                desc[c] = desc[c].round(1)

        return render.DataGrid(desc, width="100%")

    # 5) 범주형 요약
    @render.data_frame
    def cat_summary_tbl():
        cat_cols = df.select_dtypes(exclude="number").columns

        rows = []
        for col in cat_cols:
            vc = df[col].value_counts(dropna=False)
            rows.append(
                {
                    "컬럼": col,
                    "고유값 수": int(df[col].nunique(dropna=True)),
                    "최빈값": str(vc.index[0]) if len(vc) else "",
                    "빈도": int(vc.iloc[0]) if len(vc) else 0,
                }
            )

        if not rows:
            return pd.DataFrame({"message": ["범주형 컬럼이 없습니다."]})

        return render.DataGrid(pd.DataFrame(rows), width="100%")
