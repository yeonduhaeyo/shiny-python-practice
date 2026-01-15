from pathlib import Path
import geopandas as gpd

APP_DIR = Path(__file__).resolve().parent
BOUNDARY_SHP = APP_DIR / "data" / "boundary" / "bnd_sigungu_00_2024_2Q.shp"
OUT_GEOJSON = APP_DIR / "data" / "geo" / "sigungu.geojson"

SEOUL_SIDO_PREFIX = "11"


def check_shp_set(shp_path: Path) -> None:
    base = shp_path.with_suffix("")
    required = [".shp", ".shx", ".dbf", ".prj"]
    missing = [ext for ext in required if not Path(str(base) + ext).exists()]
    if missing:
        raise FileNotFoundError(
            f"[오류] SHP 세트 파일이 누락되었습니다: {missing}\n"
            f"확인 폴더: {shp_path.parent}"
        )


def main():
    if not BOUNDARY_SHP.exists():
        raise FileNotFoundError(
            f"[오류] SHP 파일을 찾을 수 없습니다:\n{BOUNDARY_SHP}\n"
            "→ data/boundary/ 폴더에 파일을 복사했는지 확인하세요."
        )

    check_shp_set(BOUNDARY_SHP)
    print(f"[1] 입력 SHP: {BOUNDARY_SHP}")

    gdf = gpd.read_file(BOUNDARY_SHP)
    print(f"[2] 행 개수(전체): {len(gdf)}")
    print(f"[2] 원본 CRS: {gdf.crs}")

    if gdf.crs is None:
        raise ValueError(
            "[오류] CRS를 확인할 수 없습니다(gdf.crs=None).\n"
            "→ .prj 파일이 존재하는지 확인하세요."
        )

    # 서울만 필터링
    gdf["SIGUNGU_CD"] = gdf["SIGUNGU_CD"].astype(str).str.strip()
    gdf_seoul = gdf[gdf["SIGUNGU_CD"].str.startswith(SEOUL_SIDO_PREFIX)].copy()
    print(f"[3] 서울 필터 후 행 개수: {len(gdf_seoul)}")

    if len(gdf_seoul) == 0:
        raise ValueError(
            "[오류] 서울 필터 결과가 0행입니다.\n"
            "→ 서울 시도코드가 '11'이 맞는지 확인하세요."
        )

    # EPSG:4326 변환
    gdf_seoul_4326 = gdf_seoul.to_crs(epsg=4326)
    print(f"[4] 변환 후 CRS: {gdf_seoul_4326.crs}")

    # 저장 컬럼 최소화 (서울 시군구명/코드 + geometry만)
    out = gdf_seoul_4326[["BASE_DATE", "SIGUNGU_NM", "SIGUNGU_CD", "geometry"]].copy()

    OUT_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    out.to_file(OUT_GEOJSON, driver="GeoJSON", encoding="utf-8")
    print(f"[5] 저장 완료: {OUT_GEOJSON}")


if __name__ == "__main__":
    main()