from pathlib import Path
import pandas as pd
import geopandas as gpd

app_dir = Path(__file__).resolve().parent

data_dir = app_dir / "data"
geo_dir = data_dir / "geo"
processed_dir = data_dir / "processed"

NURSERY_CLEAN = processed_dir / "nursery_clean.csv"
SIGUNGU_GEOJSON = geo_dir / "sigungu.geojson"

df_clean = pd.read_csv(NURSERY_CLEAN, encoding="utf-8-sig")
gdf_sigungu = gpd.read_file(SIGUNGU_GEOJSON)