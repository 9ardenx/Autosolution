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

# 2) stringToSign = signed-date + method + path + query
string_to_sign = f"{ts}{method}{path}{query}"
print("▶ stringToSign:", string_to_sign)

# 3) signature = HEX(HMAC-SHA256)
sig = hmac.new(SECRET.encode(), string_to_sign.encode(), hashlib.sha256).hexdigest()
print("▶ signature   :", sig)

# 4) full-format Authorization header
auth = (
    f"CEA algorithm=HmacSHA256, "
    f"access-key={ACCESS}, "
    f"signed-date={ts}, "
    f"signature={sig}"
)
print("▶ Authorization:", auth)

resp = requests.get(url, headers={
    "Authorization": auth,
    "Content-Type" : "application/json;charset=UTF-8"
})
print("▶ HTTP STATUS :", resp.status_code)
print("▶ RESPONSE    :", resp.text)
