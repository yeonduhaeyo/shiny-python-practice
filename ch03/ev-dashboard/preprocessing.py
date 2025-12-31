from pathlib import Path
import pandas as pd

APP_DIR = Path(__file__).resolve().parent
RAW_PATH = APP_DIR / "data" / "ev_car.csv"
CLEAN_PATH = APP_DIR / "data" / "ev_car_clean.csv"

# 1-1) 데이터 로드
print("\n[1-1] 원본 데이터를 로드합니다.")
print(f" - 파일 경로: {RAW_PATH}")

try:
    df_raw = pd.read_csv(RAW_PATH, encoding="utf-8-sig")
    print(" - 인코딩: utf-8-sig 로 로드했습니다.")
except UnicodeDecodeError:
    df_raw = pd.read_csv(RAW_PATH, encoding="cp949")
    print(" - utf-8-sig 실패 → cp949 로 재시도하여 로드했습니다.")

print(f" - 로드 완료: {df_raw.shape[0]}행 x {df_raw.shape[1]}열")

# 1-2) head 확인
print("\n[1-2] 원본 데이터 미리보기(head) - 상위 5행을 출력합니다.")
print(df_raw.head())

# 1-3) info 확인
print("\n[1-3] 원본 데이터 구조(info)를 확인합니다.")
print(df_raw.info())

# 2-1) 결측치 점검
print("\n[2-1] 결측치 점검을 시작합니다.")
missing_rows = df_raw.isna().any(axis=1).sum()
print(f" - 결측이 포함된 행 수: {missing_rows}행")
print(" - 컬럼별 결측 개수:")
print(df_raw.isna().sum())

# 2-2) 중복 데이터 점검
print("\n[2-2] 중복 데이터 점검을 시작합니다.")
print(" - 기준 키: (시군구별, 연료별, 용도별)")
dup_cnt = df_raw.duplicated(subset=["시군구별", "연료별", "용도별"], keep=False).sum()
print(f" - 중복으로 잡힌 행 수: {dup_cnt}행")

# 2-3) 합계 일관성 점검
print("\n[2-3] 합계(계) 일관성 점검을 시작합니다.")
print(" - 확인 내용: 계 == (승용 + 승합 + 화물 + 특수)")
mismatch_cnt = (
    df_raw["계"] != (df_raw["승용"] + df_raw["승합"] + df_raw["화물"] + df_raw["특수"])
).sum()
print(f" - 불일치 행 수: {mismatch_cnt}행")

# 3-0) 정제 전 데이터 스캔(unique/value_counts)
print("\n[3-0] 정제 전 데이터 스캔(unique / value_counts)")

s = (
    df_raw["시군구별"].astype("string")
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

print(" - unique 개수:", s.nunique(dropna=True))
print(" - unique 샘플(앞 20개):")
print(s.dropna().unique()[:20])

# (참고) 전체 unique를 확인하고 싶다면 아래처럼 확인할 수 있습니다.
# print(s.dropna().unique())
# 또는 s.dropna().drop_duplicates().to_csv("unique_sigungu.csv", index=False, encoding="utf-8-sig")

# 3-1) 문자열 공백 정리 + 시도/시군구 분리 + 시도 표준화
print("\n[3-1] 데이터 정제를 시작합니다.")
print(" - 정제 1) 문자열 공백 정리: (시군구별, 연료별, 용도별)")
print(" - 정제 2) 시군구별 분리: 시도/시군구")
print(" - 정제 3) 시도 표준화: 경상북도→경북 등")

df_clean = df_raw.copy()

for col in ["시군구별", "연료별", "용도별"]:
    df_clean[col] = (
        df_clean[col].astype("string")
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

tokens = df_clean["시군구별"].str.split(" ")
df_clean["시도"] = tokens.str[0]
df_clean["시군구"] = tokens.apply(
    lambda x: " ".join(x[1:]) if isinstance(x, list) and len(x) > 1 else ""
)

sido_map = {
    "경상북도": "경북",
    "경상남도": "경남",
    "전라북도": "전북",
    "전라남도": "전남",
    "충청북도": "충북",
    "충청남도": "충남",
}
df_clean["시도"] = df_clean["시도"].replace(sido_map)

print(" - 정제 결과 미리보기(시군구별/시도/시군구 상위 5행):")
print(df_clean[["시군구별", "시도", "시군구"]].head())

# 3-2) 정제 후 결측 재확인
print("\n[3-2] 정제 후 결측 재확인을 시작합니다.")
print(" - 핵심 컬럼(시군구별/시도/시군구)에 결측이 없는지 확인합니다.")
print(df_clean[["시군구별", "시도", "시군구"]].isna().sum())

# 3-3) 정제 후 중복 재확인 + 간단 통합
print("\n[3-3] 정제 후 중복 재확인을 시작합니다.")

key_cols = ["시도", "시군구", "연료별", "용도별"]
dup_cnt2 = df_clean.duplicated(subset=key_cols, keep=False).sum()
print(f" - 정제 후 중복 행 수(기준 키={key_cols}): {dup_cnt2}행")

if dup_cnt2 > 0:
    print(" - 중복이 발견되어, 동일 키는 합산 통합(groupby sum)으로 정리합니다.")
    df_clean = (
        df_clean
        .groupby(key_cols, as_index=False)[["승용", "승합", "화물", "특수", "계"]]
        .sum()
    )
    df_clean["계"] = df_clean["승용"] + df_clean["승합"] + df_clean["화물"] + df_clean["특수"]

    print(" - 통합 완료. (중복 재확인)")
    print(" - 중복 행 수:", df_clean.duplicated(subset=key_cols, keep=False).sum())

# 4) 저장 전 결측 재확인 + 저장
print("\n[4] 정제 데이터 저장 단계를 시작합니다.")
print(f" - 저장 경로: {CLEAN_PATH}")

na_rows = df_clean.isna().any(axis=1).sum()
print(f" - 저장 전 전체 결측 점검: 결측 포함 행 수 = {na_rows}행")

if na_rows > 0:
    print(" - 결측이 있어 저장을 중단합니다. (결측 상세)")
    print(df_clean.isna().sum())
    raise ValueError("정제 후 결측이 발견되어 저장을 중단합니다.")

df_clean.to_csv(CLEAN_PATH, index=False, encoding="utf-8-sig")
print(" - 저장 완료")

print("\n[완료] 정제 파일 생성이 끝났습니다.")
print(f" - 정제 파일 경로: {CLEAN_PATH}")