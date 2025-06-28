# test_coupang.py

import os, time, hmac, hashlib, requests

ACCESS = os.getenv("COUPANG_ACCESS_KEY")
SECRET = os.getenv("COUPANG_SECRET_KEY")
VENDOR = os.getenv("COUPANG_VENDOR_ID")
BASE   = "https://api-gateway.coupang.com"

method = "GET"
path   = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR}/ordersheets"
query  = "status=ACCEPT&page=1&maxPerPage=1"
url    = f"{BASE}{path}?{query}"

# 1) signed-date (UTC, yyMMddTHHmmssZ)
ts = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())

# 2) StringToSign = signed-date + method + path + query
sts = f"{ts}{method}{path}{query}"
print("▶ StringToSign:", repr(sts))

# 3) signature = HEX(HMAC-SHA256)
sig = hmac.new(SECRET.encode(), sts.encode(), hashlib.sha256).hexdigest()
print("▶ Signature   :", sig)

# 4) Authorization header (full format)
auth = (
    f"CEA algorithm=HmacSHA256, "
    f"access-key={ACCESS}, "
    f"signed-date={ts}, "
    f"signature={sig}"
)
print("▶ Authorization:", auth)

# 5) 반드시 X-Requested-By header 추가!
headers = {
    "Authorization": auth,
    "X-Requested-By": VENDOR,
    "Content-Type": "application/json;charset=UTF-8"
}

# 6) 호출
resp = requests.get(url, headers=headers)
print("▶ HTTP STATUS :", resp.status_code)
print("▶ RESPONSE    :", resp.text)

