"""
engine.py — 지금까지 만든 부품을 순서대로 이어서 한 번에 돌림
화면(gui.py)과 확인용 스크립트는 이 파일의 run() 하나만 부름. 계산 로직은 여기에 새로 쓰지 않음.
"""
import pandas as pd
import smartstore, coupang, master, matching, profit, reconcile


def run(paths):
    """paths: {'ss_settle', 'ss_order', 'cp_settle', 'cp_order', 'master'} 파일 경로"""
    m = master.read_master(paths["master"])
    settle = pd.concat([smartstore.read_settlement(paths["ss_settle"]),
                        coupang.read_settlement(paths["cp_settle"])], ignore_index=True)
    orders = pd.concat([smartstore.read_orders(paths["ss_order"]),
                        coupang.read_orders(paths["cp_order"])], ignore_index=True)

    orders = matching.attach_code(orders, m["pairs"])
    unmatched = matching.unmatched(orders, m["pairs"])
    unknown = orders[orders["상태"].str.startswith("알 수 없음") | orders["배송비구분"].str.startswith("알 수 없음")]

    lines, unsold = profit.build_lines(orders, settle, m)
    summary = profit.summarize(lines, unsold)
    issues, rates = reconcile.reconcile(orders.drop(columns=["상품코드"]), settle)

    # 상품명 붙이기 (보기 좋게)
    names = m["cost"].set_index("상품코드")["상품명"]
    summary.insert(2, "상품명", summary["상품코드"].map(names).fillna("(짝 없음)"))

    warnings = []
    for u in unmatched:
        warnings.append(f"상품 짝 없음: [{u['쇼핑몰']}] {u['쇼핑몰상품명']} ({u['줄 수']}줄). 추천 {u['추천'] or '없음'}. "
                        "기준정보의 '상품 짝' 시트에 추가한 뒤 다시 계산해 주세요. (이 줄들은 원가를 몰라 순이익이 실제보다 커요)")
    for a in unsold:
        warnings.append(f"판매 없는 광고비: [{a['쇼핑몰']}] {a['상품코드']} {names.get(a['상품코드'], '')} 광고비 {a['광고비']:,}원을 썼는데 이달 판매가 없어요.")
    if len(unknown):
        warnings.append(f"알 수 없는 주문 상태나 배송비 표기가 {len(unknown)}줄 있어요. 쇼핑몰 양식이 바뀌었는지 확인해 주세요.")

    period = sorted(orders["주문일"])
    return {
        "period": (period[0], period[-1]) if period else ("", ""),
        "summary": summary, "lines": lines, "issues": issues, "rates": rates, "warnings": warnings,
        "totals": {
            "정산금액": int(summary["정산금액"].sum()), "순이익": int(summary["순이익"].sum()),
            "판매수량": int(summary["판매수량"].sum()),
            "받을 돈": int(issues.loc[issues["종류"] == "정산 누락", "금액"].sum()),
            "오류 건수": int((issues["종류"] != "정산 누락").sum()),
            "쇼핑몰별": summary.groupby("쇼핑몰")[["정산금액", "순이익"]].sum().astype(int).to_dict("index"),
        },
    }
