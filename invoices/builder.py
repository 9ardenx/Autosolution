# invoices/builder.py

from mapper.product_mapper import locate

CSV_HEADER = [
    "이름", "연락처", "주소", "제품코드(옵션명)",
    "송장출력수량", "배송메시지", "송장출력번호"
]


def build_invoices(order: dict) -> list[dict]:
    """
    Parameters
    ----------
    order : {
        "name":      str,
        "contact":   str,
        "address":   str,
        "product":   str,   # 옵션명 포함된 상품명
        "box_count": int,
        "msg":       str
    }
    """
    primary, secondary = locate(order["product"])
    if primary is None:
        # 매칭 실패 → 스킵
        return []

    count = int(order["box_count"])
    full_sets, remaining = divmod(count, 2)

    invoices = []
    seq = 0

    # ① 2박스씩 primary
    for _ in range(full_sets):
        seq += 1
        invoices.append({
            CSV_HEADER[0]: order["name"],
            CSV_HEADER[1]: order["contact"],
            CSV_HEADER[2]: order["address"],
            CSV_HEADER[3]: primary,
            CSV_HEADER[4]: 1,
            CSV_HEADER[5]: order["msg"],
            CSV_HEADER[6]: seq,
        })

    # ② 남은 1박스 → secondary (낱장인 경우 secondary=None)
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


    return invoices

