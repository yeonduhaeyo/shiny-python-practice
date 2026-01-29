from pathlib import Path
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from imblearn.over_sampling import RandomOverSampler
from imblearn.pipeline import Pipeline as ImbPipeline


# 경로/상수
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
MODELS_DIR = APP_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

TRAIN_CLEAN_PATH = DATA_DIR / "train_clean.csv"
TEST_PATH = DATA_DIR / "test.csv"
TEST_TARGET_PATH = DATA_DIR / "test_target.csv"

RESULTS_CSV_PATH = MODELS_DIR / "model_compare_results.csv"
BEST_MODEL_PATH = MODELS_DIR / "best_model.joblib"
BEST_MODEL_NAME_PATH = MODELS_DIR / "best_model_name.txt"
TEST_PRED_BEST_PATH = MODELS_DIR / "test_predictions_best.csv"

TARGET_COL = "passorfail"
ID_COL = "id"

RANDOM_STATE = 42
VALID_SIZE = 0.2
THRESHOLD = 0.5

BEST_BY = "valid_f1"  # or "valid_roc_auc"

# 이전 레슨에서 고정한 스키마 재사용
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
    "sleeve_temperature",
    "Coolant_temperature",
    "upper_mold_temp1", "upper_mold_temp2",
    "lower_mold_temp1", "lower_mold_temp2",
]

