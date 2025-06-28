# fetchers/coupang.py

import os
import time
import hmac
import hashlib
import json
import aiohttp
from datetime import datetime

ACCESS = os.getenv("COUPANG_ACCESS_KEY")
SECRET = os.getenv("COUPANG_SECRET_KEY")
VENDOR = os.getenv("COUPANG_VENDOR_ID")
BASE   = "https://api-gateway.coupang.com"

def _hdr(method: str, path: str, query: str = "") -> dict:
    """v4 API용 CEA 인증 헤더 생성"""
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

async def fetch_orders() -> list:
    """v4 API를 사용한 주문 조회 및 평탄화"""
    # 엔드포인트 설정 (yyyy-MM-dd 형식으로 오늘 하루 조회)
    today = datetime.now().strftime('%Y-%m-%d')
    path = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR}/ordersheets"
    query = f"createdAtFrom={today}&createdAtTo={today}&status=ACCEPT&maxPerPage=50"
    url = f"{BASE}{path}?{query}"

    # API 호출
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, headers=_hdr("GET", path, query)) as resp:
            resp.raise_for_status()
            resp_json = await resp.json()

    # 'data' 배열에서 각 orderSheetDto 평탄화
    results = []
    for o in resp_json.get("data", []):
        # 기본 주문 정보
        receiver = o.get("receiver", {})
        items = o.get("orderItems", [])
        # 아이템이 없으면 하나의 기본 레코드 생성
        if not items:
            results.append({
                "name":     receiver.get("name", ""),
                "contact":  receiver.get("receiverNumber", ""),
                "address":  f"{receiver.get('addr1','')} {receiver.get('addr2','')}".strip(),
                "product":  "", 
                "box_count": 0,
                "msg":      o.get("parcelPrintMessage", ""),
                "order_id": str(o.get("orderId", ""))
            })
        else:
            # 각 상품별로 레코드 생성
            for item in items:
                results.append({
                    "name":     receiver.get("name", ""),
                    "contact":  receiver.get("receiverNumber", ""),
                    "address":  f"{receiver.get('addr1','')} {receiver.get('addr2','')}".strip(),
                    "product":  item.get("vendorItemName", ""),
                    "box_count": item.get("shippingCount", 0),
                    "msg":      item.get("parcelPrintMessage", o.get("parcelPrintMessage", "")),
                    "order_id": str(o.get("orderId", ""))
                })

    return results

