# test_coupang.py
import os, time, hmac, hashlib, requests

# 1) 환경변수
ACCESS = os.getenv("COUPANG_ACCESS_KEY")
SECRET = os.getenv("COUPANG_SECRET_KEY")
VENDOR = os.getenv("COUPANG_VENDOR_ID")
BASE   = "https://api-gateway.coupang.com"

# 2) signed-date (GMT+0, yyMMddTHHmmssZ)
ts = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())

# 3) 엔드포인트 경로 & 쿼리
method = "GET"
path   = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR}/ordersheets"
query  = "status=ACCEPT&page=1&maxPerPage=1"
url    = f"{BASE}{path}?{query}"

# 4) StringToSign = signed-date + method + path + query
string_to_sign = f"{ts}{method}{path}{query}"
print("▶ StringToSign:", string_to_sign)

# 5) Signature = hex(HMAC-SHA256(secret, StringToSign))
sig = hmac.new(SECRET.encode(), string_to_sign.encode(), hashlib.sha256).hexdigest()
print("▶ Signature   :", sig)

# 6) Authorization 헤더 (풀 포맷)
auth = (
    f"CEA algorithm=HmacSHA256, "
    f"access-key={ACCESS}, signed-date={ts}, signature={sig}"
)
print("▶ Authorization:", auth)

# 7) 실제 호출
resp = requests.get(url, headers={
    "Authorization": auth,
    "Content-Type":  "application/json;charset=UTF-8"
})
print("▶ HTTP STATUS :", resp.status_code)
print("▶ RESPONSE    :", resp.text)
