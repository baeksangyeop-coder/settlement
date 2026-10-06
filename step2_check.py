"""
step2_check.py — 번역기가 제대로 일하는지 확인하는 시험 (계산은 아직 안 함)
실행: py step2_check.py
"""
import smartstore, coupang

FILES = {
    "ss_settle": "스마트스토어_정산내역_202609.xlsx", "ss_order": "스마트스토어_주문내역_202609.xlsx",
    "cp_settle": "쿠팡_정산상세_202609.xlsx", "cp_order": "쿠팡_주문내역_202609.xlsx",
}

ss_s = smartstore.read_settlement(FILES["ss_settle"]); ss_o = smartstore.read_orders(FILES["ss_order"])
cp_s = coupang.read_settlement(FILES["cp_settle"]);    cp_o = coupang.read_orders(FILES["cp_order"])

print("== 줄 수 ==")
print(f"스마트스토어 정산 {len(ss_s)}줄, 주문 {len(ss_o)}줄 / 쿠팡 정산 {len(cp_s)}줄, 주문 {len(cp_o)}줄")

print("\n== 공통 표 첫 줄 (두 쇼핑몰이 같은 모양인지) ==")
print(ss_s.head(1).to_string(index=False)); print(cp_s.head(1).to_string(index=False))

print("\n== 시험 1: 상품주문번호의 앞자리 0이 살아 있나 ==")
print("스마트스토어:", ss_s["상품주문번호"].iloc[0], "/ 쿠팡:", cp_s["상품주문번호"].iloc[0])

print("\n== 시험 2: 쿠팡 요약 시트의 합계와 번역 결과의 합계가 같나 ==")
summary = coupang.read_summary_total(FILES["cp_settle"])
print(f"요약 시트 {summary:,}원 / 번역 결과 {cp_s['정산금액'].sum():,}원 →", "같음" if summary == cp_s["정산금액"].sum() else "다름!")

print("\n== 시험 3: 상태와 배송비 구분이 모두 공통 말로 바뀌었나 ==")
for name, t in [("스마트스토어", ss_o), ("쿠팡", cp_o)]:
    print(name, {k: int(v) for k, v in t["상태"].value_counts().items()}, {k: int(v) for k, v in t["배송비구분"].value_counts().items()})
