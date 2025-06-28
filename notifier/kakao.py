# notifier/kakao.py

import os, requests

def send_file_link(url: str):
    """
    CSV 파일 URL을 '나에게 보내기'로 스크랩 카드 전송
    - KAKAO_ACCESS_TOKEN: 사용자 액세스 토큰(카카오 로그인 → talk_message 권한 필요)
    """
    token = os.getenv("KAKAO_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("KAKAO_ACCESS_TOKEN 환경변수 없음")

    res = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/scrap/send",
        headers={"Authorization": f"Bearer {token}"},
        data={"request_url": url}
    )
    if res.status_code != 200:
        raise RuntimeError(f"Kakao API 오류: {res.status_code} {res.text}")
    return True
