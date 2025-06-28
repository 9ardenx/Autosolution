# fetchers/coupang.py

import os, time, hmac, hashlib, aiohttp
from datetime import datetime

ACCESS = os.getenv("COUPANG_ACCESS_KEY")
SECRET = os.getenv("COUPANG_SECRET_KEY")
VENDOR = os.getenv("COUPANG_VENDOR_ID")
BASE   = "https://api-gateway.coupang.com"

def _hdr(method, path, query=""):
    ts = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    sig = hmac.new(SECRET.encode(), (ts+method+path+query).encode(),
                   hashlib.sha256).hexdigest()
    auth = f"CEA algorithm=HmacSHA256, access-key={ACCESS}, signed-date={ts}, signature={sig}"
    return {
        "Authorization": auth,
        "X-Requested-By": VENDOR,
        "Content-Type": "application/json;charset=UTF-8"
    }

async def fetch_orders():
    # 오늘 날짜(ISO yyyy-MM-dd)
    today = datetime.utcnow().strftime('%Y-%m-%d')
    path  = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR}/ordersheets"
    query = f"createdAtFrom={today}&createdAtTo={today}&status=ACCEPT&maxPerPage=100"
    url   = f"{BASE}{path}?{query}"

    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, headers=_hdr("GET", path, query)) as resp:
            resp.raise_for_status()
            js = await resp.json()

    out = []
    for o in js.get("data", []):
        receiver = o.get("receiver", {})
        items = o.get("orderItems", [])

        # 옵션명 포함 상품명(문자열) 확보
        if items:
            text = items[0].get("vendorItemName", "")
            # 쿠팡 옵션명 뒤에 "다크..." 등 포함되도록 설정되어 있어야 함
        else:
            text = ""

        out.append({
            "name":      receiver.get("name", ""),
            "contact":   receiver.get("receiverNumber", ""),
            "address":   f\"{receiver.get('addr1','')} {receiver.get('addr2','')}".strip(),
            "product":   text,                    # 옵션명 문자열
            "box_count": items[0].get("shippingCount", 0) if items else 0,
            "msg":        items[0].get("parcelPrintMessage", o.get("parcelPrintMessage","")),
            "order_id":   str(o.get("orderId",""))
        })

    return out
