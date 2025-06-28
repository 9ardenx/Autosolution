import itertools, asyncio
from fetchers.smartstore import smartstore_client
from invoices.builder import build_invoices
from exporter.csv_exporter import save_csv
from notifier.kakao import send_file_link     # TODO: 링크 함수 완성
from dotenv import load_dotenv
load_dotenv()               # .env 값을 환경변수로 주입

import asyncio
from fetchers.smartstore import smartstore_client
from fetchers.coupang import fetch_orders as cp_fetch

async def run():
    # 함수 본문은 모두 이 아래 한 번만 들여쓰기 되어야 합니다.
    ss, cp = await asyncio.gather(
        smartstore_client.fetch_orders(),
        cp_fetch()
    )
    print("SmartStore orders:", ss)
    print("Coupang orders:", cp)

if __name__ == "__main__":
    asyncio.run(run())
