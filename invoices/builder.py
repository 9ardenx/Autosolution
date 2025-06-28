from mapper.product_mapper import locate  # 제품명 → 창고코드 매핑 함수 (추후 구현)

def build_invoices(order: dict) -> list[dict]:
    """
    주문 1건을 여러 송장 레코드로 분해한다.
    order 예시:
      {
        "name": "홍길동",
        "contact": "010-1234-5678",
        "address": "서울 강남구 …",
        "product": "다크 격자 2박스",
        "box_count": 2,
        "msg": "부재 시 문 앞",
        "platform_order_id": "1234567890"
      }
    """
    primary, secondary = locate(order["product"])
    box = int(order["box_count"])
    full, remain = divmod(box, 2)

    invoices, seq = [], 0
    for _ in range(full):
        seq += 1
        invoices.append({**order,
                         "location": primary,
                         "qty": 1,
                         "seq": seq})
    if remain:
        seq += 1
        invoices.append({**order,
                         "location": secondary or primary,
                         "qty": 1,
                         "seq": seq})
    return invoices
