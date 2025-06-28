async def fetch_orders():
    # ─── egress IP 찍기 ───────────────────
    async with aiohttp.ClientSession() as sess:
        async with sess.get("https://ifconfig.me/ip") as r:
            real_ip = (await r.text()).strip()
            print("▶ Real Egress IP:", real_ip)
    # ────────────────────────────────────────

    # 기존 주문 조회 로직…
    async with aiohttp.ClientSession() as sess:
        path  = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR_ID}/ordersheets"
        query = "?status=ACCEPT&page=1&maxPerPage=50"
        url   = f"{BASE}{path}{query}"
        async with sess.get(url, headers=_hdr("GET", path)) as r:
            r.raise_for_status()
            data = await r.json()
    # …

import os, time, hmac, base64, hashlib, json, aiohttp

ACCESS    = os.getenv("COUPANG_ACCESS_KEY")
SECRET    = os.getenv("COUPANG_SECRET_KEY")
VENDOR_ID = os.getenv("COUPANG_VENDOR_ID")
BASE_URL  = "https://api-gateway.coupang.com"

import time, hmac, base64, hashlib

ACCESS    = os.getenv("COUPANG_ACCESS_KEY")
SECRET    = os.getenv("COUPANG_SECRET_KEY")
VENDOR_ID = os.getenv("COUPANG_VENDOR_ID")

def _sig(path: str, method: str, ts: str) -> str:
    string_to_sign = f"{method} {path}\n{ts}\n{ACCESS}"
    # 디버그 출력 (원하는 경우만)
    print("▶ StringToSign:", repr(string_to_sign))
    signature = base64.b64encode(
        hmac.new(SECRET.encode(), string_to_sign.encode(), hashlib.sha256).digest()
    ).decode()
    print("▶ Signature   :", signature)
    return signature

def _hdr(method: str, path: str) -> dict:
    ts = str(int(time.time() * 1000))
    sig = _sig(path, method, ts)
    return {
        "Authorization": f"CEA {ACCESS}:{sig}",
        "X-Timestamp"  : ts,
        "Content-Type" : "application/json",
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
