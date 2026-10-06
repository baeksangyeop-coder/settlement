"""
matching.py — 쇼핑몰 상품명을 우리 상품코드로 바꾸고, 원가를 붙임

핵심: 표 두 개를 '이어 붙이기'(merge). 이어 붙인 뒤 줄 수가 그대로인지 꼭 확인함.
짝을 못 찾은 상품은 조용히 버리지 않고 목록으로 돌려줌 (비슷한 이름도 추천).
"""
import difflib


def attach_code(table, pairs):
    """table(공통 표)에 '상품코드' 칸을 붙임. 짝이 없는 줄은 상품코드가 빈칸."""
    before = len(table)
    keyed = pairs.rename(columns={"쇼핑몰 상품명": "쇼핑몰상품명"})
    # validate="many_to_one": 오른쪽(짝 표)에 같은 이름이 두 번 있으면 바로 오류 → 줄이 불어나는 사고 방지
    out = table.merge(keyed, on=["쇼핑몰", "쇼핑몰상품명"], how="left", validate="many_to_one")
    assert len(out) == before, "이어 붙인 뒤 줄 수가 달라졌어요"
    out["상품코드"] = out["상품코드"].fillna("")
    return out


def unmatched(table, pairs):
    """짝을 못 찾은 상품명 목록과, 짝 표에서 가장 비슷한 이름 추천."""
    missing = table[table["상품코드"] == ""].groupby(["쇼핑몰", "쇼핑몰상품명"]).size().reset_index(name="줄 수")
    result = []
    for _, r in missing.iterrows():
        same_mall = pairs[pairs["쇼핑몰"] == r["쇼핑몰"]]
        names = list(same_mall["쇼핑몰 상품명"])
        best = difflib.get_close_matches(r["쇼핑몰상품명"], names, n=1, cutoff=0.6)
        hint = ""
        if best:
            code = same_mall[same_mall["쇼핑몰 상품명"] == best[0]]["상품코드"].iloc[0]
            hint = f"{code} ({best[0]})"
        result.append({"쇼핑몰": r["쇼핑몰"], "쇼핑몰상품명": r["쇼핑몰상품명"], "줄 수": int(r["줄 수"]), "추천": hint})
    return result


def attach_cost(table, cost):
    """상품코드로 원가를 붙임. 원가를 모르는 줄(짝 없음)은 원가가 빈칸(None)."""
    before = len(table)
    out = table.merge(cost[["상품코드", "원가"]], on="상품코드", how="left", validate="many_to_one")
    assert len(out) == before, "이어 붙인 뒤 줄 수가 달라졌어요"
    # 빈칸이 하나라도 섞이면 pandas가 칸 전체를 소수(17000.0)로 바꿔 버림.
    # 'Int64'는 빈칸을 허용하는 정수 형식이라, 원 단위 정수 원칙을 지킬 수 있음
    out["원가"] = out["원가"].astype("Int64")
    return out
