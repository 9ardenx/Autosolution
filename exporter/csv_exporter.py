import pandas as pd
import datetime as dt
import os
import pathlib

# 로컬 exports 폴더
EXPORT_DIR = pathlib.Path("exports")
# 외부에서 접근 가능한 베이스 URL (끝에 슬래시 제외)
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

def save_csv(rows: list[dict]) -> str:
    """
    rows : [{'이름':..., '연락처':..., ...}, ...]
    returns : 외부에서 접근 가능한 CSV URL (str)
    """
    # 1) 로컬에 저장
    EXPORT_DIR.mkdir(exist_ok=True)
    fname = dt.datetime.now().strftime("%Y%m%d_%H%M") + ".csv"
    path = EXPORT_DIR / fname
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")

    # 2) 공개 URL 생성
    #    예: https://romancegarden.co.kr/exports/20250628_1432.csv
    public_url = f"{PUBLIC_BASE_URL}/{EXPORT_DIR.name}/{fname}"
    return public_url
