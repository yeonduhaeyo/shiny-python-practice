from pathlib import Path
import pandas as pd

APP_DIR = Path(__file__).resolve().parent
RAW_PATH = APP_DIR / "data" / "raw" / "nursery.xls"

print("\n[1] 원본 엑셀(.xls) 파일을 로드합니다.")
print(f" - 파일 경로: {RAW_PATH}")

if not RAW_PATH.exists():
    raise FileNotFoundError(
        f"[오류] 원본 파일을 찾을 수 없습니다:\n{RAW_PATH}\n"
        "→ data/raw/에 nursery.xls 파일을 저장했는지 확인하세요."
    )

df_raw = pd.read_excel(RAW_PATH, engine="xlrd")
print(f" - 로드 완료: {df_raw.shape[0]}행 x {df_raw.shape[1]}열")

print("\n[2] 원본 데이터 미리보기(head) - 상위 5행")
print(df_raw.head())

print("\n[3] 원본 데이터 구조(info)")
df_raw.info()

print("\n[4] 컬럼명 공백(strip)을 제거합니다.")
df_raw.columns = df_raw.columns.astype(str).str.strip()

required_cols = [
    "시도", "시군구", "어린이집명", "어린이집유형구분",
    "운영현황", "주소", "위도", "경도"
]
missing = [c for c in required_cols if c not in df_raw.columns]
if missing:
    raise KeyError(f"[오류] 필수 컬럼이 없습니다: {missing}")
print(" - 필수 컬럼 확인 완료")

print("\n[5] 운영현황='폐지' 행을 제외합니다.")
df_raw["운영현황"] = df_raw["운영현황"].astype(str).str.strip()

print(" - 운영현황 분포(필터 전):")
print(df_raw["운영현황"].value_counts(dropna=False))

before = len(df_raw)
df = df_raw[df_raw["운영현황"].ne("폐지")].copy()
after = len(df)

print(f" - 필터 전: {before}행")
print(f" - 필터 후: {after}행")
print(f" - 제외된 행(폐지): {before - after}행")

print(" - 운영현황 분포(필터 후):")
print(df["운영현황"].value_counts(dropna=False))

if "폐지일자" in df.columns:
    df = df.drop(columns=["폐지일자"])
    print("\n[6] 폐지 제외 후 '폐지일자' 컬럼은 제거합니다.")
    print(" - 폐지일자 컬럼 제거 완료")

print("\n[7] 결측값 점검(리포트) - 폐지 제외 후 기준")
missing_rows = int(df.isna().any(axis=1).sum())
print(f" - 결측이 포함된 행 수: {missing_rows}행")

print(" - 컬럼별 결측 개수(내림차순):")
print(df.isna().sum().sort_values(ascending=False))

print("\n[8] 중복값 제거를 진행합니다.")
dedupe_keys = [c for c in ["시도", "시군구", "어린이집명", "주소", "어린이집전화번호"] if c in df.columns]
print(f" - 중복 제거 기준 컬럼: {dedupe_keys}")

before = len(df)
df = df.drop_duplicates(subset=dedupe_keys, keep="first").copy()
after = len(df)

print(f" - 제거 전: {before}행")
print(f" - 제거 후: {after}행")
print(f" - 제거된 중복 행: {before - after}행")

print("\n[9] 텍스트/분류형 결측을 기본값으로 채웁니다.")
fill_map = {}
if "통학차량운영여부" in df.columns:
    fill_map["통학차량운영여부"] = "미확인"
if "홈페이지주소" in df.columns:
    fill_map["홈페이지주소"] = ""
if "어린이집팩스번호" in df.columns:
    fill_map["어린이집팩스번호"] = ""
if "어린이집전화번호" in df.columns:
    fill_map["어린이집전화번호"] = ""

df = df.fillna(value=fill_map)
print(f" - 채운 컬럼: {list(fill_map.keys())}")

print("\n[10] 숫자/좌표 컬럼을 숫자형으로 변환합니다.")
numeric_targets = [c for c in [
    "우편번호",
    "보육실수", "보육실면적", "놀이터수", "CCTV설치수",
    "보육교직원수", "정원수", "현원수",
    "위도", "경도",
] if c in df.columns]

for c in numeric_targets:
    df[c] = pd.to_numeric(df[c], errors="coerce")
print(" - 숫자형 변환 완료")

print("\n[11] 날짜 컬럼을 datetime으로 변환합니다.")
date_cols = [c for c in ["인가일자", "휴지시작일자", "휴지종료일자"] if c in df.columns]
for c in date_cols:
    df[c] = pd.to_datetime(df[c], errors="coerce")
print(f" - 날짜 변환 완료: {date_cols}")

print("\n[12] 좌표 결측 행 제거(지도 실습 기준)")
coord_na = df["위도"].isna() | df["경도"].isna()
na_count = int(coord_na.sum())
print(f" - 위도/경도 중 하나라도 결측인 행: {na_count}행")

before = len(df)
df = df.loc[~coord_na].copy()
after = len(df)

print(f" - 제거 전: {before}행")
print(f" - 제거 후: {after}행")
print(f" - 제거된 행(좌표 결측): {before - after}행")

print("\n[13] choropleth 조인 키(sgg_key)를 생성합니다.")
df["sgg_key"] = df["시도"].astype(str).str.strip() + " " + df["시군구"].astype(str).str.strip()
print(" - sgg_key 생성 완료")

OUT_DIR = APP_DIR / "data" / "processed"
OUT_CSV = OUT_DIR / "nursery_clean.csv"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print("\n[14] 정제 CSV 파일을 저장합니다.")
print(f" - 저장 경로: {OUT_CSV}")

df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print(" - 저장 완료")
print(f" - 최종 데이터: {df.shape[0]}행 x {df.shape[1]}열")