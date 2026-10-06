"""
step4_check.py — 순이익 계산 결과 보기
실행: py step4_check.py
"""
import pandas as pd
import smartstore, coupang, master, matching, profit

m = master.read_master()
settle = pd.concat([smartstore.read_settlement("스마트스토어_정산내역_202609.xlsx"),
                    coupang.read_settlement("쿠팡_정산상세_202609.xlsx")], ignore_index=True)
orders = pd.concat([smartstore.read_orders("스마트스토어_주문내역_202609.xlsx"),
                    coupang.read_orders("쿠팡_주문내역_202609.xlsx")], ignore_index=True)
orders = matching.attach_code(orders, m["pairs"])

lines, unsold = profit.build_lines(orders, settle, m)
table = profit.summarize(lines, unsold)

pd.set_option("display.width", 200)
print("== 쇼핑몰·상품별 순이익 ==")
print(table.to_string(index=False))
print(f"\n전체 순이익: {table['순이익'].sum():,}원")
print(f"판매 없는 광고비: {unsold}")
print(f"정산 누락으로 빼 둔 줄: {int(lines['정산누락'].sum())}줄 (5단계에서 자세히)")

print("\n== 시험: 나눈 돈의 합계가 원래 금액과 같은가 ==")
free = lines[lines["배송비구분"] == "무료배송"]
print("배송비:", f"{free['배송비'].sum():,}원 =", f"{free.groupby(['쇼핑몰','주문번호']).ngroups} 주문 x 3,000원 =",
      f"{free.groupby(['쇼핑몰','주문번호']).ngroups * 3000:,}원")
print("광고비:", f"{lines['광고비'].sum() + sum(a['광고비'] for a in unsold):,}원 =", f"광고비 시트 합계 {int(m['ads']['광고비'].sum()):,}원")
