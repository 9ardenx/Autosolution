import pandas as pd, datetime as dt, os, pathlib

EXPORT_DIR = pathlib.Path("exports")

def save_csv(rows: list[dict]) -> str:
    """
    rows : [{'이름':..., '연락처':..., ...}, ...]
    returns : 저장된 로컬 경로(str)
    """
    EXPORT_DIR.mkdir(exist_ok=True)
    fname = dt.datetime.now().strftime("%Y%m%d_%H%M") + ".csv"
    path = EXPORT_DIR / fname
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
    return str(path)
