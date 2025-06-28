# fetchers/coupang.py

import os, time, hmac, hashlib, json, aiohttp

ACCESS = os.getenv("COUPANG_ACCESS_KEY")
SECRET = os.getenv("COUPANG_SECRET_KEY")
VENDOR = os.getenv("COUPANG_VENDOR_ID")
BASE   = "https://api-gateway.coupang.com"

def _hdr(method: str, path: str, body="") -> dict:
    ts = str(int(time.time() * 1000))
    msg = f"{method} {path}\n{ts}\n{ACCESS}\n{body}"
    sig = hmac.new(SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return {
        "Authorization": f"CEA {ACCESS}:{sig}",
        "X-Timestamp"  : ts,
        "Content-Type" : "application/json; charset=utf-8"
    }

async def fetch_orders():
    # 결제완료(ON_PAYMENT) 상태만 조회
    path = f"/v2/providers/openapi/apis/api/v1/vendors/{VENDOR}/ordersheets"
    # v1의 경우 쿼리 매개변수를 Body JSON으로 전달할 수도 있습니다:
    body = {
        "status": "ACCEPT",
        "page": 1,
        "maxPerPage": 50
    }
    url = f"{BASE}{path}"

    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, json=body, headers=_hdr("POST", path, json.dumps(body, separators=(',',':')))) as r:
            r.raise_for_status()
            data = await r.json()

    # 파싱 로직
    return [
        {
            "name"     : o["shippingAddress"]["name"],
            "contact"  : o["shippingAddress"]["receiverPhone"],
            "address"  : f"{o['shippingAddress']['baseAddress']} {o['shippingAddress']['detailAddress']}".strip(),
            "product"  : o["productName"],
            "box_count": o["shippingCount"],
            "msg"      : o.get("deliveryMemo",""),
            "order_id" : str(o["orderId"]),
        }
        for o in data.get("orderSheetDtos", [])
    ]
