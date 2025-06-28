# fetchers/smartstore.py

import os
import time
import json
import bcrypt                # pip install bcrypt
import pybase64             # pip install pybase64
import aiohttp
import asyncio

# 환경변수에서 읽어오기
CLIENT_ID     = os.getenv("NAVER_ACCESS_KEY")
CLIENT_SECRET = os.getenv("NAVER_SECRET_KEY")
CUSTOMER_ID   = os.getenv("NAVER_CUSTOMER_ID")   # commerce API Center > My App > Customer ID
TOKEN_URL     = "https://api.commerce.naver.com/external/v1/oauth2/token"
ORDER_URL     = "https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders/query"

class SmartStoreClient:
    def __init__(self):
        self.client_id     = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.customer_id   = CUSTOMER_ID
        self._token        = None
        self._expires_at   = 0  # UNIX timestamp

    async def _fetch_token(self) -> str:
        """토큰 발급/갱신 (Client Credentials Grant + 전자서명)"""
        # 1) 타임스탬프 (밀리초) 생성 (API 서버와 5초 오차 허용)
        timestamp = str(int((time.time() - 3) * 1000))
        # 2) 전자서명 생성: bcrypt(client_id_timestamp, client_secret) → Base64
        raw_pwd = f"{self.client_id}_{timestamp}".encode("utf-8")
        signed = bcrypt.hashpw(raw_pwd, self.client_secret.encode("utf-8"))
        client_secret_sign = pybase64.standard_b64encode(signed).decode()

        # 3) 요청 파라미터 및 헤더
        data = {
            "client_id":            self.client_id,
            "timestamp":            timestamp,
            "client_secret_sign":   client_secret_sign,
            "grant_type":           "client_credentials",
            "type":                 "SELF"
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # 4) 토큰 요청
        async with aiohttp.ClientSession() as sess:
            async with sess.post(TOKEN_URL, data=data, headers=headers) as resp:
                resp.raise_for_status()
                resp_json = await resp.json()

        # 5) 토큰 저장 및 만료 시간 계산 (expires_in: 초)
        token       = resp_json["access_token"]
        expires_in  = resp_json.get("expires_in", 10800)
        self._token      = token
        self._expires_at = time.time() + expires_in - 60  # 마진 60초 전 갱신

        return token

    async def get_token(self) -> str:
        """유효한 토큰 반환 (필요 시 갱신)"""
        if not self._token or time.time() >= self._expires_at:
            return await self._fetch_token()
        return self._token

    async def fetch_orders(self,
                           createdAtFrom: str = "2024-01-01T00:00:00",
                           createdAtTo:   str = "2099-12-31T23:59:59",
                           status:        list = ["ON_PAYMENT"]) -> list:
        """
        주문 목록 조회
        - createdAtFrom/To: ISO 8601 (yyyy-MM-ddTHH:mm:ss)
        - status: ON_PAYMENT, IN_DELIVERY, DELIVERED 등
        """
        token = await self.get_token()

        payload = {
            "createdAtFrom": createdAtFrom,
            "createdAtTo":   createdAtTo,
            "status":        status
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
            "X-Customer-Id": self.customer_id
        }

        async with aiohttp.ClientSession() as sess:
            async with sess.post(ORDER_URL, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                result = await resp.json()

        # 필요에 따라 result["data"] 또는 result["productOrderDtos"] 구조에 맞춰 파싱
        return result.get("data", [])

# 전역 클라이언트 인스턴스
smartstore_client = SmartStoreClient()

# 예시: 단독 실행 시
if __name__ == "__main__":
    async def main():
        orders = await smartstore_client.fetch_orders(
            createdAtFrom="2025-06-28T00:00:00",
            createdAtTo=  "2025-06-28T23:59:59",
            status=["ON_PAYMENT"]
        )
        print(json.dumps(orders, indent=2, ensure_ascii=False))

    asyncio.run(main())
