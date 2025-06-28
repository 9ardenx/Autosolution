"""
제품명 → (primary, secondary) 창고 코드 변환기
Apps Script 의 긴 if/else 분기를 딕셔너리 기반 룰로 1:1 변환.
"""

# ❶ 10장(=2박스) 세트 제품
MAP_10EA = {
    "다크 격자": ("C", "A"),
    "다크 일자": ("D", "B"),
    "허니 격자": ("G", "E"),
    "허니 일자": ("H", "F"),
}

# ❷ 낱장 제품 (secondary 없음)
MAP_SINGLE = {
    "허니브라운 12슬롯": "E 낱장",
    "허니브라운 6슬롯":  "F 낱장",
    "다크브라운 12슬롯": "A 낱장",
    "다크브라운 6슬롯":  "B 낱장",
}

def locate(product_name: str) -> tuple[str | None, str | None]:
    """
    Args
    ----
    product_name : 주문 상품명 문자열

    Returns
    -------
    (primary, secondary) : Tuple[str | None, str | None]
    """
    # ❶ 10장 세트 규칙
    for key, loc in MAP_10EA.items():
        if key in product_name:
            return loc

    # ❷ 낱장 규칙
    if "낱장" in product_name:
        for key, primary in MAP_SINGLE.items():
            if key in product_name:
                return (primary, None)

    # ❸ 나머지 – 기존 로직 (12 / 6 슬롯) 보정
    if "허니브라운 12슬롯" in product_name:
        return ("G", "E")
    if "허니브라운 6슬롯" in product_name:
        return ("H", "F")
    if "다크브라운 12슬롯" in product_name or "12슬롯" in product_name:
        return ("C", "A")
    if "다크브라운 6슬롯" in product_name or "6슬롯" in product_name:
        return ("D", "B")

    # 매칭 실패
    return (None, None)
