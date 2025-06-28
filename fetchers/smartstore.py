import os
import time
import aiohttp
import bcrypt
import pybase64
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

async def fetch_orders_per_day(created_from, created_to, status=["PAYED"], page=1, page_size=100):
    token = await _get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "X-Customer-Id": CUSTOMER_ID
    }
    params = {
        "from":                  created_from,
        "to":                    created_to,
        "rangeType":             "PAYED_DATETIME",
        "productOrderStatuses":  ",".join(status),
        "pageSize":              page_size,
        "page":                  page
    }
    async with aiohttp.ClientSession() as sess:
        async with sess.get(ORDER_LIST_URL, params=params, headers=headers) as resp:
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
            "msg":        o.get("parcelPrintMessage", o.get("orderMemo", "")),
            "order_id":  str(o.get("orderId", ""))
        })
    return results

async def fetch_orders(days: int = 4) -> list:
    """
    최근 days일(4일)간 모든 'PAYED' 주문 긁어오기 (페이지 전부)
    """
    all_results = []
    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST)
    for i in range(days):
        day_from = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_to   = day_from + timedelta(days=1)
        created_from = day_from.isoformat(timespec="milliseconds")
        created_to   = day_to.isoformat(timespec="milliseconds")
        page = 1
        while True:
            batch = await fetch_orders_per_day(created_from, created_to, page=page)
            if not batch:
                break
            all_results.extend(batch)
            if len(batch) < 100:
                break
            page += 1
    return all_results
