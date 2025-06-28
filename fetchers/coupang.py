# fetchers/coupang.py

import os, time, hmac, hashlib, json, aiohttp
from datetime import datetime

ACCESS = os.getenv("COUPANG_ACCESS_KEY")
SECRET = os.getenv("COUPANG_SECRET_KEY")
VENDOR = os.getenv("COUPANG_VENDOR_ID")
BASE   = "https://api-gateway.coupang.com"

def _hdr(method: str, path: str, query: str = "") -> dict:
    ts = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    sts = f"{ts}{method}{path}{query}"
    sig = hmac.new(SECRET.encode(), sts.encode(), hashlib.sha256).hexdigest()
    auth = (
        f"CEA algorithm=HmacSHA256, "
        f"access-key={ACCESS}, "
        f"signed-date={ts}, "
        f"signature={sig}"
    )
    return {
        "Authorization": auth,
        "X-Requested-By": VENDOR,
        "Content-Type": "application/json;charset=UTF-8"
    }

async def fetch_orders():
    path = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR}/ordersheets"
    today = datetime.now()
    created_at_from = today.strftime('%Y-%m-%d')
    created_at_to = today.strftime('%Y-%m-%d')
    query = f"createdAtFrom={created_at_from}&createdAtTo={created_at_to}&status=ACCEPT&maxPerPage=50"
    url = f"{BASE}{path}?{query}"

    # 1) 세션 열기 → 2) 요청 → 3) JSON 파싱
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, headers=_hdr("GET", path, query)) as r:
            r.raise_for_status()
            response_json = await r.json()         # ← 반드시 이 변수에 저장

    # 4) response_json에서 'data' 키 추출
    orders_data = response_json.get("data", [])  # 키가 없어도 빈 리스트 반환

    # 5) 올바른 스코프에서 orders_data 사용
    parsed = []
    for o in orders_data:
        parsed.append({
            "name"     : o.get("receiver", {}).get("name", ""),
            "contact"  : o.get("receiver", {}).get("receiverNumber", ""),
            "address"  : f"{o.get('receiver', {}).get('addr1','')} {o.get('receiver', {}).get('addr2','')}".strip(),
            "product"  : o.get("orderItems", [{}])[0].get("vendorItemName", ""),
            "box_count": o.get("orderItems", [{}])[0].get("shippingCount", 0),
            "msg"      : o.get("parcelPrintMessage", ""),
            "order_id" : str(o.get("orderId", "")),
        })

    return parsed
