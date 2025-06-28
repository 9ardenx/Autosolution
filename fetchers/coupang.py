import os
import time
import hmac
import hashlib
import aiohttp
from datetime import datetime, timedelta

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

async def fetch_orders(days: int = 4) -> list:
    """
    최근 n일간 결제완료(ACCEPT) 주문만 불러오기
    """
    now = datetime.utcnow()
    start = (now - timedelta(days=days)).strftime('%Y-%m-%dT00:00:00')
    end   = now.strftime('%Y-%m-%dT23:59:59')

    path = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR}/ordersheets"
    query = f"createdAtFrom={start}&createdAtTo={end}&status=ACCEPT&maxPerPage=50"
    url = f"{BASE}{path}?{query}"

    print(f"[Coupang] request URL: {url}")

    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, headers=_hdr("GET", path, query)) as resp:
            if resp.status == 403:
                print("[Coupang] 403 Forbidden: 인증 실패 or 주문 없음 or 권한 문제 → 빈 리스트 반환")
                return []
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

