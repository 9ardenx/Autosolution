# fetchers/smartstore.py

import os, time, aiohttp, bcrypt, pybase64
from datetime import datetime, timedelta, timezone

CLIENT_ID     = os.getenv("NAVER_ACCESS_KEY")
CLIENT_SECRET = os.getenv("NAVER_SECRET_KEY")
CUSTOMER_ID   = os.getenv("NAVER_CUSTOMER_ID")
TOKEN_URL     = "https://api.commerce.naver.com/external/v1/oauth2/token"
ORDER_URL     = "https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders"

async def _fetch_token():
    ts = str(int((time.time()-3)*1000))
    raw = f"{CLIENT_ID}_{ts}".encode()
    signed = bcrypt.hashpw(raw, CLIENT_SECRET.encode())
    sign = pybase64.standard_b64encode(signed).decode()
    data = {"client_id":CLIENT_ID, "timestamp":ts,
            "client_secret_sign":sign,
            "grant_type":"client_credentials","type":"SELF"}
    hdr = {"Content-Type":"application/x-www-form-urlencoded"}
    async with aiohttp.ClientSession() as s:
        async with s.post(TOKEN_URL, data=data, headers=hdr) as r:
            r.raise_for_status()
            js = await r.json()
    token = js["access_token"]
    _fetch_token._token = token
    _fetch_token._expiry = time.time() + js.get("expires_in",3600)-60
    return token

async def _get_token():
    if not getattr(_fetch_token, "_token", None) or time.time()>=getattr(_fetch_token,"_expiry",0):
        return await _fetch_token()
    return _fetch_token._token

async def fetch_orders(
    createdFrom: str=None,
    createdTo:   str=None,
    status:      list=None
):
    # 기본 24h 범위
    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST)
    if not createdFrom:
        createdFrom = (now - timedelta(days=1)).isoformat(timespec="milliseconds")
    if not createdTo:
        createdTo   = now.isoformat(timespec="milliseconds")
    if not status:
        status = ["PAYED"]

    params = {
        "from":                  createdFrom,
        "to":                    createdTo,
        "rangeType":             "PAYED_DATETIME",
        "productOrderStatuses":  ",".join(status),
        "pageSize":              100,
        "page":                  1
    }
    token = await _get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Customer-Id": CUSTOMER_ID,
        "Content-Type":  "application/json"
    }
    async with aiohttp.ClientSession() as s:
        async with s.get(ORDER_URL, params=params, headers=headers) as r:
            r.raise_for_status()
            js = await r.json()

    out = []
    for o in js.get("data", []):
        # productOrderDtos 배열 중 첫 번째 옵션명 사용
        item = (o.get("productOrderDtos") or [{}])[0]
        out.append({
            "name":      o.get("receiverName", ""),
            "contact":   o.get("receiverContactTelephone",""),
            "address":   f\"{o.get('receiverBaseAddress','')} {o.get('receiverDetailAddress','')}".strip(),
            "product":   item.get("vendorItemName",""),  # 옵션명
            "box_count": item.get("orderCount",1),
            "msg":        item.get("parcelPrintMessage", o.get("orderMemo","")),
            "order_id":   str(o.get("orderId",""))
        })
    return out


