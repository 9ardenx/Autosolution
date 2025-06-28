# main.py

import asyncio
import itertools
from dotenv import load_dotenv

from fetchers.smartstore import fetch_orders as ss_fetch
from fetchers.coupang    import fetch_orders as cp_fetch
from invoices.builder     import build_invoices
from exporter.csv_exporter import save_csv
from notifier.kakao        import send_file_link

# .env 파일 로드
load_dotenv()

async def run():
    # SmartStore와 Coupang 주문을 병렬 조회
    ss_raw, cp_orders = await asyncio.gather(
        ss_fetch(),
        cp_fetch()
    )

    # SmartStore API 응답이 dict 형태라면 'contents' 키를 사용, 아니면 그대로 리스트로 사용
    if isinstance(ss_raw, dict):
        ss_orders = ss_raw.get("contents", [])
    else:
        ss_orders = ss_raw

    print("SmartStore orders count:", len(ss_orders))
    print("Coupang orders count:",   len(cp_orders))

    # SmartStore와 Coupang 주문 리스트를 합쳐 인보이스 빌더에 전달
    combined_orders = list(itertools.chain(ss_orders, cp_orders))
    invoices = build_invoices(combined_orders)

    # CSV로 저장
    csv_path = save_csv(invoices)
    print(f"CSV saved to {csv_path}")

    # 카카오톡으로 링크 전송
    await send_file_link(csv_path)

if __name__ == "__main__":
    asyncio.run(run())
