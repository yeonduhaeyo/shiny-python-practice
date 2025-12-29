from pathlib import Path
import pandas as pd

APP_DIR = Path(__file__).resolve().parent
RAW_PATH = APP_DIR / "data" / "ev_car.csv"

try:
    df_raw = pd.read_csv(RAW_PATH, encoding="utf-8-sig")
except UnicodeDecodeError:
    df_raw = pd.read_csv(RAW_PATH, encoding="cp949")

df_raw.head()