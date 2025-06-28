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
    # 1) SmartStore와 Coupang 주문을 병렬 조회
    ss_raw, cp_orders = await asyncio.gather(
        ss_fetch(),   # SmartStore 원시 응답 리스트 또는 dict
        cp_fetch()    # Coupang에서 이미 평탄화된 주문 리스트
    )

    # 2) SmartStore 원시 응답을 빌더가 기대하는 평탄화된 리스트로 변환
    ss_orders = []
    for o in (ss_raw if isinstance(ss_raw, list) else ss_raw.get("contents", [])):
        # 공통 주문 정보 베이스
        base = {
            "name":     o.get("receiverName", ""),
            "contact":  o.get("receiverPhone", ""),
            "address":  f"{o.get('receiverBaseAddress','')} {o.get('receiverDetailAddress','')}".strip(),
            "msg":      o.get("orderMemo", ""),
            "order_id": str(o.get("orderId", "")),
        }
        # 각 상품별로 하나씩 분리
        for item in o.get("productOrderDtos", []):
            ss_orders.append({
                **base,
                "product":   item.get("vendorItemName", ""),
                "box_count": item.get("orderCount", 1),
                "msg":        item.get("parcelPrintMessage", base["msg"])
            })

    print("SmartStore orders count:", len(ss_orders))
    print("Coupang orders count:",   len(cp_orders))

    # 3) 두 리스트를 합쳐 인보이스 빌더에 전달
    combined_orders = list(itertools.chain(ss_orders, cp_orders))
    invoices = build_invoices(combined_orders)

    # 4) CSV로 저장
    csv_path = save_csv(invoices)
    print(f"CSV saved to {csv_path}")

    # 5) 카카오톡으로 링크 전송
    await send_file_link(csv_path)

if __name__ == "__main__":
    asyncio.run(run())

