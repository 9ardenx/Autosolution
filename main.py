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
    ss_orders, cp_orders = await asyncio.gather(
        ss_fetch(),
        cp_fetch()
    )
    print("SmartStore orders:", ss_orders)
    print("Coupang orders:",   cp_orders)

    invoices = build_invoices(itertools.chain(ss_orders, cp_orders))
    csv_path = save_csv(invoices)
    print(f"CSV saved to {csv_path}")

    await send_file_link(csv_path)

if __name__ == "__main__":
    asyncio.run(run())
