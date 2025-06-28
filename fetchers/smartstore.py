# fetchers/smartstore.py

import os
import time
import aiohttp
import bcrypt  # pip install bcrypt
import pybase64  # pip install pybase64
from datetime import datetime, timedelta, timezone

# 환경변수
CLIENT_ID     = os.getenv("NAVER_ACCESS_KEY")
CLIENT_SECRET = os.getenv("NAVER_SECRET_KEY")
CUSTOMER_ID   = os.getenv("NAVER_CUSTOMER_ID")

# 엔드포인트
TOKEN_URL        = "https://api.commerce.naver.com/external/v1/oauth2/token"
LAST_CHANGED_URL = "https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders/last-changed-statuses"

async def _fetch_token() -> str:
    """OAuth2 Client Credentials Grant + 전자서명으로 토큰 발급"""
    ts = str(int((time.time() - 3) * 1000))
    raw = f"{CLIENT_ID}_{ts}".encode()
    signed = bcrypt.hashpw(raw, CLIENT_SECRET.encode())
    sign_b64 = pybase64.standard_b64encode(signed).decode()

    data = {
        "client_id":          CLIENT_ID,
        "timestamp":          ts,
        "client_secret_sign": sign_b64,
        "grant_type":         "client_credentials",
        "type":               "SELF"
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
    """캐시된 토큰 재사용, 없거나 만료 임박 시 재발급"""
    if not getattr(_fetch_token, "_token", None) or time.time() >= getattr(_fetch_token, "_expires_at", 0):
        return await _fetch_token()
    return _fetch_token._token

async def fetch_orders(
    last_changed_from: str = None,
    last_changed_type: str = "PAYED",
    limit_count:      int = 100,
    more_sequence:    str = None
) -> list:
    """
    '변경 상품 주문 내역 조회' (last-changed-statuses)
    - last_changed_from: ISO8601 with ms +TZ (e.g. "2025-06-27T21:00:00.000+09:00"), defaults to 24h ago
    - last_changed_type: one of PAY_WAITING,PAYED,DELIVERING,DELIVERED, etc.
    - limit_count: up to 300
    - more_sequence: for paging
    """
    KST = timezone(timedelta(hours=9))
    now_kst = datetime.now(KST)
    if last_changed_from is None:
        last_changed_from = (now_kst - timedelta(days=1)).isoformat(timespec="milliseconds")

    params = {
        "lastChangedFrom": last_changed_from,
        "lastChangedType": last_changed_type,
        "limitCount":      limit_count
    }
    if more_sequence:
        params["moreSequence"] = more_sequence

    token = await _get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "X-Customer-Id": CUSTOMER_ID
    }

    async with aiohttp.ClientSession() as sess:
        async with sess.get(LAST_CHANGED_URL, params=params, headers=headers) as resp:
            # 디버그 로그
            text = await resp.text()
            print(f"[SmartStore] request params: {params}")
            print(f"[SmartStore] status: {resp.status}")
            print(f"[SmartStore] body: {text}")
            resp.raise_for_status()
            resp_json = await resp.json()

    raw = resp_json.get("data", {})
    orders_list = raw.get("lastChangeStatuses", [])
    results = []
    for o in orders_list:
        results.append({
            "name":      o.get("receiverName", ""),
            "contact":   o.get("receiverContactTelephone", ""),
            "address":   f"{o.get('receiverBaseAddress','')} {o.get('receiverDetailAddress','')}".strip(),
            "product":   o.get("productName", "") or o.get("productOrderId", ""),
            "box_count": 1,
            "msg":        o.get("orderMemo", ""),
            "order_id":  str(o.get("orderId", ""))
        })

    return results

