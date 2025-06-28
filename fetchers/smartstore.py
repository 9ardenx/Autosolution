from datetime import datetime
import os, json, time
import hashlib, hmac, aiohttp

ACCESS = os.getenv("NAVER_ACCESS_KEY")
SECRET = os.getenv("NAVER_SECRET_KEY")
CID    = os.getenv("NAVER_CUSTOMER_ID")
BASE   = "https://api.commerce.naver.com"

def _sig(method, path, ts, body=""):
    msg = f"{ts}.{method}.{path}.{body}"
    return hmac.new(SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()

def _hdr(method, path, body=""):
    ts = str(int(time.time() * 1000))
    signature = _sig(method, path, ts, json.dumps(body, separators=(",",":")) if body else "")
    return {
        "X-API-KEY":      ACCESS,
        "X-Customer-Id":  CID,
        "X-Timestamp":    ts,
        "X-Signature":    signature,
        "Content-Type":   "application/json"
    }

async def fetch_orders():
    # 날짜 포맷 맞춰서
    from_date = "2024-01-01T00:00:00"
    to_date   = "2099-12-31T23:59:59"

    # v1 한 방 조회
    path = "/external/v1/pay-order/seller/product-orders/query"
    body = {
        "createdAtFrom": from_date,
        "createdAtTo":   to_date,
        "status":        ["ON_PAYMENT"]
    }
    url = f"{BASE}{path}"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=body, headers=_hdr("POST", path, body)) as resp:
            resp.raise_for_status()
            data = await resp.json()

    orders = []
    for dto in data.get("productOrderDtos", []):
        orders.append({
            "name":        dto["receiverName"],
            "contact":     dto["receiverPhone"],
            "address":     f"{dto['receiverAddr']}".strip(),
            "product":     dto["productName"],
            "box_count":   dto["orderCount"],
            "msg":         dto.get("memo", ""),
            "order_id":    dto["orderId"],
        })
    return orders