# 입력 정합성: 최소 규칙 재적용 (test/실시간 입력 대비)
def prepare_features_like_preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    preprocessing.py의 핵심 규칙을 test/실시간 입력에도 동일하게 적용하기 위한 최소 함수.
    - 스키마 고정(FEATURE_COLS)
    - 1449 플래그 → NaN
    - 비정상값 보정(molten_temp<=100, production_cycletime==0)
    - 최소 결측 규칙(tryshot_signal, molten_volume)
    - 범주형 string 고정
    """
    out = df.copy()

    # (1) 스키마 고정: 누락 컬럼은 NaN 생성
    for c in FEATURE_COLS:
        if c not in out.columns:
            out[c] = np.nan
    out = out[FEATURE_COLS].copy()

    # (2) 플래그(1449) → NaN
    for c in FLAG_1449_COLS:
        out.loc[out[c] == 1449, c] = np.nan

    # (3) 비정상값 처리
    out.loc[out["molten_temp"] <= 100, "molten_temp"] = np.nan

    m = (out["production_cycletime"] == 0)
    out.loc[m, "production_cycletime"] = out.loc[m, "facility_operation_cycleTime"]

    # (4) 최소 결측 규칙
    out["tryshot_signal"] = out["tryshot_signal"].astype("string").fillna("A")
    out["molten_volume"] = pd.to_numeric(out["molten_volume"], errors="coerce").fillna(-1)

    # (5) 범주형 → string
    for c in CATEGORICAL_COLS:
        out[c] = out[c].astype("string")

    return out


# 전처리기(ColumnTransformer)
def make_onehot_encoder_dense():
    """sklearn 버전 호환 + oversampler 안정성을 위해 dense 고정."""
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    """
    수치형: 결측(median) + 스케일링
    범주형: 결측(most_frequent) + 원핫
    """
    numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()

    categorical_features = []
    for c in X.columns:
        if c in CATEGORICAL_COLS:
            categorical_features.append(c)
    for c in X.columns:
        if c not in numeric_features and c not in categorical_features:
            categorical_features.append(c)

    num_pipe = ImbPipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    cat_pipe = ImbPipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", make_onehot_encoder_dense()),
    ])

    return ColumnTransformer(
        transformers=[
            ("num", num_pipe, numeric_features),
            ("cat", cat_pipe, categorical_features),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


# 평가용 유틸 함수
def evaluate(pipe, X_eval, y_eval) -> dict:
    """valid 평가(확률 기반: ROC-AUC 포함)."""
    proba = pipe.predict_proba(X_eval)[:, 1]
    pred = (proba >= THRESHOLD).astype(int)
    return {
        "accuracy": float(accuracy_score(y_eval, pred)),
        "precision": float(precision_score(y_eval, pred, zero_division=0)),
        "recall": float(recall_score(y_eval, pred, zero_division=0)),
        "f1": float(f1_score(y_eval, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_eval, proba)),
    }


def score_test(pipe, test_df, test_target_df):
    """test 예측 + test_target(id, passorfail) 조인 후 최종 스코어 산출."""
    if ID_COL not in test_df.columns:
        raise ValueError(f"'{ID_COL}' not found in test.csv")

    X_test = prepare_features_like_preprocess(test_df)
    proba = pipe.predict_proba(X_test)[:, 1]
    pred = (proba >= THRESHOLD).astype(int)

    pred_df = pd.DataFrame({ID_COL: test_df[ID_COL], "pred": pred, "proba": proba})
    merged = pred_df.merge(test_target_df[[ID_COL, TARGET_COL]], on=ID_COL, how="inner")
    if merged.empty:
        raise ValueError("[test] join 결과가 비었습니다. id 정합성 확인하세요.")

    y_true = merged[TARGET_COL].astype(int)
    y_pred = merged["pred"].astype(int)

    return merged, {
        "n_scored": int(len(merged)),
        "test_f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "test_accuracy": float(accuracy_score(y_true, y_pred)),
        "test_precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "test_recall": float(recall_score(y_true, y_pred, zero_division=0)),
    }

print("\n[1] train_clean.csv 로드")
if not TRAIN_CLEAN_PATH.exists():
    raise FileNotFoundError(f"not found: {TRAIN_CLEAN_PATH}")

df = pd.read_csv(TRAIN_CLEAN_PATH, encoding="utf-8-sig", low_memory=False)
print(f" - shape: {df.shape}")
if TARGET_COL not in df.columns:
    raise KeyError(f"target not found: {TARGET_COL}")

print("\n[2] X/y 구성 (라벨 정규화 없음 → int 고정)")
y = df[TARGET_COL].astype(int)
X = prepare_features_like_preprocess(df.drop(columns=[TARGET_COL], errors="ignore"))

print(f" - X shape: {X.shape}")
print(" - y ratio:")
print((y.value_counts() / len(y)).round(4).to_string())

print("\n[3] train/valid split (stratify)")
X_train, X_valid, y_train, y_valid = train_test_split(
    X, y, test_size=VALID_SIZE, random_state=RANDOM_STATE, stratify=y
)
print(f" - train: {X_train.shape}, valid: {X_valid.shape}")

print("\n[4] test/test_target 로드(있으면)")
has_test = TEST_PATH.exists() and TEST_TARGET_PATH.exists()
test_df = test_target = None
if has_test:
    test_df = pd.read_csv(TEST_PATH, low_memory=False)
    test_target = pd.read_csv(TEST_TARGET_PATH, low_memory=False)
    if ID_COL not in test_target.columns or TARGET_COL not in test_target.columns:
        raise ValueError(f"test_target must have columns: {ID_COL}, {TARGET_COL}")
    test_target[TARGET_COL] = test_target[TARGET_COL].astype(int)
    print(f" - test: {test_df.shape}, test_target: {test_target.shape}")
else:
    print(" - 없음 → test 평가는 스킵")

print("\n[5] 전처리기 + 오버샘플러 준비")
preprocessor = build_preprocessor(X_train)
sampler = RandomOverSampler(random_state=RANDOM_STATE)

print("\n[6] 모델 정의 (LR/DT/RF + XGB/LGBM)")
models = {
    "LogReg": LogisticRegression(max_iter=3000),
    "DT": DecisionTreeClassifier(random_state=RANDOM_STATE),
    "RF": RandomForestClassifier(n_estimators=600, random_state=RANDOM_STATE, n_jobs=-1),

    "XGB": XGBClassifier(
        n_estimators=400, max_depth=6, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9, reg_lambda=1.0,
        random_state=RANDOM_STATE, eval_metric="logloss", n_jobs=-1,
    ),
    "LGBM": LGBMClassifier(
        n_estimators=800, learning_rate=0.05, num_leaves=31,
        subsample=0.9, colsample_bytree=0.9,
        random_state=RANDOM_STATE, n_jobs=-1,
    ),
}
print(" - models:", list(models.keys()))

print("\n[7] 모델 학습/평가 시작")
results = []
best_name, best_score, best_pipe, best_test_merged = None, -1, None, None

for i, (name, clf) in enumerate(models.items(), start=1):
    print(f"\n[7-{i}] {name} 학습 중...")

    pipe = ImbPipeline(steps=[
        ("preprocess", preprocessor),
        ("oversample", sampler),
        ("model", clf),
    ])

    print(" - fit...")
    pipe.fit(X_train, y_train)
    print(" - fit done")

    print(" - valid evaluate...")
    valid_m = evaluate(pipe, X_valid, y_valid)
    row = {"model": name, **{f"valid_{k}": v for k, v in valid_m.items()}}

    if has_test:
        print(" - test evaluate...")
        merged, test_m = score_test(pipe, test_df, test_target)
        row.update(test_m)

    results.append(row)

    current = row.get(BEST_BY)
    print(f" - {BEST_BY}: {current:.6f}")

    if current > best_score:
        best_score, best_name, best_pipe = current, name, pipe
        if has_test:
            best_test_merged = merged
        print(f" - best 갱신: {best_name} ({BEST_BY}={best_score:.6f})")

print("\n[8] 결과 저장")
results_df = pd.DataFrame(results).sort_values(by=BEST_BY, ascending=False)
results_df.to_csv(RESULTS_CSV_PATH, index=False, encoding="utf-8-sig")
print(f" - saved results: {RESULTS_CSV_PATH}")

joblib.dump(best_pipe, BEST_MODEL_PATH)
BEST_MODEL_NAME_PATH.write_text(best_name, encoding="utf-8")
print(f" - saved best model: {BEST_MODEL_PATH}")
print(f" - saved best name : {BEST_MODEL_NAME_PATH}")

if has_test and isinstance(best_test_merged, pd.DataFrame):
    best_test_merged.to_csv(TEST_PRED_BEST_PATH, index=False, encoding="utf-8-sig")
    print(f" - saved best test preds: {TEST_PRED_BEST_PATH}")

print("\n[TOP 5]")
print(results_df.head(5).to_string(index=False))
print("\n[done]")
