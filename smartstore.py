"""
smartstore.py — 스마트스토어 번역기
스마트스토어에서 내려받은 정산 엑셀, 주문 엑셀을 '공통 표'로 바꿈.
양식이 바뀌면 이 파일 위쪽의 표(COLUMN 들)만 고치면 됨. 계산 코드는 건드리지 않음.
"""
import common

MALL = "스마트스토어"

# 스마트스토어 열 이름 → 공통 이름
SETTLEMENT_COLUMNS = {
    "주문번호": "주문번호", "상품주문번호": "상품주문번호", "결제일": "주문일", "정산완료일": "정산일",
    "상품명": "쇼핑몰상품명", "옵션정보": "옵션", "수량": "수량", "상품결제금액": "판매금액",
    "판매수수료": "판매수수료", "결제수수료": "결제수수료", "정산예정금액": "정산금액",
}
ORDER_COLUMNS = {
    "주문번호": "주문번호", "상품주문번호": "상품주문번호", "주문일시": "주문일", "상품명": "쇼핑몰상품명",
    "옵션정보": "옵션", "수량": "수량", "상품결제금액": "판매금액", "배송비 형태": "배송비구분", "주문상태": "상태",
}
# 같은 뜻을 공통 말로
STATUS = {"구매확정": "구매확정", "취소완료": "취소", "반품완료": "반품"}
SHIPPING = {"무료": "무료배송", "선결제": "고객부담"}


def read_settlement(path):
    t = common.read_table(path, need=["상품주문번호", "정산예정금액"])
    t = common.rename(t, SETTLEMENT_COLUMNS, path)
    for col in ["수량", "판매금액", "판매수수료", "결제수수료", "정산금액"]:
        t[col] = t[col].map(common.to_won)
    # 스마트스토어만 수수료가 두 칸이라, 공통 표의 '수수료' 한 칸으로 합침
    t["수수료"] = t["판매수수료"] + t["결제수수료"]
    t["주문일"] = t["주문일"].map(common.to_date)
    t["정산일"] = t["정산일"].map(common.to_date)
    t["쇼핑몰"] = MALL
    return t[common.SETTLEMENT_COLUMNS]


def read_orders(path):
    t = common.read_table(path, need=["상품주문번호", "주문상태"])
    t = common.rename(t, ORDER_COLUMNS, path)
    for col in ["수량", "판매금액"]:
        t[col] = t[col].map(common.to_won)
    t["주문일"] = t["주문일"].map(common.to_date)
    t["상태"] = t["상태"].map(lambda s: STATUS.get(s, f"알 수 없음({s})"))
    t["배송비구분"] = t["배송비구분"].map(lambda s: SHIPPING.get(s, f"알 수 없음({s})"))
    t["쇼핑몰"] = MALL
    return t[common.ORDER_COLUMNS]
