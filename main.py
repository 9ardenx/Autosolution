import asyncio
from dotenv import load_dotenv

from fetchers.smartstore import smartstore_client
from fetchers.coupang import fetch_orders as cp_fetch
from invoices.builder import build_invoices
from exporter.csv_exporter import save_csv
from notifier.kakao import send_file_link  # TODO: 링크 함수 완성

# .env 파일 로드
load_dotenv()

async def run():
    # SmartStore와 Coupang 주문을 병렬로 조회
    ss_orders, cp_orders = await asyncio.gather(
        smartstore_client.fetch_orders(),
        cp_fetch()
    )
    print("SmartStore orders:", ss_orders)
    print("Coupang orders:", cp_orders)

    # 송장(인보이스) 빌드
    invoices = build_invoices(itertools.chain(ss_orders, cp_orders))

    # CSV 저장
    csv_path = save_csv(invoices)
    print(f"CSV saved to {csv_path}")

    # 카카오톡으로 링크 전송
    await send_file_link(csv_path)

if __name__ == "__main__":
    asyncio.run(run())
```
