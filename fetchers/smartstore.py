import os
import time
import aiohttp
import bcrypt            # pip install bcrypt
import pybase64          # pip install pybase64
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
    if not getattr(_fetch_token, "_token", None) or time.time() >= getattr(_fetch_token, "_expires_at", 0):
        return await _fetch_token()
    return _fetch_token._token

async def fetch_orders(days: int = 4) -> list:
    """
    최근 n일간 결제완료(PAYED) 주문만 불러오기
    """
    KST = timezone(timedelta(hours=9))
    now_kst = datetime.now(KST)
    created_from = (now_kst - timedelta(days=days)).isoformat(timespec="milliseconds")

    params = {
        "from":                  created_from,
        "rangeType":             "PAYED_DATETIME",
        "productOrderStatuses":  "PAYED",
        "pageSize":              100,
        "page":                  1
    }

    token = await _get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "X-Customer-Id": CUSTOMER_ID
    }

    async with aiohttp.ClientSession() as sess:
        async with sess.get(ORDER_LIST_URL, params=params, headers=headers) as resp:
            if resp.status == 403:
                print("[SmartStore] 403 Forbidden: 인증 실패(키/시크릿/고객ID 확인) or 권한 부족")
                return []
            resp.raise_for_status()
            response_json = await resp.json()

    orders = response_json.get("data", {}).get("productOrderDtos", [])
    results = []
    for o in orders:
        results.append({
            "name":      o.get("receiverName", ""),
            "contact":   o.get("receiverContactTelephone", ""),
            "address":   f"{o.get('receiverBaseAddress','')} {o.get('receiverDetailAddress','')}".strip(),
            "product":   o.get("vendorItemName", ""),
            "box_count": o.get("orderCount", 1),
            "msg":       o.get("parcelPrintMessage", o.get("orderMemo", "")),
            "order_id":  str(o.get("orderId", ""))
        })

    return results
