from pathlib import Path
import pandas as pd

app_dir = Path(__file__).resolve().parent
clean_path = app_dir / "data" / "ev_car_clean.csv"

df = pd.read_csv(clean_path, encoding="utf-8-sig")