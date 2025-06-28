import os, time, hmac, hashlib, aiohttp, json

BASE = "https://api.commerce.naver.com/external/v2"
AK, SK, CID = os.getenv("NAVER_ACCESS_KEY"), os.getenv("NAVER_SECRET_KEY"), os.getenv("NAVER_CUSTOMER_ID")

def _sig(ts, m, p, q="", b=""):
    msg = f"{ts}.{m}.{p}.{q}.{b}"
    return hmac.new(SK.encode(), msg.encode(), hashlib.sha256).hexdigest()

def _hdr(m, p, q="", body=None):
    ts = str(int(time.time()*1000))
    return {
        "X-Timestamp": ts,
        "X-API-KEY": AK,
        "X-Customer-Id": CID,
        "X-Signature": _sig(ts, m, p, q, json.dumps(body, separators=(",",":")) if body else ""),
    }

async def fetch_orders():
    """
    '변경 상품 주문 내역 조회' 엔드포인트 예시
    결제완료·상품준비중 건만 가져오고, 필요한 필드만 변환
    """
    async with aiohttp.ClientSession() as s:
        p = "/change-product-orders"
        q = "lastChangedFrom=2024-01-01T00:00:00&lastChangedTo=2099-12-31T23:59:59&status=ON_PAYMENT"
        async with s.get(f"{BASE}{p}?{q}", headers=_hdr("GET", p, q)) as r:
            r.raise_for_status()
            data = await r.json()
    orders = []
    for o in data["productOrderList"]:
        orders.append({
            "name": o["receiverName"],
            "contact": o["receiverContact1"],
            "address": f'{o["shippingAddress"]["base"]} {o["shippingAddress"]["detail"]}',
            "product": o["productName"],
            "box_count": o["orderQuantity"],
            "msg": o.get("etcMessage", ""),
            "platform_order_id": o["productOrderId"],
        })
    return orders
