import os
import time
import hmac
import hashlib
import aiohttp
from datetime import datetime, timedelta

# === 반드시 함수 바깥! ===
ACCESS = os.getenv("COUPANG_ACCESS_KEY")
SECRET = os.getenv("COUPANG_SECRET_KEY")
VENDOR = os.getenv("COUPANG_VENDOR_ID")
BASE   = "https://api-gateway.coupang.com"
async def fetch_orders() -> list:
    """최근 7일치 결제완료(ACCEPT) 주문 조회 및 평탄화"""
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    start = seven_days_ago.strftime('%Y-%m-%dT00:00:00')
    end   = now.strftime('%Y-%m-%dT23:59:59')

    path = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR}/ordersheets"
    query = (
        f"createdAtFrom={start}&createdAtTo={end}"
        f"&status=ACCEPT&maxPerPage=50"
    )
    url = f"{BASE}{path}?{query}"

    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, headers=_hdr("GET", path, query)) as resp:
            resp.raise_for_status()
            resp_json = await resp.json()

    results = []
    for o in resp_json.get("data", []):
        receiver = o.get("receiver", {})
        items    = o.get("orderItems", [])
        if items:
            first = items[0]
            product_name = first.get("vendorItemName", "")
            box_count    = first.get("shippingCount", 0)
            msg          = first.get("parcelPrintMessage", o.get("parcelPrintMessage", ""))
        else:
            product_name = ""
            box_count    = 0
            msg          = o.get("parcelPrintMessage", "")

        results.append({
            "name":      receiver.get("name", ""),
            "contact":   receiver.get("receiverNumber", ""),
            "address":   f"{receiver.get('addr1','')} {receiver.get('addr2','')}".strip(),
            "product":   product_name,
            "box_count": box_count,
            "msg":       msg,
            "order_id":  str(o.get("orderId", ""))
        })

    return results
