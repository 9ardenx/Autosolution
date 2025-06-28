# fetchers/smartstore.py

import os
import time
import aiohttp
import bcrypt            # pip install bcrypt
import pybase64          # pip install pybase64
from datetime import datetime, timedelta, timezone

# 환경변수
CLIENT_ID     = os.getenv("NAVER_ACCESS_KEY")
CLIENT_SECRET = os.getenv("NAVER_SECRET_KEY")
CUSTOMER_ID   = os.getenv("NAVER_CUSTOMER_ID")

# 엔드포인트
TOKEN_URL      = "https://api.commerce.naver.com/external/v1/oauth2/token"
ORDER_LIST_URL = "https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders"

async def _fetch_token() -> str:
    """OAuth2 Client Credentials Grant + 전자서명으로 토큰 발급"""
    timestamp = str(int((time.time() - 3) * 1000))
    raw = f"{CLIENT_ID}_{timestamp}".encode()
    signed = bcrypt.hashpw(raw, CLIENT_SECRET.encode())
    client_secret_sign = pybase64.standard_b64encode(signed).decode()

    data = {
        "client_id":          CLIENT_ID,
        "timestamp":          timestamp,
        "client_secret_sign": client_secret_sign,
        "grant_type":         "client_credentials",
        "type":               "SELF"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with aiohttp.ClientSession() as sess:
        async with sess.post(TOKEN_URL, data=data, headers=headers) as resp:
            resp.raise_for_status()
            js = await resp.json()

    token      = js["access_token"]
    expires_in = js.get("expires_in", 10800)
    # save expiry so we could cache if desired
    _fetch_token._expires_at = time.time() + expires_in - 60
    _fetch_token._token      = token
    return token

async def get_token() -> str:
    """
    캐시된 토큰이 있으면 재사용, 없거나 만료 임박 시 재발급
    """
    if not getattr(_fetch_token, "_token", None) or time.time() >= getattr(_fetch_token, "_expires_at", 0):
        return await _fetch_token()
    return _fetch_token._token

async def fetch_orders(
    created_from: str = None,
    status:        list = None,
    page_size:     int  = 100,
    page:          int  = 1
) -> list:
    """
    조건형 상품 주문 상세 내역 조회 (GET)
    - created_from: ISO 8601 "YYYY-MM-DDTHH:MM:SS.sss±TZ" 형식 (생략 시 24시간 전)
    - status: ["ON_PAYMENT", ...] (결제완료 등)
    """
    # 1) 기본 날짜 범위: 24시간 전부터 현재까지
    now = datetime.now(timezone.utc).astimezone()
    if created_from is None:
        created_from = (now - timedelta(days=1)).isoformat(timespec="milliseconds")
    if status is None:
        status = ["ON_PAYMENT"]

    # 2) 쿼리 파라미터 (to 생략하면 24시간 기본)
    params = {
        "from":                  created_from,
        "rangeType":             "PAYED_DATETIME",
        "productOrderStatuses":  ",".join(status),
        "pageSize":              page_size,
        "page":                  page
    }

    # 3) 헤더에 Bearer 토큰과 고객 ID 포함
    token = await get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "X-Customer-Id": CUSTOMER_ID
    }

    # 4) API 호출
    async with aiohttp.ClientSession() as sess:
        async with sess.get(ORDER_LIST_URL, params=params, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()

    # 5) data 배열 반환
    return data.get("data", [])

