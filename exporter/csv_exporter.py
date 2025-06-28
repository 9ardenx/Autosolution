# exporter/csv_exporter.py

import pandas as pd
import datetime as dt
import os
import pathlib

EXPORT_DIR = pathlib.Path("exports")

def save_csv(rows: list[dict]) -> str:
    """
    rows : [{'이름':..., '연락처':..., ...}, ...]
    returns : 외부에서 접근 가능한 CSV URL (str)
    """
    # 1) 로컬에 저장
    EXPORT_DIR.mkdir(exist_ok=True)
    fname = dt.datetime.now().strftime("%Y%m%d_%H%M") + ".csv"
    local_path = EXPORT_DIR / fname
    pd.DataFrame(rows).to_csv(local_path, index=False, encoding="utf-8-sig")

    # 2) 환경변수에서 PUBLIC_BASE_URL 읽기 (load_dotenv 이후에!)
    public_base = os.getenv("PUBLIC_BASE_URL")
    if not public_base:
        raise RuntimeError("환경변수 PUBLIC_BASE_URL 이 정의되어 있지 않습니다.")
    # 끝에 슬래시는 제거
    public_base = public_base.rstrip("/")

    # 3) 공개 URL 조합
    #    https://romancegarden.co.kr/exports/20250628_1440.csv
    public_url = f"{public_base}/{EXPORT_DIR.name}/{fname}"
    return public_url
