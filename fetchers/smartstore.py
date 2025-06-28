# fetchers/smartstore.py

import os, time, json, hashlib, hmac, aiohttp

ACCESS_KEY     = os.getenv("NAVER_ACCESS_KEY")
SECRET_KEY     = os.getenv("NAVER_SECRET_KEY")
CUSTOMER_ID    = os.getenv("NAVER_CUSTOMER_ID")
BASE_URL       = "https://api.commerce.naver.com"

def _sig(method: str, path: str, ts: str, body: str = "") -> str:
    """
    StringToSign 포맷: "{timestamp}.{method}.{path}.{body}"
    Signature    : HMAC-SHA256(secretKey, StringToSign).hexdigest()
    """
    msg = f"{ts}.{method}.{path}.{body}"
    print("▶ Naver StringToSign:", msg)           # 디버그 출력
    sig = hmac.new(
        SECRET_KEY.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()
    print("▶ Naver Signature   :", sig)           # 디버그 출력
    return sig

def _hdr(method: str, path: str, body_obj=None) -> dict:
    """
    매 호출마다 timestamp 새로 생성 → HMAC 생성 → 헤더 반환
    """
    ts = str(int(time.time() * 1000))
    body_str = json.dumps(body_obj, separators=(",", ":")) if body_obj else ""
    sig = _sig(method, path, ts, body_str)
    return {
        "X-API-KEY"      : ACCESS_KEY,
        "X-Customer-Id"  : CUSTOMER_ID,
        "X-Timestamp"    : ts,
        "X-Signature"    : sig,
        "Content-Type"   : "application/json",
    }

async def fetch_orders():
    """
    v1 주문 판매자 API 예시 (ON_PAYMENT 상태 조회)
    """
    from_date = "2024-01-01T00:00:00"
    to_date   = "2099-12-31T23:59:59"

    # v1 한 방 조회 엔드포인트
    path = "/external/v1/pay-order/seller/product-orders/query"
    body = {
        "createdAtFrom": from_date,
        "createdAtTo"  : to_date,
        "status"       : ["ON_PAYMENT"],
    }
    url = f"{BASE_URL}{path}"

    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, json=body, headers=_hdr("POST", path, body)) as resp:
            print("▶ HTTP STATUS:", resp.status)
            text = await resp.text()
            print("▶ RESPONSE BODY:", text[:200], "…")  # 첫 200자만
            resp.raise_for_status()
            data = await resp.json()

    orders = []
    for dto in data.get("productOrderDtos", []):
        orders.append({
            "name"         : dto["receiverName"],
            "contact"      : dto["receiverPhone"],
            "address"      : dto["receiverAddr"].strip(),
            "product"      : dto["productName"],
            "box_count"    : dto["orderCount"],
            "msg"          : dto.get("memo", ""),
            "platform_id"  : str(dto["orderId"]),
        })
    return orders

