# fetchers/smartstore.py

import os, aiohttp, asyncio
from datetime import datetime, timedelta, timezone

CLIENT_ID   = os.getenv("NAVER_ACCESS_KEY")
CLIENT_SECRET = os.getenv("NAVER_SECRET_KEY")
CUSTOMER_ID = os.getenv("NAVER_CUSTOMER_ID")
ORDER_LIST_URL = "https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders"

async def fetch_orders(
    created_from: str = None,
    status:         list = None,
    page_size:      int = 100,
    page:           int = 1
) -> list:
    """
    조건형 상품 주문 상세 내역 조회 (GET)
    - 조회 기준 시작 일시(created_from): ISO 8601 "YYYY-MM-DDTHH:MM:SS.sss±TZ" 형식 필수
    - to 파라미터 생략 시 from부터 24시간 내역 자동 조회
    - status 예: ["ON_PAYMENT"], ["IN_DELIVERY"], ["DELIVERED"]
    """
    # 1) 기본 생성: 24시간 전부터 지금까지
    now = datetime.now(timezone.utc).astimezone()
    if created_from is None:
        created_from = (now - timedelta(days=1)).isoformat(timespec="milliseconds")
    if status is None:
        status = ["ON_PAYMENT"]

    # 2) 쿼리 파라미터
    params = {
        "from":                 created_from,
        "rangeType":            "PAYED_DATETIME",
        "productOrderStatuses": ",".join(status),
        "pageSize":             page_size,
        "page":                 page
    }
    # (참고) to 포함하려면 아래처럼 추가하되, created_from 대비 24시간 미만인지 확인 필요
    # params["to"] = now.isoformat(timespec="milliseconds")

    # 3) 토큰 발급 로직은 기존 get_token()/ _fetch_token() 활용
    token = await smartstore_client.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "X-Customer-Id": CUSTOMER_ID
    }

    # 4) API 호출
    async with aiohttp.ClientSession() as sess:
        async with sess.get(ORDER_LIST_URL, params=params, headers=headers) as resp:
            resp.raise_for_status()  # 400 Bad Request → 예외 발생
            data = await resp.json()

    return data.get("data", [])

