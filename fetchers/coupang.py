# fetchers/coupang.py

import os, time, hmac, base64, hashlib, json, aiohttp

ACCESS    = os.getenv("COUPANG_ACCESS_KEY")
SECRET    = os.getenv("COUPANG_SECRET_KEY")
VENDOR_ID = os.getenv("COUPANG_VENDOR_ID")
BASE_URL  = "https://api-gateway.coupang.com"

def _sig(path: str, method: str, ts: str) -> str:
    """
    stringToSign = "{method} {path}\\n{timestamp}\\n{accessKey}"
    signature    = Base64( HMAC-SHA256( secretKey, stringToSign ) )
    """
    # ➊ signature 대상 문자열
    string_to_sign = f"{method} {path}\n{ts}\n{ACCESS}"
    # —디버그용 프린트 (Postman 'Generate signature' 결과와 비교)
    print("▶ Coupang StringToSign:", repr(string_to_sign))

    # ➋ HMAC-SHA256 → Base64
    signature = base64.b64encode(
        hmac.new(SECRET.encode(), string_to_sign.encode(), hashlib.sha256).digest()
    ).decode()
    print("▶ Coupang Signature   :", signature)
    return signature

def _hdr(method: str, path: str) -> dict:
    """
    path 에는 반드시 '/v2/providers/.../ordersheets' 형태로,
    쿼리스트링 없이 전달해야 합니다.
    """
    ts = str(int(time.time() * 1000))
    return {
        "Authorization": f"CEA {ACCESS}:{_sig(path, method, ts)}",
        "X-Timestamp": ts,
        "Content-Type": "application/json",
    }

async def fetch_orders() -> list[dict]:
    """
    ACCEPT 상태(=결제완료) 주문만 가져옴.
    """
    # ➌ path 와 query를 분리
    path  = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR_ID}/ordersheets"
    query = "?status=ACCEPT&page=1&maxPerPage=50"
    url   = f"{BASE_URL}{path}{query}"

    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, headers=_hdr("GET", path)) as r:
            r.raise_for_status()
            data = await r.json()

    orders = []
    for o in data["orderSheetDtos"]:
        ship = o["shippingAddress"]
        orders.append({
            "name"             : ship["name"],
            "contact"          : ship["receiverPhone"],
            "address"          : f'{ship["baseAddress"]} {ship["detailAddress"]}'.strip(),
            "product"          : o["productName"],
            "box_count"        : o["shippingCount"],
            "msg"              : o.get("deliveryMemo", ""),
            "platform_order_id": str(o["orderId"]),
        })
    return orders
