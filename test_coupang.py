# test_coupang.py
import os, time, hmac, hashlib, base64, requests

ACCESS = os.getenv("COUPANG_ACCESS_KEY")
SECRET = os.getenv("COUPANG_SECRET_KEY")
VENDOR = os.getenv("COUPANG_VENDOR_ID")
BASE   = "https://api-gateway.coupang.com"

# 1) 타임스탬프 (밀리초)
ts = str(int(time.time() * 1000))

# 2) 경로+쿼리
path  = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR}/ordersheets"
query = "status=ACCEPT&page=1&maxPerPage=1"

# 3) StringToSign (쿼리 포함)
string_to_sign = f"GET {path}?{query}\n{ts}\n{ACCESS}"
print("▶ StringToSign:", string_to_sign)

# 4) Signature = Base64(HMAC-SHA256)
sig = base64.b64encode(
    hmac.new(SECRET.encode(), string_to_sign.encode(), hashlib.sha256).digest()
).decode()
print("▶ Signature   :", sig)

# 5) 헤더 조합
headers = {
    "Authorization": f"CEA {ACCESS}:{sig}",
    "X-Timestamp":   ts,
}

# 6) 요청
url = f"{BASE}{path}?{query}"
resp = requests.get(url, headers=headers)
print("▶ HTTP STATUS :", resp.status_code)
print("▶ RESPONSE    :", resp.text)
