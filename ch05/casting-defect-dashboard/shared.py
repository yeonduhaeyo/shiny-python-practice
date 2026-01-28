from pathlib import Path
import pandas as pd

app_dir = Path(__file__).resolve().parent
data_dir = app_dir / "data"

train_path = data_dir / "train.csv"
clean_path = data_dir / "train_clean.csv"

if not train_path.exists():
    raise FileNotFoundError(f"train.csv not found: {train_path}")
if not clean_path.exists():
    raise FileNotFoundError(
        f"train_clean.csv not found: {clean_path}\n"
        f"→ 먼저 preprocessing.py를 실행해 train_clean.csv를 생성하세요."
    )

df_raw = pd.read_csv(train_path, encoding="utf-8-sig", low_memory=False)
df_clean = pd.read_csv(clean_path, encoding="utf-8-sig", low_memory=False)

