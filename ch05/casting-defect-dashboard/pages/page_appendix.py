import pandas as pd
from shiny import ui, module, render

import shared

TARGET_COL = "passorfail"
BEST_BY = "valid_f1"

FEATURE_COLS = [
    "count", "mold_code", "working", "tryshot_signal",
    "facility_operation_cycleTime", "production_cycletime",
    "molten_volume", "molten_temp", "EMS_operation_time",
    "sleeve_temperature", "cast_pressure", "biscuit_thickness",
    "low_section_speed", "high_section_speed", "physical_strength",
    "upper_mold_temp1", "upper_mold_temp2",
    "lower_mold_temp1", "lower_mold_temp2",
    "Coolant_temperature",
]
CATEGORICAL_COLS = ["mold_code", "EMS_operation_time", "working", "tryshot_signal"]
FLAG_1449_COLS = [
    "sleeve_temperature", "Coolant_temperature",
    "upper_mold_temp1", "upper_mold_temp2",
    "lower_mold_temp1", "lower_mold_temp2",
]

def fmt3(x):
    try:
        return f"{float(x):.3f}"
    except Exception:
        return "-"


@module.ui
def page_appendix_ui():
    return ui.nav_panel(
        "부록",
        ui.div(
            {"class": "container-fluid p-0"},

            ui.h4({"class": "mb-3"}, "전처리 요약"),
            ui.layout_columns(
                ui.output_ui("before_after_ui"),
                col_widths=[12],
                class_="mb-3",
            ),
            ui.card(ui.card_header("전처리 규칙 상세"), ui.output_ui("preprocess_rules_ui"), class_="mb-4"),

            ui.hr({"class": "my-4"}),

            ui.h4({"class": "mb-3"}, "모델 성능 리포트"),
            ui.layout_columns(
                ui.output_ui("best_model_box"),
                ui.output_ui("valid_f1_box"),
                ui.output_ui("test_f1_box"),
                ui.output_ui("test_acc_box"),
                col_widths=[3, 3, 3, 3],
                class_="mb-3",
            ),
            ui.card(ui.card_header("모델 비교 결과"), ui.output_ui("compare_tbl_ui"), class_="mb-3"),
        ),
    )


