# shared.py
from pathlib import Path
import pandas as pd

# shared.py 위치를 기준으로 경로를 고정
app_dir = Path(__file__).resolve().parent
data_path = app_dir / "data" / "ev_car.csv"

# UTF-8 계열로 먼저 시도 → 실패하면 CP949로 재시도
try:
    df_raw = pd.read_csv(data_path, encoding="utf-8-sig")
except UnicodeDecodeError:
    df_raw = pd.read_csv(data_path, encoding="cp949")

df_raw.info()