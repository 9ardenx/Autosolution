# test_coupang.py
import os, time, hmac, hashlib, base64, requests

# 1) 환경변수 읽기
ACCESS = os.getenv("COUPANG_ACCESS_KEY")
SECRET = os.getenv("COUPANG_SECRET_KEY")
VENDOR = os.getenv("COUPANG_VENDOR_ID")

# 2) 타임스탬프 (밀리초)
ts = str(int(time.time() * 1000))

# 3) Path (쿼리 제외)
path = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR}/ordersheets"

# 4) StringToSign 조합
string_to_sign = f"GET {path}\n{ts}\n{ACCESS}"
print("▶ StringToSign:", string_to_sign)

# 5) HMAC-SHA256 → Base64
signature = base64.b64encode(
    hmac.new(SECRET.encode(), string_to_sign.encode(), hashlib.sha256).digest()
).decode()
print("▶ Signature   :", signature)

# 6) 실제 호출
url = f"https://api-gateway.coupang.com{path}?status=ACCEPT&page=1&maxPerPage=1"
headers = {
    "Authorization": f"CEA {ACCESS}:{signature}",
    "X-Timestamp"  : ts,
    "Content-Type" : "application/json",
}

resp = requests.get(url, headers=headers)
print("▶ HTTP STATUS :", resp.status_code)
print("▶ RESPONSE    :", resp.text)
