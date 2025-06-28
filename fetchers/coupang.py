# fetchers/coupang.py

import os, time, hmac, hashlib, json, aiohttp
from datetime import datetime

ACCESS = os.getenv("COUPANG_ACCESS_KEY")
SECRET = os.getenv("COUPANG_SECRET_KEY") 
VENDOR = os.getenv("COUPANG_VENDOR_ID")
BASE   = "https://api-gateway.coupang.com"

def _hdr(method: str, path: str, query: str = "") -> dict:
    """v4 API용 CEA 인증 헤더 생성"""
    # signed-date 형식: yyMMddTHHmmssZ (GMT 기준)
    ts = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    
    # StringToSign = signed-date + method + path + query
    sts = f"{ts}{method}{path}{query}"
    
    # HMAC-SHA256 서명 생성
    sig = hmac.new(SECRET.encode(), sts.encode(), hashlib.sha256).hexdigest()
    
    # CEA 인증 헤더
    auth = (
        f"CEA algorithm=HmacSHA256, "
        f"access-key={ACCESS}, "
        f"signed-date={ts}, "
        f"signature={sig}"
    )
    
    return {
        "Authorization": auth,
        "X-Requested-By": VENDOR,  # v4에서는 필수
        "Content-Type": "application/json;charset=UTF-8"
    }

async def fetch_orders():
    """v4 API를 사용한 주문 조회"""
    # v4 API 엔드포인트
    path = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR}/ordersheets"
    
    # 오늘 날짜로 쿼리 파라미터 설정 (yyyy-MM-dd 형식)
    today = datetime.now()
    created_at_from = today.strftime('%Y-%m-%d')
    created_at_to = today.strftime('%Y-%m-%d')
    
    # 쿼리 파라미터
    query = f"createdAtFrom={created_at_from}&createdAtTo={created_at_to}&status=ACCEPT&maxPerPage=50"
    url = f"{BASE}{path}?{query}"

    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, headers=_hdr("GET", path, query)) as r:
            r.raise_for_status()
            data = await r.json()

    # 응답 데이터 파싱 (v4 형식)
    return [
        {
            "name"     : o["receiver"]["name"],
            "contact"  : o["receiver"]["receiverPhone"], 
            "address"  : f"{o['receiver']['baseAddress']} {o['receiver']['detailAddress']}".strip(),
            "product"  : o["productName"],
            "box_count": o["shippingCount"],
            "msg"      : o.get("deliveryMemo", ""),
            "order_id" : str(o["orderId"]),
        }
        for o in data.get("data", [])  # v4는 data 배열 사용
    ]
