# pages/page_appendix.py
from pathlib import Path
import json

import pandas as pd
from shiny import ui, module, render

import shared


# =========================
# tiny helpers (minimal)
# =========================
def _overview_df(df: pd.DataFrame) -> pd.DataFrame:
    total_cells = int(df.shape[0] * df.shape[1])
    miss_cells = int(df.isna().sum().sum())
    miss_ratio = round(miss_cells / total_cells, 6) if total_cells else 0.0
    return pd.DataFrame(
        [
            {"item": "shape", "value": f"{df.shape[0]} × {df.shape[1]}"},
            {"item": "missing_cells", "value": miss_cells},
            {"item": "missing_ratio", "value": miss_ratio},
        ]
    )


def _target_df(df: pd.DataFrame, target_col: str = "passorfail") -> pd.DataFrame:
    # KeyError('class') 방지: 항상 class/count/ratio 컬럼으로 만든다
    if target_col not in df.columns:
        return pd.DataFrame([{"class": f"{target_col} not found", "count": 0, "ratio": 0.0}])

    vc = df[target_col].value_counts(dropna=False)
    out = pd.DataFrame({"class": vc.index.astype(str), "count": vc.values.astype(int)})
    out["ratio"] = (out["count"] / len(df)).round(4)
    return out


def _na_top_df(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    s = df.isna().sum().sort_values(ascending=False)
    s = s[s > 0].head(top_n)
    if len(s) == 0:
        return pd.DataFrame([{"column": "남은 결측 없음", "na_count": 0}])
    return pd.DataFrame({"column": s.index.astype(str), "na_count": s.values.astype(int)})


def _load_summary():
    app_dir = Path(__file__).resolve().parents[1]  # pages/ -> app root
    p = app_dir / "data" / "preprocess_summary.json"
    if not p.exists():
        return None, "preprocess_summary.json 없음 → preprocessing.py 실행 후 생성됩니다."

    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None, "preprocess_summary.json 파싱 실패 → 파일을 직접 확인하세요."

    # 사람이 읽기 좋은 “문장 요약”
    raw_shape = d.get("raw_shape", ["?", "?"])
    clean_shape = d.get("clean_shape", ["?", "?"])
    removed = int(d.get("removed_bad_row_id_19327", 0))

    flag = d.get("flag_1449_to_na", {}) or {}
    flag_total = sum(int(v) for v in flag.values()) if isinstance(flag, dict) else 0

    molten_bad = int(d.get("molten_temp_le_100_to_na", 0))
    prod_fix = int(d.get("production_cycletime_zero_fix", 0))

    fills = d.get("fills", {}) or {}
    tryshot_fill = int(fills.get("tryshot_signal_na_to_A", 0))
    vol_fill = int(fills.get("molten_volume_na_to_minus1", 0))

    dropped = d.get("dropped_columns", []) or []
    dropped_txt = ", ".join(dropped) if dropped else "-"

    text = "\n".join(
        [
            f"- raw → clean: {raw_shape[0]}×{raw_shape[1]} → {clean_shape[0]}×{clean_shape[1]}",
            f"- 결측 과다 단일행 제거(id=19327): {removed}건",
            f"- 플래그 1449 → NaN: 총 {flag_total}셀",
            f"- molten_temp ≤ 100 → NaN: {molten_bad}건",
            f"- production_cycletime==0 보정: {prod_fix}건",
            f"- tryshot_signal 결측 → 'A': {tryshot_fill}건",
            f"- molten_volume 결측/비수치 → -1: {vol_fill}건",
            f"- drop columns: {dropped_txt}",
        ]
    )

    # 요약을 표로도 같이 제공(간단히)
    summary_tbl = pd.DataFrame(
        [
            {"metric": "raw_shape", "value": f"{raw_shape[0]}×{raw_shape[1]}"},
            {"metric": "clean_shape", "value": f"{clean_shape[0]}×{clean_shape[1]}"},
            {"metric": "removed(id=19327)", "value": removed},
            {"metric": "flag_1449_to_na(cells)", "value": flag_total},
            {"metric": "molten_temp<=100_to_na(rows)", "value": molten_bad},
            {"metric": "prod_cycletime_zero_fix(rows)", "value": prod_fix},
            {"metric": "tryshot_na_to_A(rows)", "value": tryshot_fill},
            {"metric": "molten_volume_na_to_-1(rows)", "value": vol_fill},
        ]
    )

    return summary_tbl, text


# =========================
# UI
# =========================
@module.ui
def page_appendix_ui():
    return ui.nav_panel(
        "부록",
        ui.h3("부록"),
        ui.p("이번 레슨에서는 Raw(train.csv)와 1차 정제(train_clean.csv)를 비교하고, 전처리 요약을 별도 탭에서 확인합니다."),
        ui.navset_tab(
            # 탭 1) Raw vs Clean 비교 (한 화면에서 좌우 비교)
            ui.nav_panel(
                "Raw vs Clean",
                ui.h4("요약(overview)"),
                ui.layout_columns(
                    ui.card(ui.card_header("Raw"), ui.output_data_frame("raw_overview_tbl")),
                    ui.card(ui.card_header("Clean"), ui.output_data_frame("clean_overview_tbl")),
                    col_widths=[6, 6],
                ),
                ui.h4("타깃 분포(passorfail)"),
                ui.layout_columns(
                    ui.card(ui.card_header("Raw"), ui.output_data_frame("raw_target_tbl")),
                    ui.card(ui.card_header("Clean"), ui.output_data_frame("clean_target_tbl")),
                    col_widths=[6, 6],
                ),
                ui.h4("결측 Top 10"),
                ui.layout_columns(
                    ui.card(ui.card_header("Raw"), ui.output_data_frame("raw_na_tbl")),
                    ui.card(ui.card_header("Clean"), ui.output_data_frame("clean_na_tbl")),
                    col_widths=[6, 6],
                ),
                ui.h4("head(12)"),
                ui.layout_columns(
                    ui.card(ui.card_header("Raw"), ui.output_data_frame("raw_head_tbl")),
                    ui.card(ui.card_header("Clean"), ui.output_data_frame("clean_head_tbl")),
                    col_widths=[6, 6],
                ),
            ),
            # 탭 2) 전처리 요약
            ui.nav_panel(
                "전처리 요약",
                ui.card(
                    ui.card_header("preprocess_summary.json (요약)"),
                    ui.output_text_verbatim("summary_txt"),
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header("요약 표"),
                        ui.output_data_frame("summary_tbl"),
                    ),
                    ui.card(
                        ui.card_header("남은 결측 Top 10 (Clean)"),
                        ui.output_data_frame("clean_na_tbl2"),
                    ),
                    col_widths=[6, 6],
                ),
                ui.p("※ 모델 리포트(성능/지표/혼동행렬)는 5-3에서 이 탭에 확장합니다."),
            ),
        ),
    )


