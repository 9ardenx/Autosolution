import os, time, hmac, base64, hashlib, json, aiohttp
ACCESS, SECRET, VENDOR_ID = os.getenv("COUPANG_ACCESS_KEY"), os.getenv("COUPANG_SECRET_KEY"), os.getenv("COUPANG_VENDOR_ID")
BASE = "https://api-gateway.coupang.com"

def _sig(path, method, ts):
    msg = f"{method} {path}\n{ts}\n{ACCESS}"
    return base64.b64encode(hmac.new(SECRET.encode(), msg.encode(), hashlib.sha256).digest()).decode()

def _hdr(method, path):
    ts = str(int(time.time()*1000))
    return {
        "Authorization": f"CEA {ACCESS}:{_sig(path, method, ts)}",
        "Content-Type": "application/json",
        "X-Timestamp": ts,
    }

async def fetch_orders():
    """
    ACCEPT 상태(=결제완료) 주문만 가져옴.
    ※ 쿠팡은 고객 정보 암호화 필드가 많아 decrypt API 쿼리 필요할 수 있음.
    """
    async with aiohttp.ClientSession() as sess:
        path = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR_ID}/ordersheets"
        query = "?status=ACCEPT&page=1&maxPerPage=50"
        url = f"{BASE}{path}{query}"
        async with sess.get(url, headers=_hdr("GET", path)) as r:
            r.raise_for_status()
            data = await r.json()

    orders = []
    for o in data["orderSheetDtos"]:
        ship = o["shippingAddress"]
        orders.append({
            "name"  : ship["name"],
            "contact": ship["receiverPhone"],
            "address": f'{ship["baseAddress"]} {ship["detailAddress"]}'.strip(),
            "product": o["productName"],
            "box_count": o["shippingCount"],         # 수량
            "msg"   : o.get("deliveryMemo", ""),
            "platform_order_id": str(o["orderId"]),
        })
    return orders
