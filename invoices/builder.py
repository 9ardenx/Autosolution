# invoices/builder.py

"""
주문 dict → 여러 송장 레코드(list[dict]) 생성
옵션명 키워드에 따른 primary/secondary 매핑 로직 포함
"""

CSV_HEADER = [
    "이름", "연락처", "주소", "제품코드(옵션명)",
    "송장출력수량", "배송메시지", "송장출력번호"
]

def locate(product_name: str) -> tuple[str|None, str|None]:
    """
    옵션명(product_name) 키워드 기준으로
    primaryLocation, secondaryLocation을 반환.
    일치 없으면 (None, None)
    """
    # 1) 10장 세트(격자 vs 일자, 다크 vs 허니)
    if "다크 격자" in product_name:
        return "C", "A"
    if "다크 일자" in product_name:
        return "D", "B"
    if "허니 격자" in product_name:
        return "G", "E"
    if "허니 일자" in product_name:
        return "H", "F"

    # 2) 낱장 옵션
    if "낱장" in product_name:
        if "허니브라운 12슬롯" in product_name:
            return "E 낱장", None
        if "허니브라운 6슬롯" in product_name:
            return "F 낱장", None
        if "다크브라운 12슬롯" in product_name or "12슬롯" in product_name:
            return "A 낱장", None
        if "다크브라운 6슬롯" in product_name or "6슬롯" in product_name:
            return "B 낱장", None
        return None, None

    # 3) 기존(4장 세트) 옵션
    if "허니브라운 12슬롯" in product_name:
        return "G", "E"
    if "허니브라운 6슬롯" in product_name:
        return "H", "F"
    if "다크브라운 12슬롯" in product_name or "12슬롯" in product_name:
        return "C", "A"
    if "다크브라운 6슬롯" in product_name or "6슬롯" in product_name:
        return "D", "B"

    return None, None


def build_invoices(order: dict) -> list[dict]:
    """
    Parameters
    ----------
    order : {
        "name":      str,
        "contact":   str,
        "address":   str,
        "product":   str,  # 옵션명 포함
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

    # 1) 2박스씩 (primary)
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

    # 2) 남은 1박스 (secondary, 낱장은 secondary=None → 본문 건너뜀)
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