# =========================
# Server
# =========================
@module.server
def page_appendix_server(input, output, session):
    # Raw / Clean 객체는 shared에서 제공한다고 가정
    df_raw = shared.df_raw
    df_clean = shared.df_clean

    # ----- Raw vs Clean: overview
    @output
    @render.data_frame
    def raw_overview_tbl():
        return _overview_df(df_raw)

    @output
    @render.data_frame
    def clean_overview_tbl():
        return _overview_df(df_clean)

    # ----- target
    @output
    @render.data_frame
    def raw_target_tbl():
        return _target_df(df_raw, "passorfail")

    @output
    @render.data_frame
    def clean_target_tbl():
        return _target_df(df_clean, "passorfail")

    # ----- NA top
    @output
    @render.data_frame
    def raw_na_tbl():
        return _na_top_df(df_raw, 10)

    @output
    @render.data_frame
    def clean_na_tbl():
        return _na_top_df(df_clean, 10)

    # ----- head
    @output
    @render.data_frame
    def raw_head_tbl():
        return df_raw.head(12)

    @output
    @render.data_frame
    def clean_head_tbl():
        return df_clean.head(12)

    # ----- Summary tab
    @output
    @render.text
    def summary_txt():
        _, text = _load_summary()
        return text

    @output
    @render.data_frame
    def summary_tbl():
        tbl, _ = _load_summary()
        if tbl is None:
            return pd.DataFrame([{"metric": "status", "value": "summary json 없음"}])
        return tbl

    @output
    @render.data_frame
    def clean_na_tbl2():
        return _na_top_df(df_clean, 10)
