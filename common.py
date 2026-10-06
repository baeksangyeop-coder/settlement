"""
common.py — 모든 번역기가 같이 쓰는 도구와 '공통 표' 모양

이 파일이 하는 일
- 공통 표의 열 이름을 한곳에 정해 둠 (번역기들은 이 이름으로만 결과를 만듦)
- 엑셀을 '전부 글자로' 읽기 (주문번호 앞의 0이 사라지지 않게)
- 금액과 날짜를 하나의 형식으로 바꾸기
"""
import re
import pandas as pd

# 공통 표의 열 이름. 계산 코드는 이 이름만 알면 됨
SETTLEMENT_COLUMNS = ["쇼핑몰", "주문번호", "상품주문번호", "주문일", "정산일",
                      "쇼핑몰상품명", "옵션", "수량", "판매금액", "수수료", "정산금액"]
ORDER_COLUMNS = ["쇼핑몰", "주문번호", "상품주문번호", "주문일",
                 "쇼핑몰상품명", "옵션", "수량", "판매금액", "배송비구분", "상태"]


def read_table(path, need, sheet=None):
    """엑셀을 읽어서, 'need' 열 이름이 모두 있는 줄을 열 이름 줄로 삼아 표로 돌려줌.

    왜 이렇게 하나: 쇼핑몰 파일은 맨 위에 제목 줄이 있기도 하고 없기도 해서,
    '몇 번째 줄이 열 이름'이라고 정해 두면 양식이 조금만 바뀌어도 깨짐.
    dtype=str: 모든 칸을 글자로 읽음. 숫자로 읽으면 '000410301'이 410301이 됨.
    """
    raw = pd.read_excel(path, sheet_name=sheet or 0, header=None, dtype=str).fillna("")
    for i in range(min(20, len(raw))):
        cells = [str(c).strip() for c in raw.iloc[i]]
        if all(n in cells for n in need):
            table = raw.iloc[i + 1:].copy()
            table.columns = cells
            table = table[table.apply(lambda r: "".join(r).strip() != "", axis=1)]   # 빈 줄 빼기
            return table.reset_index(drop=True)
    raise ValueError(f"{path}: 열 이름 {need} 이(가) 모두 있는 줄을 찾지 못했어요.")


def to_won(value):
    """'44,000', '44000', '44000.0', '' 를 원 단위 정수로. 빈칸은 0.

    왜 float()를 거치지 않나: 소수 계산 오차를 아예 들이지 않으려고.
    '44000.0'처럼 엑셀이 붙인 .0만 떼어 내고 정수로 바꿈.
    """
    text = str(value).strip().replace(",", "").replace("원", "")
    if text == "":
        return 0
    if not re.fullmatch(r"-?\d+(\.0+)?", text):
        raise ValueError(f"금액으로 읽을 수 없는 값: {value!r}")
    return int(text.split(".")[0])


def to_date(value):
    """'2026.09.09', '20260910', '2026/09/02', '2026-09-01 18:09' 를 '2026-09-09' 형식으로."""
    text = str(value).strip()
    m = re.match(r"(\d{4})[.\-/]?(\d{1,2})[.\-/]?(\d{1,2})", text)
    if not m:
        raise ValueError(f"날짜로 읽을 수 없는 값: {value!r}")
    y, mo, d = m.groups()
    return f"{y}-{int(mo):02d}-{int(d):02d}"


def rename(table, column_map, path):
    """쇼핑몰 열 이름을 공통 이름으로 바꿈. 필요한 열이 없으면 무엇이 없는지 알려 주고 멈춤."""
    missing = [k for k in column_map if k not in table.columns]
    if missing:
        raise ValueError(f"{path}: 이 열이 없어요 {missing}. 쇼핑몰 양식이 바뀌었는지 확인해 주세요.")
    return table[list(column_map)].rename(columns=column_map)
