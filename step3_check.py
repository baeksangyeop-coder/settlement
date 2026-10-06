"""
step3_check.py — 상품 짝 맞추기와 원가 연결이 제대로 되는지 확인
실행: py step3_check.py
"""
import pandas as pd
import smartstore, coupang, master, matching

m = master.read_master()
settle = pd.concat([smartstore.read_settlement("스마트스토어_정산내역_202609.xlsx"),
                    coupang.read_settlement("쿠팡_정산상세_202609.xlsx")], ignore_index=True)
orders = pd.concat([smartstore.read_orders("스마트스토어_주문내역_202609.xlsx"),
                    coupang.read_orders("쿠팡_주문내역_202609.xlsx")], ignore_index=True)
print(f"== 기준 정보 == 상품 {len(m['cost'])}개, 상품 짝 {len(m['pairs'])}줄, 광고비 {len(m['ads'])}줄, 설정 {m['settings']}")

for name, t in [("정산", settle), ("주문", orders)]:
    t2 = matching.attach_code(t, m["pairs"])
    ok = (t2["상품코드"] != "").sum()
    print(f"\n== {name} 표: {len(t2)}줄 중 {ok}줄 짝 찾음 ==")
    for u in matching.unmatched(t2, m["pairs"]):
        print(f"  짝 없음: [{u['쇼핑몰']}] {u['쇼핑몰상품명']} ({u['줄 수']}줄) → 추천: {u['추천'] or '없음'}")

t3 = matching.attach_cost(matching.attach_code(settle, m["pairs"]), m["cost"])
print("\n== 원가를 붙인 정산 표 (처음 3줄) ==")
print(t3[["쇼핑몰", "상품주문번호", "상품코드", "수량", "정산금액", "원가"]].head(3).to_string(index=False))
print("원가가 비어 있는 줄:", int(t3["원가"].isna().sum()))
