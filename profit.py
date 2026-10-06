"""
profit.py — 상품별 순이익 계산 (기준정보 '계산 규칙' 시트를 코드로 옮긴 것)

순이익 = 정산금액 - 원가 x 수량 - 포장비 - 배송비 몫 - 광고비 몫 - 반품 비용
모든 금액은 원 단위 정수. 나눗셈은 몫(//)만 쓰고, 남는 원은 첫 줄에 붙임.
"""
import pandas as pd


def split_evenly(total, n):
    """total원을 n줄에 나눔. 예: 3000원을 2줄 → [1500, 1500], 1000원을 3줄 → [334, 333, 333]
    나머지를 버리면 합계가 원래 금액과 달라지므로, 남는 원은 첫 줄에 붙여 합계를 지킴."""
    share, rest = divmod(total, n)
    return [share + (rest if i == 0 else 0) for i in range(n)]


def split_by_qty(total, qtys):
    """total원을 수량 비율로 나눔. 예: 광고비 10000원, 수량 [1, 2] → [3334, 6666]"""
    whole = sum(qtys)
    parts = [total * q // whole for q in qtys]
    parts[0] += total - sum(parts)   # 버림으로 생긴 차이를 첫 줄에
    return parts


def build_lines(orders, settle, master):
    """주문 표를 기준으로, 정산 표의 정산금액을 붙여 '계산용 줄'을 만듦."""
    s = master["settings"]
    lines = orders[orders["상태"] != "취소"].copy()             # 취소는 계산에서 뺌
    lines = lines.sort_values(["쇼핑몰", "상품주문번호"]).reset_index(drop=True)

    paid = settle[["쇼핑몰", "상품주문번호", "정산금액"]]
    lines = lines.merge(paid, on=["쇼핑몰", "상품주문번호"], how="left", validate="one_to_one")
    lines["정산누락"] = (lines["상태"] == "구매확정") & lines["정산금액"].isna()
    lines["정산금액"] = lines["정산금액"].fillna(0).astype("int64")

    cost = master["cost"].set_index("상품코드")["원가"]
    confirmed = lines["상태"] == "구매확정"
    lines["원가합계"] = (lines["상품코드"].map(cost).fillna(0).astype("int64") * lines["수량"]).where(confirmed, 0)   # 반품은 상품이 돌아오니 원가 0
    lines["포장비"] = s["포장비"] * lines["수량"]
    lines["반품비용"] = (lines["상태"] == "반품").astype("int64") * s["반품 비용"]

    # 무료배송 주문: 주문 하나의 배송비를 그 주문의 상품 줄에 똑같이 나눔
    lines["배송비"] = 0
    for _, idx in lines[lines["배송비구분"] == "무료배송"].groupby(["쇼핑몰", "주문번호"]).groups.items():
        lines.loc[idx, "배송비"] = split_evenly(s["판매자 부담 배송비"], len(idx))

    # 광고비: 쇼핑몰+상품별 한 달 광고비를, 정산된 구매확정 수량대로 나눔
    lines["광고비"] = 0
    sold = lines[confirmed & ~lines["정산누락"]]
    unsold_ads = []
    for _, ad in master["ads"].iterrows():
        target = sold[(sold["쇼핑몰"] == ad["쇼핑몰"]) & (sold["상품코드"] == ad["상품코드"])]
        if target.empty:
            unsold_ads.append({"쇼핑몰": ad["쇼핑몰"], "상품코드": ad["상품코드"], "광고비": int(ad["광고비"])})
            continue
        lines.loc[target.index, "광고비"] += split_by_qty(int(ad["광고비"]), list(target["수량"]))

    lines["순이익"] = (lines["정산금액"] - lines["원가합계"] - lines["포장비"]
                      - lines["배송비"] - lines["광고비"] - lines["반품비용"])
    return lines, unsold_ads


def summarize(lines, unsold_ads):
    """쇼핑몰+상품별로 더함. 정산 누락 줄은 빼고(받을 돈으로 따로), 판매 없는 광고비는 손실로 더함."""
    counted = lines[~lines["정산누락"]]
    money = ["정산금액", "원가합계", "포장비", "배송비", "광고비", "반품비용", "순이익"]
    sold_qty = counted[counted["상태"] == "구매확정"].groupby(["쇼핑몰", "상품코드"])["수량"].sum()
    table = counted.groupby(["쇼핑몰", "상품코드"])[money].sum()
    table.insert(0, "판매수량", sold_qty)
    table = table.fillna(0).astype("int64").reset_index()
    for ad in unsold_ads:
        hit = (table["쇼핑몰"] == ad["쇼핑몰"]) & (table["상품코드"] == ad["상품코드"])
        if not hit.any():   # 그 쇼핑몰에서 한 번도 안 팔린 상품이면 빈 줄을 하나 만듦
            empty = {"쇼핑몰": ad["쇼핑몰"], "상품코드": ad["상품코드"], "판매수량": 0, **{k: 0 for k in money}}
            table = pd.concat([table, pd.DataFrame([empty])], ignore_index=True)
            hit = (table["쇼핑몰"] == ad["쇼핑몰"]) & (table["상품코드"] == ad["상품코드"])
        table.loc[hit, "광고비"] += ad["광고비"]
        table.loc[hit, "순이익"] -= ad["광고비"]
    return table.sort_values(["쇼핑몰", "상품코드"]).reset_index(drop=True)
