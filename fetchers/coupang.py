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

async def fetch_orders(
    created_from: str = None,
    status:        list = None,
    page_size:     int  = 100,
    page:          int  = 1
) -> list:
    """
    조건형 상품 주문 상세 내역 조회 (GET)
    - created_from: ISO 8601 "YYYY-MM-DDTHH:MM:SS.sss±TZ" (생략 시 24시간 전 KST)
    - status: ["PAYED", ...] 등 문서에 명시된 코드 사용
    """
    # 1) KST 기준 24시간 전부터 현재까지
    KST = timezone(timedelta(hours=9))
    now_kst = datetime.now(KST)
    if created_from is None:
        created_from = (now_kst - timedelta(days=1)).isoformat(timespec="milliseconds")
    if status is None:
        status = ["PAYED"]

    # 2) 파라미터 설정 (to 생략하면 from부터 24시간 범위)
    params = {
        "from":                  created_from,
        "rangeType":             "PAYED_DATETIME",
        "productOrderStatuses":  ",".join(status),
        "pageSize":              page_size,
        "page":                  page
    }

    # 3) 헤더에 Bearer 토큰과 고객 ID 포함
    token = await _get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "X-Customer-Id": CUSTOMER_ID
    }

    # 4) API 호출
    async with aiohttp.ClientSession() as sess:
        async with sess.get(ORDER_LIST_URL, params=params, headers=headers) as resp:
            resp.raise_for_status()
            response_json = await resp.json()

    # 5) 'productOrderDtos' 키의 리스트를 꺼내서 평탄화
    orders = response_json.get("data", {}).get("productOrderDtos", [])

    results = []
    for o in orders:
        # 각 주문의 첫 번째 상품 옵션만 사용
        item = (o.get("productOrderDtos") or [{}])[0] if False else o  # Placeholder, see below
        # Actually here, o itself is a productOrderDto containing fields:
        results.append({
            "name":      o.get("receiverName", ""),
            "contact":   o.get("receiverContactTelephone", ""),
            "address":   f"{o.get('receiverBaseAddress','')} {o.get('receiverDetailAddress','')}".strip(),
            "product":   o.get("vendorItemName", ""),     # 단일 문자열
            "box_count": o.get("orderCount", 1),
            "msg":        o.get("parcelPrintMessage", o.get("orderMemo", "")),
            "order_id":  str(o.get("orderId", ""))
        })

    return results
