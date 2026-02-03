from pathlib import Path
import pandas as pd
import joblib

app_dir = Path(__file__).resolve().parent
data_dir = app_dir / "data"
models_dir = app_dir / "models"

train_path = data_dir / "train.csv"
clean_path = data_dir / "train_clean.csv"
best_model_path = models_dir / "best_model.joblib"

if not train_path.exists():
    raise FileNotFoundError(f"train.csv not found: {train_path}")

if not clean_path.exists():
    raise FileNotFoundError(
        f"train_clean.csv not found: {clean_path}\n"
        f"→ 먼저 preprocessing.py를 실행해 train_clean.csv를 생성하세요."
    )

df_raw = pd.read_csv(train_path, encoding="utf-8-sig", low_memory=False)
df_clean = pd.read_csv(clean_path, encoding="utf-8-sig", low_memory=False)

model = None
model_load_err = None

try:
    if not best_model_path.exists():
        model_load_err = f"best_model.joblib not found: {best_model_path}"
        print(model_load_err)
    else:
        model = joblib.load(best_model_path)
        print("모델 로드 완료")
except Exception as e:
    model_load_err = f"모델 로드 실패: {e}"
    print(model_load_err)
