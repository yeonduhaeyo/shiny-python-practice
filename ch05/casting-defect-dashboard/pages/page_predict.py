from pathlib import Path

from shiny import ui, render, reactive, module
import pandas as pd

from shared import model, model_load_err


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

FEATURE_KR = {
    "count":                        "생산 횟수",
    "mold_code":                    "금형 코드",
    "working":                      "작업 여부",
    "tryshot_signal":               "트라이샷 신호",
    "facility_operation_cycleTime": "설비 가동 사이클타임",
    "production_cycletime":         "생산 사이클타임",
    "molten_volume":                "용탕 부피",
    "molten_temp":                  "용탕 온도 (℃)",
    "EMS_operation_time":           "EMS 작동시간",
    "sleeve_temperature":           "슬리브 온도 (℃)",
    "cast_pressure":                "주조 압력 (bar)",
    "biscuit_thickness":            "비스킷 두께",
    "low_section_speed":            "저속 구간 속도",
    "high_section_speed":           "고속 구간 속도",
    "physical_strength":            "형체력",
    "upper_mold_temp1":             "상형 온도1 (℃)",
    "upper_mold_temp2":             "상형 온도2 (℃)",
    "lower_mold_temp1":             "하형 온도1 (℃)",
    "lower_mold_temp2":             "하형 온도2 (℃)",
    "Coolant_temperature":          "냉각수 온도 (℃)",
}


def build_input_df_from_ui(input) -> pd.DataFrame:
    tryshot_signal = "T" if input.tryshot_check() else "A"

    row = {
        "molten_temp": input.molten_temp(),
        "molten_volume": input.molten_volume(),
        "sleeve_temperature": input.sleeve_temperature(),
        "EMS_operation_time": str(input.EMS_operation_time()),
        "cast_pressure": input.cast_pressure(),
        "low_section_speed": input.low_section_speed(),
        "high_section_speed": input.high_section_speed(),
        "physical_strength": input.physical_strength(),
        "biscuit_thickness": input.biscuit_thickness(),
        "upper_mold_temp1": input.upper_mold_temp1(),
        "upper_mold_temp2": input.upper_mold_temp2(),
        "lower_mold_temp1": input.lower_mold_temp1(),
        "lower_mold_temp2": input.lower_mold_temp2(),
        "Coolant_temperature": input.coolant_temp(),
        "mold_code": str(input.mold_code()),
        "working": str(input.working()),
        "count": input.count(),
        "facility_operation_cycleTime": input.facility_operation_cycleTime(),
        "production_cycletime": input.production_cycletime(),
        "tryshot_signal": tryshot_signal,
    }

    X = pd.DataFrame([row]).reindex(columns=FEATURE_COLS)

    if list(X.columns) != FEATURE_COLS:
        raise ValueError("입력 DF 컬럼이 FEATURE_COLS와 일치하지 않습니다.")

    for c in CATEGORICAL_COLS:
        X[c] = X[c].astype("string")

    X["count"] = pd.to_numeric(X["count"], errors="raise").astype(int)

    numeric_cols = [c for c in FEATURE_COLS if c not in CATEGORICAL_COLS and c != "count"]
    for c in numeric_cols:
        X[c] = pd.to_numeric(X[c], errors="coerce")

    nan_cols = X.columns[X.isna().any()].tolist()
    if nan_cols:
        raise ValueError(f"수치 변환 실패/결측 발생 컬럼: {nan_cols}")

    return X


def process_card(title: str, inputs: list):
    return ui.card(
        ui.card_header(title),
        ui.accordion(ui.accordion_panel("변수 입력", *inputs), open=False),
        class_="mb-2",
    )


