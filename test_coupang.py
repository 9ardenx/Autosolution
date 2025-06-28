# test_coupang.py

import os, time, hmac, hashlib, base64, requests

ACCESS = os.getenv("COUPANG_ACCESS_KEY")
SECRET = os.getenv("COUPANG_SECRET_KEY")
VENDOR = os.getenv("COUPANG_VENDOR_ID")

ts = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())   # GMT+0 형식: yyMMddTHHmmssZ
path = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR}/ordersheets"
query = "status=ACCEPT&page=1&maxPerPage=1"
string_to_sign = ts + "GET" + path + query         # = "signed-date + method + path + query"
print("▶ StringToSign:", string_to_sign)

sig = hmac.new(
    SECRET.encode(), 
    string_to_sign.encode(), 
    hashlib.sha256
).hexdigest()                                    # Hex 인코딩
print("▶ Signature   :", sig)

auth_header = (
    f"CEA algorithm=HmacSHA256, "
    f"access-key={ACCESS}, signed-date={ts}, signature={sig}"
)
print("▶ Authorization:", auth_header)

url = f"https://api-gateway.coupang.com{path}?{query}"
resp = requests.get(url, headers={
    "Authorization": auth_header,
    "Content-Type":  "application/json;charset=UTF-8",
})
print("▶ HTTP STATUS :", resp.status_code)
print("▶ RESPONSE    :", resp.text)
