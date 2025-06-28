# test_coupang.py
import os, time, hmac, hashlib, base64, requests

ACCESS = os.getenv("COUPANG_ACCESS_KEY")
SECRET = os.getenv("COUPANG_SECRET_KEY")
VENDOR = os.getenv("COUPANG_VENDOR_ID")

# 1. 타임스탬프 (밀리초)
ts = str(int(time.time() * 1000))

# 2. 엔드포인트 경로 & 쿼리
path  = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR}/ordersheets"
query = "status=ACCEPT&page=1&maxPerPage=1"
url   = f"https://api-gateway.coupang.com{path}?{query}"

# 3. StringToSign (method + ' ' + path + '\n' + timestamp + '\n' + accessKey)
string_to_sign = f"GET {path}\n{ts}\n{ACCESS}"
print("▶ StringToSign:", string_to_sign)

# 4. Signature = Base64( HMAC-SHA256(secretKey, StringToSign) )
sig = base64.b64encode(
    hmac.new(SECRET.encode(), string_to_sign.encode(), hashlib.sha256).digest()
).decode()
print("▶ Signature   :", sig)

# 5. 헤더 조합 (신규 v4 포맷)
headers = {
    "Authorization": f"CEA {ACCESS}:{sig}",
    "X-Timestamp": ts,
}

# 6. 호출 & 결과
resp = requests.get(url, headers=headers)
print("▶ HTTP STATUS :", resp.status_code)
print("▶ RESPONSE    :", resp.text)
