from pathlib import Path
import json

import numpy as np
import pandas as pd

APP_DIR = Path(__file__).resolve().parent
RAW_PATH = APP_DIR / "data" / "train.csv"
CLEAN_PATH = APP_DIR / "data" / "train_clean.csv"
SUMMARY_PATH = APP_DIR / "data" / "preprocess_summary.json"

TARGET_COL = "passorfail"

# [1] 데이터 로딩
print("\n[1] train.csv 로드")
print(f" - path: {RAW_PATH}")

if not RAW_PATH.exists():
    raise FileNotFoundError(f"train.csv not found: {RAW_PATH}")

try:
    df = pd.read_csv(RAW_PATH, encoding="utf-8-sig", low_memory=False)
    print(" - encoding: utf-8-sig")
except UnicodeDecodeError:
    df = pd.read_csv(RAW_PATH, encoding="cp949", low_memory=False)
    print(" - encoding: cp949 (fallback)")

raw_shape = list(df.shape)
print(f" - df shape: {df.shape}")

# [2] head / info 확인
print("\n[2] head / info 확인")
print(df.head())
print(df.info())

# [3] 타깃 분포 확인(passorfail)
print("\n[3] 타깃 분포(passorfail)")
if TARGET_COL not in df.columns:
    raise KeyError(f"타깃 컬럼이 없습니다: {TARGET_COL}")

vc = df[TARGET_COL].value_counts(dropna=False)
ratio = (vc / len(df)).round(4)
print(vc)
print(ratio)

# [4] 결측 과다 단일 행 제거(id=19327)
print("\n[4] 결측 과다 단일 행 제거(id=19327)")

removed_rows = 0
if "id" in df.columns:
    bad = df["id"] == 19327
    if bad.any():
        print(" - 대상 행(요약):")
        print(df.loc[bad].head(1))
        print(" - 결측 열 수:", df.loc[bad].isna().sum(axis=1).values)

        before = len(df)
        df = df.loc[~bad].copy()
        removed_rows = before - len(df)

print(f" - removed rows: {removed_rows}")
print(f" - df shape: {df.shape}")

# [5] 스키마 고정(가용 변수만 유지)
print("\n[5] 스키마 고정(가용 변수만 유지)")

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

DROP_COLS = [
    "line", "name", "mold_name", "emergency_stop",
    "date", "time", "registration_time",
    "heating_furnace",
    "upper_mold_temp3", "lower_mold_temp3",
    "id",
]

drop_exist = [c for c in DROP_COLS if c in df.columns]
if drop_exist:
    df = df.drop(columns=drop_exist)

keep_cols = [c for c in FEATURE_COLS + [TARGET_COL] if c in df.columns]
df = df[keep_cols].copy()

print(f" - after schema fix: {df.shape}")
print(" - columns:", list(df.columns))

# [6] 플래그(1449) 처리 → NaN
print("\n[6] 플래그(1449) 처리 → NaN")

FLAG_1449_COLS = [
    "sleeve_temperature",
    "Coolant_temperature",
    "upper_mold_temp1", "upper_mold_temp2",
    "lower_mold_temp1", "lower_mold_temp2",
]

flag_1449_counts = {}
for c in FLAG_1449_COLS:
    if c in df.columns:
        cnt = int((df[c] == 1449).sum())
        flag_1449_counts[c] = cnt
        if cnt > 0:
            df.loc[df[c] == 1449, c] = np.nan
        print(f" - {c} : {cnt} 개 → NaN")

print(" - done")

# [7] 비정상값 처리
print("\n[7] 비정상값 처리(대표 케이스)")

molten_temp_bad_cnt = 0
if "molten_temp" in df.columns:
    m = df["molten_temp"] <= 100
    molten_temp_bad_cnt = int(m.sum())
    print(f" - molten_temp가 100 이하인 데이터 수 : {molten_temp_bad_cnt} 개")
    if molten_temp_bad_cnt > 0:
        df.loc[m, "molten_temp"] = np.nan

prod_cycle_fix_cnt = 0
if "production_cycletime" in df.columns and "facility_operation_cycleTime" in df.columns:
    m = df["production_cycletime"] == 0
    prod_cycle_fix_cnt = int(m.sum())
    print(f" - production_cycletime이 0인 데이터 수 : {prod_cycle_fix_cnt} 개")
    if prod_cycle_fix_cnt > 0:
        df.loc[m, "production_cycletime"] = df.loc[m, "facility_operation_cycleTime"]

print(" - done")

# [8] 최소 결측 규칙 적용
print("\n[8] 최소 결측 규칙 적용")

tryshot_fill_cnt = 0
if "tryshot_signal" in df.columns:
    tryshot_fill_cnt = int(df["tryshot_signal"].isna().sum())
    print(f" - tryshot_signal 결측 수 : {tryshot_fill_cnt} 개")
    print(" - tryshot_signal 결측값 → 'A'로 대치")
    df["tryshot_signal"] = df["tryshot_signal"].astype("string").fillna("A")

molten_volume_fill_cnt = 0
if "molten_volume" in df.columns:
    vol = pd.to_numeric(df["molten_volume"], errors="coerce")
    molten_volume_fill_cnt = int(vol.isna().sum())
    print(f" - molten_volume 결측/비수치 수 : {molten_volume_fill_cnt} 개")
    print(" - molten_volume 결측값 → -1로 대치")
    df["molten_volume"] = vol.fillna(-1)

print(" - done")

# [9] 타입 정리(범주형 → string)
print("\n[9] 타입 정리(범주형 → string)")

CATEGORICAL_COLS = ["mold_code", "EMS_operation_time", "working", "tryshot_signal"]
for c in CATEGORICAL_COLS:
    if c in df.columns:
        df[c] = df[c].astype("string")

print(" - categorical dtypes:")
for c in CATEGORICAL_COLS:
    if c in df.columns:
        print(f"   - {c}: {df[c].dtype}")

# [10] 전처리 결과 점검 + 저장(+요약 JSON 저장)
print("\n[10] 전처리 결과 점검 + 저장(+요약 JSON 저장)")

print(" - df shape:", df.shape)

na_top10 = df.isna().sum().sort_values(ascending=False).head(10)
print("\n - 결측 상위 10개:")
print(na_top10)

print("\n - 타깃 분포 재확인:")
vc2 = df[TARGET_COL].value_counts(dropna=False)
ratio2 = (vc2 / len(df)).round(4)
print(vc2)
print(ratio2)

summary = {
    "raw_shape": raw_shape,
    "clean_shape": list(df.shape),
    "removed_bad_row_id_19327": removed_rows,
    "dropped_columns": drop_exist,
    "flag_1449_to_na": flag_1449_counts,
    "molten_temp_le_100_to_na": molten_temp_bad_cnt,
    "production_cycletime_zero_fix": prod_cycle_fix_cnt,
    "fills": {
        "tryshot_signal_na_to_A": tryshot_fill_cnt,
        "molten_volume_na_to_minus1": molten_volume_fill_cnt,
    },
    "remaining_na_top10": {k: int(v) for k, v in na_top10.to_dict().items()},
    "target_ratio": {str(k): float(v) for k, v in ratio2.to_dict().items()},
}

print(f"\n - save summary json to: {SUMMARY_PATH}")
SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(" - saved summary json")

print(f"\n - save csv to: {CLEAN_PATH}")
df.to_csv(CLEAN_PATH, index=False, encoding="utf-8-sig")
print(" - saved csv")
print(" - done")