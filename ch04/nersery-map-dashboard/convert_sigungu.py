from pathlib import Path
import geopandas as gpd

APP_DIR = Path(__file__).resolve().parent
BOUNDARY_SHP = APP_DIR / "data" / "boundary" / "bnd_sigungu_00_2024_2Q.shp"
OUT_GEOJSON = APP_DIR / "data" / "geo" / "sigungu.geojson"


def check_shp_set(shp_path: Path) -> None:
    base = shp_path.with_suffix("")
    required = [".shp", ".shx", ".dbf", ".prj"]  # 강의 기준: prj까지 필수
    missing = [ext for ext in required if not Path(str(base) + ext).exists()]
    if missing:
        raise FileNotFoundError(
            f"[오류] SHP 세트 파일이 누락되었습니다: {missing}\n"
            f"확인 폴더: {shp_path.parent}"
        )


def main():
    # 1) 입력 파일 존재 확인
    if not BOUNDARY_SHP.exists():
        raise FileNotFoundError(
            f"[오류] SHP 파일을 찾을 수 없습니다:\n{BOUNDARY_SHP}\n"
            "→ data/boundary/ 폴더에 파일을 복사했는지 확인하세요."
        )

    # 2) 세트 파일 체크
    check_shp_set(BOUNDARY_SHP)
    print(f"[1] 입력 SHP: {BOUNDARY_SHP}")

    # 3) SHP 로드
    gdf = gpd.read_file(BOUNDARY_SHP)
    print(f"[2] 행 개수: {len(gdf)}")
    print(f"[2] 원본 CRS: {gdf.crs}")

    # 4) CRS 확인 (None이면 변환 불가)
    if gdf.crs is None:
        raise ValueError(
            "[오류] CRS를 확인할 수 없습니다(gdf.crs=None).\n"
            "→ .prj 파일이 존재하는지 확인하세요."
        )

    # 5) EPSG:4326(WGS84 위경도)로 변환
    gdf_4326 = gdf.to_crs(epsg=4326)
    print(f"[3] 변환 후 CRS: {gdf_4326.crs}")

    # 6) GeoJSON 저장
    OUT_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    gdf_4326.to_file(OUT_GEOJSON, driver="GeoJSON", encoding="utf-8")
    print(f"[4] 저장 완료: {OUT_GEOJSON}")


if __name__ == "__main__":
    main()