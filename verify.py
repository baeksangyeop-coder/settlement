"""
verify.py — 6단계 공식 검산
프로그램 결과를, 1단계에서 '다른 코드로 따로 계산해 둔 정답 파일'과 원 단위로 맞대 봄.
실행: py verify.py
"""
import pandas as pd
import smartstore, coupang, master, matching, profit, reconcile

ANSWER = "정답_나중에열기.xlsx"

m = master.read_master()
settle = pd.concat([smartstore.read_settlement("스마트스토어_정산내역_202609.xlsx"),
                    coupang.read_settlement("쿠팡_정산상세_202609.xlsx")], ignore_index=True)
orders = matching.attach_code(pd.concat([smartstore.read_orders("스마트스토어_주문내역_202609.xlsx"),
                                         coupang.read_orders("쿠팡_주문내역_202609.xlsx")], ignore_index=True), m["pairs"])
lines, unsold = profit.build_lines(orders, settle, m)
mine = profit.summarize(lines, unsold)
issues, _ = reconcile.reconcile(orders, settle)

# ---- 1) 상품별 순이익: 20줄 x 8칸 ----
answer = pd.read_excel(ANSWER, sheet_name="상품별 순이익", dtype={"상품코드": str})
answer = answer[answer["상품코드"].notna() & (answer["쇼핑몰"] != "전체")]
pairs = {"판매수량": "판매수량", "정산금액": "정산금액", "원가합계": "원가", "포장비": "포장비",
         "배송비": "배송비", "광고비": "광고비", "반품비용": "반품 비용", "순이익": "순이익"}
both = mine.merge(answer, on=["쇼핑몰", "상품코드"], how="outer", suffixes=("", "_정답"), indicator=True)
print("== 1) 상품별 순이익 ==")
print(f"줄: 프로그램 {len(mine)}줄 / 정답 {len(answer)}줄 / 한쪽에만 있는 줄 {(both['_merge'] != 'both').sum()}줄")
total_cells, wrong = 0, []
for ours, theirs in pairs.items():
    a = both[ours]; b = both[theirs + "_정답"] if theirs + "_정답" in both else both[theirs]
    for (_, r), x, y in zip(both.iterrows(), a, b):
        total_cells += 1
        if pd.isna(x) or pd.isna(y) or int(x) != int(y):
            wrong.append(f"{r['쇼핑몰']} {r['상품코드']} {ours}: 프로그램 {x} / 정답 {y}")
print(f"칸: {total_cells}칸 중 {total_cells - len(wrong)}칸 일치")
for w in wrong:
    print("  다름:", w)
print(f"전체 순이익: 프로그램 {mine['순이익'].sum():,}원 / 정답 {int(answer['순이익'].sum()):,}원")

# ---- 2) 심어 둔 문제: 정산 누락, 금액 오류를 찾았나 ----
planted = pd.read_excel(ANSWER, sheet_name="심어 둔 문제", dtype={"상품주문번호": str})
planted = planted[planted["종류"].isin(["정산 누락", "금액 오류"])]
found = set(zip(issues["쇼핑몰"], issues["상품주문번호"]))
want = set(zip(planted["쇼핑몰"], planted["상품주문번호"].str.zfill(9)))
print("\n== 2) 심어 둔 문제 (정산 누락, 금액 오류) ==")
print(f"심어 둔 {len(want)}건 중 찾은 것 {len(want & found)}건, 놓친 것 {len(want - found)}건, 엉뚱하게 찾은 것 {len(found - want)}건")
for x in sorted(want - found): print("  놓침:", x)
for x in sorted(found - want): print("  엉뚱함:", x)
