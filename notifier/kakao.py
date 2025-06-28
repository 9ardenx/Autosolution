"""
CSV 링크를 '나에게 보내기'로 전송.
사전 준비: KAKAO_ACCESS_TOKEN, KAKAO_REST_KEY를 GitHub Secrets에 등록.
"""

import os, requests, json

def send_file_link(url: str, text: str = "재고/송장 CSV 파일입니다"):
    token = os.getenv("KAKAO_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("KAKAO_ACCESS_TOKEN 환경변수 없음")

    # Scrap API로 링크 카드 전송
    res = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/scrap/send",
        headers={"Authorization": f"Bearer {token}"},
        data={"request_url": url}
    )
    if res.status_code != 200:
        raise RuntimeError(f"Kakao API 오류: {res.status_code} {res.text}")
    return True
