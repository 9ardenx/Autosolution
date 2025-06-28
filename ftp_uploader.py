import os
from ftplib import FTP

def upload_csv_ftp(local_path: str, remote_filename: str = None):
    FTP_HOST = os.getenv("FTP_HOST")
    FTP_USER = os.getenv("FTP_USER")
    FTP_PASS = os.getenv("FTP_PASS")
    FTP_DIR  = os.getenv("FTP_DIR", "/www/exports/")  # 필요시 경로 수정

    if not remote_filename:
        remote_filename = os.path.basename(local_path)

    with FTP(FTP_HOST) as ftp:
        ftp.login(FTP_USER, FTP_PASS)
        ftp.cwd(FTP_DIR)
        with open(local_path, "rb") as f:
            ftp.storbinary(f"STOR {remote_filename}", f)
    print(f"업로드 완료: {remote_filename}")

# 사용 예시 (csv_path는 너의 save_csv 리턴값)
# upload_csv_ftp(csv_path)
