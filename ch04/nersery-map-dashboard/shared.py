from pathlib import Path
import pandas as pd
import geopandas as gpd

app_dir = Path(__file__).resolve().parent

data_dir = app_dir / "data"
geo_dir = data_dir / "geo"
processed_dir = data_dir / "processed"

SIGUNGU_GEOJSON = geo_dir / "sigungu.geojson"
NURSERY_CLEAN = processed_dir / "nursery_clean.csv"

gdf_sigungu = gpd.read_file(SIGUNGU_GEOJSON)
df = pd.read_csv(NURSERY_CLEAN, encoding="utf-8-sig")

# shared.py (추가)
try:
    from data.config_api import KAKAO_JAVASCRIPT_KEY
    KAKAO_APP_KEY = str(KAKAO_JAVASCRIPT_KEY).strip()
except Exception:
    KAKAO_APP_KEY = ""