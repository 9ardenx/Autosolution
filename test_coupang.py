import os, time, hmac, hashlib, requests
from datetime import datetime

ACCESS = os.getenv("COUPANG_ACCESS_KEY")
SECRET = os.getenv("COUPANG_SECRET_KEY")
VENDOR = os.getenv("COUPANG_VENDOR_ID")
BASE   = "https://api-gateway.coupang.com"

method = "GET"
path   = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR}/ordersheets"

# 필수 날짜 파라미터 추가
today = datetime.now()
created_at_from = today.strftime('%Y-%m-%dT00:00')
created_at_to = today.strftime('%Y-%m-%dT23:59')

# 수정된 쿼리 파라미터 (필수 파라미터 포함)
query = f"createdAtFrom={created_at_from}&createdAtTo={created_at_to}&status=INSTRUCT&maxPerPage=1"
url = f"{BASE}{path}?{query}"

# signed-date 생성
ts = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())

# StringToSign 생성
sts = f"{ts}{method}{path}{query}"
print("▶ StringToSign:", repr(sts))

# 서명 생성
sig = hmac.new(SECRET.encode(), sts.encode(), hashlib.sha256).hexdigest()
print("▶ Signature   :", sig)

# Authorization 헤더
auth = (
    f"CEA algorithm=HmacSHA256, "
    f"access-key={ACCESS}, "
    f"signed-date={ts}, "
    f"signature={sig}"
)
print("▶ Authorization:", auth)

# 헤더 설정 (X-Requested-By 필수)
headers = {
    "Authorization": auth,
    "X-Requested-By": VENDOR,
    "Content-Type": "application/json;charset=UTF-8"
}

# API 호출
resp = requests.get(url, headers=headers)
print("▶ HTTP STATUS :", resp.status_code)
print("▶ RESPONSE    :", resp.text)
