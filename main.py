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
    # SmartStore와 Coupang 주문을 병렬 조회
    ss_data, cp_orders = await asyncio.gather(
        ss_fetch(),
        cp_fetch()
    )

    # SmartStore 반환값이 dict이면 contents 키의 리스트를 사용
    if isinstance(ss_data, dict):
        ss_orders = ss_data.get("contents", [])
    else:
        ss_orders = ss_data

    print("SmartStore orders count:", len(ss_orders))
    print("Coupang orders count:",   len(cp_orders))

    # 주문 리스트 합치기
    combined_orders = list(itertools.chain(ss_orders, cp_orders))

    # 방어막: 딕셔너리가 아닌 항목은 제거
    clean_orders = [o for o in combined_orders if isinstance(o, dict)]

    # 인보이스 생성 및 CSV 저장
    invoices = build_invoices(clean_orders)
    csv_path = save_csv(invoices)
    print(f"CSV saved to {csv_path}")

    # 카카오톡으로 링크 전송
    await send_file_link(csv_path)

if __name__ == "__main__":
    asyncio.run(run())