@module.server
def page_appendix_server(input, output, session):
    preprocess_summary = shared.preprocess_summary
    compare_df = shared.model_compare_results
    best_name = shared.best_model_name

    # helpers (server-local)
    def preprocess_rules_items():
        dropped = (preprocess_summary or {}).get("dropped_columns", []) or []
        return [
            ("1. 스키마 고정",
             f"입력 컬럼을 FEATURE_COLS {len(FEATURE_COLS)}개로 고정하고, 누락 컬럼은 NaN으로 생성해 일관성을 유지합니다."),
            ("2. 센서 오류 플래그",
             f"값이 1449인 경우 오류로 간주해 NaN 처리합니다. 대상: {', '.join(FLAG_1449_COLS)}"),
            ("3. 용탕 온도 비정상",
             "molten_temp ≤ 100이면 측정 오류로 판단해 NaN 처리합니다."),
            ("4. 생산 사이클타임 보정",
             "production_cycletime==0이면 facility_operation_cycleTime으로 대체합니다."),
            ("5. 트라이샷 결측",
             "tryshot_signal 결측은 기본값 'A'로 대체합니다(입력 누락 방어)."),
            ("6. 용탕 부피 결측",
             "molten_volume 결측/비수치 값은 -1로 대체합니다(결측 신호 반영)."),
            ("7. 범주형 타입 고정",
             f"범주형은 string으로 변환해 인코딩 안정성을 확보합니다. 대상: {', '.join(CATEGORICAL_COLS)}"),
            ("8. 제거된 컬럼",
             f"전처리 과정에서 제거된 컬럼: {len(dropped)}개 → {', '.join(dropped) if dropped else '-'}"),
        ]

    def best_row_from_compare(df: pd.DataFrame | None, model_name: str):
        if df is None or df.empty:
            return None
        if "model" not in df.columns:
            return None
        m = df["model"].astype(str) == str(model_name)
        if not m.any():
            return None
        return df.loc[m].iloc[0]

    def get_metric(row, col):
        if row is None:
            return "-"
        if col not in row.index:
            return "-"
        return fmt3(row[col])

    def compare_table_html(df: pd.DataFrame | None):
        if df is None:
            return ui.p({"class": "text-muted mb-0"}, "모델 비교 결과 파일이 없습니다.")

        cols = [c for c in [
            "model",
            "valid_f1", "valid_accuracy", "valid_precision", "valid_recall",
            "test_f1", "test_accuracy", "test_precision", "test_recall",
        ] if c in df.columns]

        out = df[cols].copy() if cols else df.copy()
        out = out.head(10)

        for c in out.columns:
            if c == "model":
                continue
            if pd.api.types.is_numeric_dtype(out[c]):
                out[c] = out[c].map(lambda v: fmt3(v) if pd.notna(v) else "-")

        col_kr = {
            "model": "모델",
            "valid_f1": "검증 F1",
            "valid_accuracy": "검증 정확도",
            "valid_precision": "검증 정밀도",
            "valid_recall": "검증 재현율",
            "test_f1": "테스트 F1",
            "test_accuracy": "테스트 정확도",
            "test_precision": "테스트 정밀도",
            "test_recall": "테스트 재현율",
        }

        headers = [col_kr.get(c, c) for c in out.columns]
        rows = out.astype(str).values.tolist()

        return ui.tags.table(
            {"class": "table table-sm table-hover mb-0"},
            ui.tags.thead({"class": "table-light"}, ui.tags.tr(*[ui.tags.th(h) for h in headers])),
            ui.tags.tbody(*[ui.tags.tr(*[ui.tags.td(c) for c in r]) for r in rows]),
        )

    # ---- precompute ----
    best_row = best_row_from_compare(compare_df, best_name)

    # outputs
    @render.ui
    def before_after_ui():
        if not preprocess_summary:
            return ui.p({"class": "text-muted mb-0"}, "preprocess_summary.json 파일이 없어 전처리 전/후 통계를 확인할 수 없습니다.")

        raw_shape = preprocess_summary.get("raw_shape")
        clean_shape = preprocess_summary.get("clean_shape")
        if not raw_shape or not clean_shape or len(raw_shape) != 2 or len(clean_shape) != 2:
            return ui.p({"class": "text-muted mb-0"}, "raw_shape/clean_shape 정보가 없어 전처리 전/후 통계를 확인할 수 없습니다.")

        before_info = f"{raw_shape[0]:,}행 × {raw_shape[1]}컬럼"
        after_info = f"{clean_shape[0]:,}행 × {clean_shape[1]}컬럼"

        try:
            row_delta = int(clean_shape[0]) - int(raw_shape[0])
            col_delta = int(clean_shape[1]) - int(raw_shape[1])
            delta_info = f"행: {row_delta:+,} / 컬럼: {col_delta:+}"
        except Exception:
            delta_info = "-"

        return ui.layout_columns(
            ui.value_box("전처리 전", before_info, "원본 데이터", theme="bg-light"),
            ui.value_box("전처리 후", after_info, "최종 학습 데이터", theme="bg-light"),
            ui.value_box("변화량", delta_info, "전처리 효과", theme="bg-light"),
            col_widths=[4, 4, 4],
        )

    @render.ui
    def preprocess_rules_ui():
        rules = preprocess_rules_items()
        cards = [ui.card(ui.card_header(title), ui.p({"class": "mb-0"}, text), class_="mb-2") for (title, text) in rules]
        return ui.div(*cards)

    @render.ui
    def best_model_box():
        show = best_name if best_name else "-"
        return ui.value_box("최우수 모델", show, f"검증 {BEST_BY} 기준 선정", theme="primary")

    @render.ui
    def valid_f1_box():
        return ui.value_box("검증 F1 Score", get_metric(best_row, "valid_f1"), "Validation Set", theme="info")

    @render.ui
    def test_f1_box():
        return ui.value_box("테스트 F1 Score", get_metric(best_row, "test_f1"), "Test Set", theme="success")

    @render.ui
    def test_acc_box():
        return ui.value_box("테스트 정확도", get_metric(best_row, "test_accuracy"), "Test Accuracy", theme="success")

    @render.ui
    def compare_tbl_ui():
        return compare_table_html(compare_df)
