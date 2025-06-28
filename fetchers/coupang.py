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

    # 응답 데이터 파싱 (수정된 필드명 사용)
    return [
        {
            "name"     : o["receiver"]["name"],
            "contact"  : o["receiver"]["receiverNumber"],  # ✅ 올바른 필드명으로 수정
            "address"  : f"{o['receiver']['addr1']} {o['receiver']['addr2']}".strip(),  # ✅ addr1, addr2로 수정
            "product"  : o["orderItems"][0]["vendorItemName"] if o["orderItems"] else "",  # ✅ orderItems 배열에서 가져오기
            "box_count": o["orderItems"][0]["shippingCount"] if o["orderItems"] else 0,   # ✅ orderItems에서 가져오기
            "msg"      : o.get("parcelPrintMessage", ""),  # ✅ 배송메시지 필드명 수정
            "order_id" : str(o["orderId"]),
        }
        for o in data.get("data", [])  # v4는 data 배열 사용
    ]

async def fetch_orders():
    # ... (앞부분 동일)
    
    # 더 안전한 파싱 로직
    return [
        {
            "name"     : o.get("receiver", {}).get("name", ""),
            "contact"  : o.get("receiver", {}).get("receiverNumber") or o.get("receiver", {}).get("safeNumber", ""),  # 실번호가 없으면 안심번호 사용
            "address"  : f"{o.get('receiver', {}).get('addr1', '')} {o.get('receiver', {}).get('addr2', '')}".strip(),
            "product"  : o.get("orderItems", [{}])[0].get("vendorItemName", "") if o.get("orderItems") else "",
            "box_count": o.get("orderItems", [{}])[0].get("shippingCount", 0) if o.get("orderItems") else 0,
            "msg"      : o.get("parcelPrintMessage", ""),
            "order_id" : str(o.get("orderId", "")),
        }
        for o in data.get("data", [])
    ]