def page_layout():
    return ui.page_fluid(
        ui.card(
            ui.card_header("예측 결과"),
            ui.output_ui("pred_result"),
            ui.input_action_button(
                "btn_predict",
                "예측 실행",
                class_="btn-lg btn-block w-100 mt-2",
            ),
            class_="mb-3",
        ),

        ui.layout_columns(
            process_card(
                "1) 용탕 준비 및 가열",
                [
                    ui.input_slider("molten_temp", "용탕 온도 (℃)", 70, 750, 693),
                    ui.input_slider("molten_volume", "용탕 부피", -1, 600, 102),
                ],
            ),
            process_card(
                "2) 반고체 슬러리 제조",
                [
                    ui.input_slider("sleeve_temperature", "슬리브 온도 (℃)", 20, 1000, 459),
                    ui.input_select("EMS_operation_time", "EMS 작동시간", [3, 6, 23, 25], selected=23),
                ],
            ),
            process_card(
                "3) 사출 & 금형 충전",
                [
                    ui.input_slider("cast_pressure", "주조 압력 (bar)", 40, 370, 331),
                    ui.input_slider("low_section_speed", "저속 구간 속도", 0, 200, 110, step=1),
                    ui.input_slider("high_section_speed", "고속 구간 속도", 0, 400, 112, step=1),
                    ui.input_slider("physical_strength", "형체력", 0, 750, 703),
                    ui.input_slider("biscuit_thickness", "비스킷 두께", 0, 450, 42),
                ],
            ),
            process_card(
                "4) 응고",
                [
                    ui.input_slider("upper_mold_temp1", "상형 온도1 (℃)", 10, 400, 167),
                    ui.input_slider("upper_mold_temp2", "상형 온도2 (℃)", 10, 250, 125),
                    ui.input_slider("lower_mold_temp1", "하형 온도1 (℃)", 10, 400, 290),
                    ui.input_slider("lower_mold_temp2", "하형 온도2 (℃)", 10, 550, 176),
                    ui.input_slider("coolant_temp", "냉각수 온도 (℃)", 0, 50, 38),
                ],
            ),
            process_card(
                "기타) 전체 과정 관여 변수",
                [
                    ui.input_select("mold_code", "금형 코드", ["8412", "8573", "8600", "8722", "8917"], selected="8722"),
                    ui.input_select("working", "작업 여부", ["가동", "정지"], selected="가동"),
                    ui.input_numeric("count", "생산 횟수", min=1, value=95),
                    ui.input_slider("facility_operation_cycleTime", "설비 가동 사이클타임", 60, 500, 120),
                    ui.input_slider("production_cycletime", "생산 사이클타임", 60, 500, 119),
                    ui.input_checkbox("tryshot_check", "트라이샷 여부", value=False),
                ],
            ),
            fill=True,
        ),

        ui.hr(),

        ui.card(
            ui.card_header("입력된 변수 값"),
            ui.accordion(
                ui.accordion_panel(
                    "입력값 요약 보기",
                    ui.output_ui("input_summary_default"),
                    ui.output_data_frame("input_summary_grid"),
                ),
                open=False,
            ),
            class_="mb-3",
        ),
    )


@module.ui
def page_predict_ui():
    return ui.nav_panel("불량 예측", page_layout())


@module.server
def page_predict_server(input, output, session):
    X_input_state = reactive.Value(None)
    err_state = reactive.Value(None)
    pred_state = reactive.Value(None)
    proba_state = reactive.Value(None)

    @render.ui
    def input_summary_default():
        if input.btn_predict() == 0:
            return ui.div("예측 실행 후 입력값 요약이 표시됩니다.")
        return ui.div()

    @reactive.effect
    @reactive.event(input.btn_predict)
    def _run_predict():
        if model is None:
            msg = model_load_err or "모델이 로드되지 않았습니다."
            err_state.set(msg)
            X_input_state.set(None)
            pred_state.set(None)
            proba_state.set(None)
            return

        try:
            X = build_input_df_from_ui(input)
            X_input_state.set(X)

            proba = float(model.predict_proba(X)[:, 1][0])
            pred = int(proba >= 0.5)

            pred_state.set(pred)
            proba_state.set(proba)
            err_state.set(None)

        except Exception as e:
            err_state.set(str(e))
            X_input_state.set(None)
            pred_state.set(None)
            proba_state.set(None)

    @render.ui
    def pred_result():
        if input.btn_predict() == 0:
            return ui.value_box(
                "예측 결과",
                "대기 중",
                "입력값 설정 후 아래 버튼을 누르세요.",
                theme="bg-light",
            )

        err = err_state.get()
        if err:
            return ui.value_box("예측 결과", "오류 발생", err, theme="danger")

        pred = pred_state.get()
        proba = proba_state.get()
        if pred is None or proba is None:
            return ui.value_box("예측 결과", "처리 중", "다시 시도하세요.", theme="bg-light")

        if pred == 0:
            return ui.value_box("예측 결과", "✔  PASS", f"불량 확률: {proba:.2%}", theme="success")

        return ui.value_box("예측 결과", "✖  FAIL", f"불량 확률: {proba:.2%}", theme="danger")

    @render.data_frame
    @reactive.event(input.btn_predict)
    def input_summary_grid():
        err = err_state.get()
        if err:
            df = pd.DataFrame({"메시지": [f"입력/예측 실패: {err}"]})
            return render.DataGrid(df, width="100%", height=260, summary=False, filters=False)

        X = X_input_state.get()
        if X is None:
            df = pd.DataFrame({"메시지": ["예측 실행 후 입력값 요약이 표시됩니다."]})
            return render.DataGrid(df, width="100%", height=260, summary=False, filters=False)

        s = X.iloc[0]
        view_df = pd.DataFrame(
            {
                "변수명": [FEATURE_KR.get(c, c) for c in s.index],
                "입력값": s.values.tolist(),
            }
        )

        return render.DataGrid(
            view_df,
            width="100%",
            height=320,
            summary=False,
            filters=False,
            selection_mode="none",
        )