import os
import requests
import json

def send_file_link(url: str):
    """
    CSV 파일 URL을 '나에게 보내기'로 전송 (Default API)
    - KAKAO_ACCESS_TOKEN: 사용자 액세스 토큰 필요
    """
    token = os.getenv("KAKAO_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("환경변수 KAKAO_ACCESS_TOKEN 이 정의되어 있지 않습니다.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/x-www-form-urlencoded"
    }
    template = {
        "object_type":  "text",
        "text":         "🚚 재고/송장 CSV 파일이 준비되었습니다!",
        "link": {
            "web_url":        url,
            "mobile_web_url": url
        },
        "button_title": "CSV 내려받기"
    }

    res = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers=headers,
        data={"template_object": json.dumps(template)}
    )
    if res.status_code != 200:
        raise RuntimeError(f"Kakao API 오류: {res.status_code} {res.text}")

    return True
