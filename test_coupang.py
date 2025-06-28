import os, time, hmac, hashlib, requests
from datetime import datetime

ACCESS = os.getenv("COUPANG_ACCESS_KEY")
SECRET = os.getenv("COUPANG_SECRET_KEY")
VENDOR = os.getenv("COUPANG_VENDOR_ID")
BASE   = "https://api-gateway.coupang.com"

method = "GET"
path   = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR}/ordersheets"

# 일 단위 조회 - yyyy-MM-dd 형식 사용
today = datetime.now()
created_at_from = today.strftime('%Y-%m-%d')  # 2025-06-28
created_at_to = today.strftime('%Y-%m-%d')    # 2025-06-28

# 수정된 쿼리 파라미터 (yyyy-MM-dd 형식)
query = f"createdAtFrom={created_at_from}&createdAtTo={created_at_to}&status=INSTRUCT&maxPerPage=1"
url = f"{BASE}{path}?{query}"

# 서명 생성 (나머지 코드 동일)
ts = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
sts = f"{ts}{method}{path}{query}"
sig = hmac.new(SECRET.encode(), sts.encode(), hashlib.sha256).hexdigest()

auth = (
    f"CEA algorithm=HmacSHA256, "
    f"access-key={ACCESS}, "
    f"signed-date={ts}, "
    f"signature={sig}"
)

headers = {
    "Authorization": auth,
    "X-Requested-By": VENDOR,
    "Content-Type": "application/json;charset=UTF-8"
}

resp = requests.get(url, headers=headers)
print("▶ HTTP STATUS :", resp.status_code)
print("▶ RESPONSE    :", resp.text)

