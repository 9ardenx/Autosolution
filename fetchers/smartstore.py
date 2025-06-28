# fetchers/smartstore.py

import os, time, json, aiohttp, asyncio
from datetime import datetime, timedelta

CLIENT_ID     = os.getenv("NAVER_ACCESS_KEY")
CLIENT_SECRET = os.getenv("NAVER_SECRET_KEY")
CUSTOMER_ID   = os.getenv("NAVER_CUSTOMER_ID")

ORDER_LIST_URL = "https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders"

async def fetch_orders(created_from: str,
                       created_to:   str,
                       status:       list,
                       page_size:    int = 50,
                       page:         int = 1) -> list:
    """
    조건형 상품 주문 상세 내역 조회
    GET /external/v1/pay-order/seller/product-orders
    """
    params = {
        "from":               created_from,
        "to":                 created_to,
        "rangeType":          "PAYED_DATETIME",       # 결제 완료 시각 기준
        "productOrderStatuses": ",".join(status),     # 예: "ON_PAYMENT"
        "pageSize":           page_size,
        "page":               page
    }
    headers = {
        "Authorization": f"Bearer {await get_token()}",
        "Content-Type":  "application/json",
        "X-Customer-Id": CUSTOMER_ID
    }

    async with aiohttp.ClientSession() as sess:
        async with sess.get(ORDER_LIST_URL, params=params, headers=headers) as resp:
            resp.raise_for_status()
            result = await resp.json()

    # 결과 구조: result["data"]에 주문 리스트
    return result.get("data", [])

# 토큰 발급 로직 (기존 get_token/_fetch_token 메서드 활용)
# ...

# 사용 예시
if __name__ == "__main__":
    async def main():
        # 오늘 하루 결제완료 주문 조회
        today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        orders = await fetch_orders(
            created_from=yesterday,
            created_to=today,
            status=["ON_PAYMENT"],
            page_size=100,
            page=1
        )
        print(json.dumps(orders, indent=2, ensure_ascii=False))

    asyncio.run(main())
