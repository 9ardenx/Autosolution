# fetchers/smartstore.py

import os, aiohttp, asyncio, bcrypt, pybase64, time
from datetime import datetime, timedelta, timezone

CLIENT_ID     = os.getenv("NAVER_ACCESS_KEY")
CLIENT_SECRET = os.getenv("NAVER_SECRET_KEY")
CUSTOMER_ID   = os.getenv("NAVER_CUSTOMER_ID")

TOKEN_URL      = "https://api.commerce.naver.com/external/v1/oauth2/token"
ORDER_LIST_URL = "https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders"

async def _fetch_token() -> str:
    ts = str(int((time.time() - 3) * 1000))
    raw = f"{CLIENT_ID}_{ts}".encode()
    signed = bcrypt.hashpw(raw, CLIENT_SECRET.encode())
    sign_b64 = pybase64.standard_b64encode(signed).decode()
    data = {
        "client_id": CLIENT_ID,
        "timestamp": ts,
        "client_secret_sign": sign_b64,
        "grant_type": "client_credentials",
        "type": "SELF"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    async with aiohttp.ClientSession() as sess:
        async with sess.post(TOKEN_URL, data=data, headers=headers) as resp:
            resp.raise_for_status()
            js = await resp.json()
    token      = js["access_token"]
    expires    = js.get("expires_in", 10800)
    _fetch_token._token      = token
    _fetch_token._expires_at = time.time() + expires - 60
    return token

async def _get_token() -> str:
    if not getattr(_fetch_token, "_token", None) or time.time() >= getattr(_fetch_token, "_expires_at", 0):
        return await _fetch_token()
    return _fetch_token._token

async def fetch_orders(
    created_from: str = None,
    status:        list = None,
    page_size:     int  = 100,
    page:          int  = 1
) -> list:
    # 1) 기본 from: KST 기준 24시간 전 ISO 8601
    KST = timezone(timedelta(hours=9))
    now_kst = datetime.now(KST)
    if created_from is None:
        created_from = (now_kst - timedelta(days=1)).isoformat(timespec="milliseconds")
    # 2) 올바른 상태 코드 사용: PAYED (결제 완료) 등
    if status is None:
        status = ["PAYED"]
    # 3) 직접 URL 문자열 조합 (인코딩 이중 방지)
    query = (
        f"from={created_from}"
        f"&rangeType=PAYED_DATETIME"
        f"&productOrderStatuses={','.join(status)}"
        f"&pageSize={page_size}&page={page}"
    )
    url = f"{ORDER_LIST_URL}?{query}"
    # 4) 호출 헤더
    token = await _get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "X-Customer-Id": CUSTOMER_ID
    }
    # 5) API 요청
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
    return data.get("data", [])

