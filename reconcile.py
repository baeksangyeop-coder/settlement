"""
reconcile.py — 주문과 정산을 맞대 봐서 '받아야 할 돈을 다 받았는지' 확인

찾는 것
1. 정산 누락: 구매확정인데 정산이 없음 → 받을 돈
2. 있으면 안 되는 정산: 취소, 반품 주문인데 정산이 있음, 또는 주문 내역에 없는 정산
3. 금액 오류: 정산금액 계산이 안 맞음 / 수수료율이 평소와 다름 / 주문 금액과 정산 판매금액이 다름 / 수량이 다름

'평소 수수료율'은 숫자를 코드에 적어 두지 않고, 그 달 데이터에서 쇼핑몰별 가운뎃값으로 구함.
(쇼핑몰이 수수료 정책을 바꿔도 코드를 고칠 필요가 없게)
"""
import pandas as pd

RATE_GAP = 0.01   # 평소 수수료율과 1%p 넘게 다르면 확인 필요


def typical_rates(settle):
    """쇼핑몰별 평소 수수료율 (가운뎃값). 평균은 이상한 값 하나에 끌려가서 가운뎃값을 씀."""
    rate = settle["수수료"] / settle["판매금액"]
    return rate.groupby(settle["쇼핑몰"]).median().to_dict()


def reconcile(orders, settle):
    issues = []
    add = lambda kind, row, text, money=0: issues.append({
        "종류": kind, "쇼핑몰": row["쇼핑몰"], "상품주문번호": row["상품주문번호"],
        "상품": row.get("쇼핑몰상품명", ""), "내용": text, "금액": int(money)})

    rates = typical_rates(settle)
    both = orders.merge(settle, on=["쇼핑몰", "상품주문번호"], how="outer",
                        suffixes=("_주문", "_정산"), indicator=True, validate="one_to_one")
    # outer로 이으면 한쪽에만 있는 줄의 빈칸 때문에 금액이 소수(1000.0)가 됨 → 빈칸을 허용하는 정수로 되돌림 (3단계와 같은 문제)
    for col in ["수량_주문", "판매금액_주문", "수량_정산", "판매금액_정산", "수수료", "정산금액"]:
        both[col] = both[col].astype("Int64")

    for _, r in both.iterrows():
        row = {"쇼핑몰": r["쇼핑몰"], "상품주문번호": r["상품주문번호"],
               "쇼핑몰상품명": r["쇼핑몰상품명_주문"] if pd.notna(r.get("쇼핑몰상품명_주문")) else r.get("쇼핑몰상품명_정산", "")}

        if r["_merge"] == "left_only":            # 주문만 있음
            if r["상태"] == "구매확정":
                expected = r["판매금액_주문"] - int(r["판매금액_주문"] * rates[r["쇼핑몰"]])
                add("정산 누락", row, f"구매확정({r['주문일_주문']} 주문)인데 정산이 없음. 예상 정산금액 약 {expected:,}원", expected)
            continue                               # 취소, 반품은 정산이 없는 게 정상
        if r["_merge"] == "right_only":           # 정산만 있음
            add("주문 없는 정산", row, "정산은 있는데 주문 내역에 없음", r["정산금액"])
            continue

        # 둘 다 있음
        if r["상태"] != "구매확정":
            add("있으면 안 되는 정산", row, f"주문 상태가 '{r['상태']}'인데 정산이 있음", r["정산금액"])
        gap = r["판매금액_정산"] - r["수수료"] - r["정산금액"]
        if gap != 0:
            add("금액 오류", row, f"정산금액이 판매금액 - 수수료보다 {gap:,}원 적음" if gap > 0 else f"정산금액이 {-gap:,}원 많음", gap)
        rate = r["수수료"] / r["판매금액_정산"] if r["판매금액_정산"] else 0
        if abs(rate - rates[r["쇼핑몰"]]) > RATE_GAP:
            normal = int(r["판매금액_정산"] * rates[r["쇼핑몰"]])
            add("금액 오류", row, f"수수료율 {rate:.1%} (평소 {rates[r['쇼핑몰']]:.1%}). 평소대로면 수수료 약 {normal:,}원",
                r["수수료"] - normal)
        if r["판매금액_정산"] != r["판매금액_주문"]:
            diff = r["판매금액_주문"] - r["판매금액_정산"]
            add("금액 오류", row, f"정산 판매금액이 주문 결제금액보다 {diff:,}원 {'적음' if diff > 0 else '많음'} (쿠폰, 할인 확인)", diff)
        if r["수량_정산"] != r["수량_주문"]:
            add("금액 오류", row, f"수량이 다름 (주문 {r['수량_주문']}개, 정산 {r['수량_정산']}개)")

    return pd.DataFrame(issues, columns=["종류", "쇼핑몰", "상품주문번호", "상품", "내용", "금액"]), rates
