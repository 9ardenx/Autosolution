# main.py

import asyncio
import itertools
from dotenv import load_dotenv

from fetchers.smartstore import fetch_orders as ss_fetch
from fetchers.coupang    import fetch_orders as cp_fetch
from invoices.builder     import build_invoices
from exporter.csv_exporter import save_csv
from notifier.kakao        import send_file_link

load_dotenv()

async def run():
    # 1) 병렬 조회
    ss_orders, cp_orders = await asyncio.gather(
        ss_fetch(),
        cp_fetch()
    )

    print("SmartStore count:", len(ss_orders))
    print("Coupang count:",   len(cp_orders))

    # 2) 합치기
    all_orders = list(itertools.chain(ss_orders, cp_orders))

    # 3) 빌드 및 CSV
    invoices = []
    for o in all_orders:
        invoices.extend(build_invoices(o))
    csv_path = save_csv(invoices)
    print("CSV saved to", csv_path)

    # 4) 전송
    await send_file_link(csv_path)

if __name__ == "__main__":
    asyncio.run(run())

