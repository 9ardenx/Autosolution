# test_coupang.py
import os, time, hmac, hashlib, base64, requests

ACCESS = os.getenv("COUPANG_ACCESS_KEY")
SECRET = os.getenv("COUPANG_SECRET_KEY")
VENDOR = os.getenv("COUPANG_VENDOR_ID")
BASE   = "https://api-gateway.coupang.com"

method = "GET"
path   = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR}/ordersheets"
query  = "status=ACCEPT&page=1&maxPerPage=1"
url    = f"{BASE}{path}?{query}"

# 1) 타임스탬프
ts = str(int(time.time() * 1000))

# 2) StringToSign (한 문자열로 세 줄을 결합)
string_to_sign = f"{method} {path}?{query}\n{ts}\n{ACCESS}"
print("▶ StringToSign:", repr(string_to_sign))

# 3) Signature (Base64)
sig = base64.b64encode(
    hmac.new(SECRET.encode(), string_to_sign.encode(), hashlib.sha256).digest()
).decode()
print("▶ Signature   :", sig)

# 4) 헤더 세팅
headers = {
    "Authorization": f"CEA {ACCESS}:{sig}",
    "X-Timestamp": ts,
}

# 5) 호출
resp = requests.get(url, headers=headers)
print("▶ HTTP STATUS :", resp.status_code)
print("▶ RESPONSE    :", resp.text)
