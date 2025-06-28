"""
주문 dict → 여러 송장 레코드(list[dict]) 생성
원본 Apps Script 의 ‘송장출력’ 반복문을 그대로 옮김.
"""

from mapper.product_mapper import locate

CSV_HEADER = ["이름", "연락처", "주소", "제품명",
              "송장출력수량", "배송메시지", "송장출력번호"]


def build_invoices(order: dict) -> list[dict]:
    """
    Parameters
    ----------
    order : {
        "name": str,
        "contact": str,
        "address": str,
        "product": str,
        "box_count": int | str,
        "msg": str
    }

    Returns
    -------
    invoices : list[dict]  # CSV 헤더 순서의 행 dict
    """
    primary, secondary = locate(order["product"])
    if primary is None:
        # 매칭 실패 → 스킵
        return []

    box_cnt = int(order["box_count"])
    full_sets, remaining = divmod(box_cnt, 2)

    invoices, seq = [], 0
    # ❶ 2박스씩 나갈 송장
    for _ in range(full_sets):
        seq += 1
        invoices.append({
            CSV_HEADER[0]: order["name"],
            CSV_HEADER[1]: order["contact"],
            CSV_HEADER[2]: order["address"],
            CSV_HEADER[3]: primary,
            CSV_HEADER[4]: 1,            # 송장 출력 수량 = 1
            CSV_HEADER[5]: order["msg"],
            CSV_HEADER[6]: seq,
        })

    # ❷ 1박스 남으면 secondary 코드로 한 번 더
    if remaining and secondary:
        seq += 1
        invoices.append({
            CSV_HEADER[0]: order["name"],
            CSV_HEADER[1]: order["contact"],
            CSV_HEADER[2]: order["address"],
            CSV_HEADER[3]: secondary,
            CSV_HEADER[4]: 1,
            CSV_HEADER[5]: order["msg"],
            CSV_HEADER[6]: seq,
        })

    return invoices
