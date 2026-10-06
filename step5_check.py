"""
step5_check.py — 주문과 정산 대조 결과 보기
실행: py step5_check.py
"""
import pandas as pd
import smartstore, coupang, reconcile

settle = pd.concat([smartstore.read_settlement("스마트스토어_정산내역_202609.xlsx"),
                    coupang.read_settlement("쿠팡_정산상세_202609.xlsx")], ignore_index=True)
orders = pd.concat([smartstore.read_orders("스마트스토어_주문내역_202609.xlsx"),
                    coupang.read_orders("쿠팡_주문내역_202609.xlsx")], ignore_index=True)

issues, rates = reconcile.reconcile(orders, settle)
print("== 평소 수수료율 (데이터에서 구한 가운뎃값) ==")
for mall, r in rates.items():
    print(f"  {mall}: {r:.2%}")

pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 70)
print(f"\n== 찾은 문제 {len(issues)}건 ==")
print(issues.to_string(index=False))

missing = issues[issues["종류"] == "정산 누락"]
print(f"\n받을 돈(정산 누락) 합계: 약 {missing['금액'].sum():,}원 ({len(missing)}건)")
