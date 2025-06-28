# fetchers/smartstore.py

import os
import time
import json
import aiohttp
import asyncio
from datetime import datetime, timedelta
import bcrypt                # pip install bcrypt
import pybase64             # pip install pybase64

# 환경변수에서 읽어오기
CLIENT_ID     = os.getenv("NAVER_ACCESS_KEY")
CLIENT_SECRET = os.getenv("NAVER_SECRET_KEY")
CUSTOMER_ID   = os.getenv("NAVER_CUSTOMER_ID")
TOKEN_URL     = "https://api.commerce.naver.com/external/v1/oauth2/token"
ORDER_LIST_URL = "https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders"

class SmartStoreClient:
    def __init__(self):
        self.client_id     = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.customer_id   = CUSTOMER_ID
        self._token        = None
        self._expires_at   = 0  # UNIX timestamp

    async def _fetch_token(self) -> str:
        """토큰 발급/갱신 (Client Credentials Grant + 전자서명)"""
        timestamp = str(int((time.time() - 3) * 1000))
        raw = f"{self.client_id}_{timestamp}".encode("utf-8")
        signed = bcrypt.hashpw(raw, self.client_secret.encode("utf-8"))
        client_secret_sign = pybase64.standard_b64encode(signed).decode()

        data = {
            "client_id":          self.client_id,
            "timestamp":          timestamp,
            "client_secret_sign": client_secret_sign,
            "grant_type":         "client_credentials",
            "type":               "SELF"
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with aiohttp.ClientSession() as sess:
            async with sess.post(TOKEN_URL, data=data, headers=headers) as resp:
                resp.raise_for_status()
                js = await resp.json()

        token      = js["access_token"]
        expires_in = js.get("expires_in", 10800)
        self._token      = token
        self._expires_at = time.time() + expires_in - 60
        return token

    async def get_token(self) -> str:
        """유효한 토큰 반환 (필요 시 갱신)"""
        if not self._token or time.time() >= self._expires_at:
            return await self._fetch_token()
        return self._token

    async def fetch_orders(self,
                           created_from: str = None,
                           created_to:   str = None,
                           status:       list = None,
                           page_size:    int = 100,
                           page:         int = 1) -> list:
        """
        조건형 상품 주문 상세 내역 조회 (GET)
        - created_from/to: ISO 8601 "YYYY-MM-DDTHH:MM:SS" 형식
        - status: ["ON_PAYMENT", ...]
        """
        if created_from is None:
            created_from = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        if created_to is None:
            created_to = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        if status is None:
            status = ["ON_PAYMENT"]

        params = {
            "from":                 created_from,
            "to":                   created_to,
            "rangeType":            "PAYED_DATETIME",
            "productOrderStatuses": ",".join(status),
            "pageSize":             page_size,
            "page":                 page
        }
        headers = {
            "Authorization": f"Bearer {await self.get_token()}",
            "Content-Type":  "application/json",
            "X-Customer-Id":  self.customer_id
        }

        async with aiohttp.ClientSession() as sess:
            async with sess.get(ORDER_LIST_URL, params=params, headers=headers) as resp:
                resp.raise_for_status()
                result = await resp.json()

        return result.get("data", [])


smartstore_client = SmartStoreClient()
fetch_orders = smartstore_client.fetch_orders
