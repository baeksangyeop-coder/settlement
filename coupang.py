"""
coupang.py — 쿠팡 번역기
쿠팡 정산 엑셀(두 번째 시트 '정산상세')과 주문 엑셀을 '공통 표'로 바꿈.
"""
import common

MALL = "쿠팡"
SETTLEMENT_SHEET = "정산상세"   # 첫 시트는 요약이라 건너뜀

SETTLEMENT_COLUMNS = {
    "주문번호": "주문번호", "주문상품번호": "상품주문번호", "주문일": "주문일", "정산일": "정산일",
    "노출상품명": "쇼핑몰상품명", "옵션명": "옵션", "판매수량": "수량", "판매액": "판매금액",
    "판매수수료": "수수료", "정산금액": "정산금액",
}
ORDER_COLUMNS = {
    "주문번호": "주문번호", "주문상품번호": "상품주문번호", "주문일": "주문일", "노출상품명": "쇼핑몰상품명",
    "옵션명": "옵션", "구매수": "수량", "결제액": "판매금액", "배송비구분": "배송비구분", "상태": "상태",
}
STATUS = {"구매확정": "구매확정", "취소완료": "취소", "반품완료": "반품"}
SHIPPING = {"무료배송": "무료배송", "유료배송": "고객부담"}


def read_settlement(path):
    t = common.read_table(path, need=["주문상품번호", "정산금액"], sheet=SETTLEMENT_SHEET)
    t = common.rename(t, SETTLEMENT_COLUMNS, path)
    for col in ["수량", "판매금액", "수수료", "정산금액"]:
        t[col] = t[col].map(common.to_won)
    t["주문일"] = t["주문일"].map(common.to_date)
    t["정산일"] = t["정산일"].map(common.to_date)
    t["쇼핑몰"] = MALL
    return t[common.SETTLEMENT_COLUMNS]


def read_orders(path):
    t = common.read_table(path, need=["주문상품번호", "상태"])
    t = common.rename(t, ORDER_COLUMNS, path)
    for col in ["수량", "판매금액"]:
        t[col] = t[col].map(common.to_won)
    t["주문일"] = t["주문일"].map(common.to_date)
    t["상태"] = t["상태"].map(lambda s: STATUS.get(s, f"알 수 없음({s})"))
    t["배송비구분"] = t["배송비구분"].map(lambda s: SHIPPING.get(s, f"알 수 없음({s})"))
    t["쇼핑몰"] = MALL
    return t[common.ORDER_COLUMNS]


def read_summary_total(path):
    """쿠팡 요약 시트의 '정산금액 합계'. 번역이 맞는지 맞춰 보는 데 씀."""
    raw = common.pd.read_excel(path, sheet_name="요약", header=None, dtype=str).fillna("")
    for _, row in raw.iterrows():
        if str(row[0]).strip() == "정산금액 합계":
            return common.to_won(row[1])
    return None
