# fetchers/smartstore.py
import os
import time
import json
import hashlib
import hmac
import aiohttp
from datetime import datetime

# 환경변수 로드: .env 또는 Codespaces Secrets
ACCESS_KEY    = os.getenv("NAVER_ACCESS_KEY")
SECRET_KEY    = os.getenv("NAVER_SECRET_KEY")
CUSTOMER_ID   = os.getenv("NAVER_CUSTOMER_ID")
BASE_URL      = "https://api.commerce.naver.com"


def _sig(method: str, path: str, ts: str, body_str: str = "") -> str:
    """
    stringToSign 포맷: "{timestamp}.{method}.{path}.{body}"
    HMAC-SHA256(hex)
    """
    msg = f"{ts}.{method}.{path}.{body_str}"
    print(f"▶ Naver StringToSign: {msg}")
    sig = hmac.new(
        SECRET_KEY.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()
    print(f"▶ Naver Signature   : {sig}")
    return sig


def _hdr(method: str, path: str, body_obj=None) -> dict:
    """
    네이버 커머스 API 인증 헤더 생성
    """
    ts = str(int(time.time() * 1000))
    body_str = json.dumps(body_obj, separators=(",",":")) if body_obj else ""
    signature = _sig(method, path, ts, body_str)
    headers = {
        "X-API-KEY"    : ACCESS_KEY,
        "X-Customer-Id": CUSTOMER_ID,
        "X-Timestamp"  : ts,
        "X-Signature"  : signature,
        "Content-Type" : "application/json",
    }
    print(f"▶ Naver Headers   : {headers}")
    return headers


async def fetch_orders():
    """
    ON_PAYMENT 상태(결제완료) 주문 조회
    """
    # 날짜 필터: 오늘~오늘
    today = datetime.now().strftime('%Y-%m-%dT00:00:00')
    to_day = datetime.now().strftime('%Y-%m-%dT23:59:59')

    path = "/external/v1/pay-order/seller/product-orders/query"
    url  = f"{BASE_URL}{path}"

    body = {
        "createdAtFrom": today,
        "createdAtTo"  : to_day,
        "status"       : ["ON_PAYMENT"]
    }

    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, json=body, headers=_hdr("POST", path, body)) as resp:
            print(f"▶ Naver HTTP Status: {resp.status} {resp.reason}")
            text = await resp.text()
            print(f"▶ Naver Response   : {text[:200]}{'...' if len(text)>200 else ''}")
            resp.raise_for_status()
            data = await resp.json()

    orders = []
    # productOrderDtos 리스트 순회
    for dto in data.get("productOrderDtos", []):
        orders.append({
            "name": dto.get("receiverName"),
            "contact": dto.get("receiverPhone"),
            "address": dto.get("receiverAddr"),
            "product": dto.get("productName"),
            "box_count": dto.get("orderCount"),
            "msg": dto.get("memo", ""),
            "order_id": str(dto.get("orderId")),
        })
    return orders
