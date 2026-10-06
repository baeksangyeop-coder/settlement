"""
master.py — 의뢰인이 관리하는 '기준 정보' 엑셀 읽기
원가, 상품 짝, 광고비, 설정을 읽고, 잘못 적힌 곳이 있으면 계산 전에 멈춰서 알려 줌.
"""
import common

PATH = "무숙녀_기준정보.xlsx"


def read_master(path=PATH):
    cost = common.read_table(path, need=["상품코드", "원가"], sheet="원가")
    pairs = common.read_table(path, need=["쇼핑몰", "쇼핑몰 상품명", "상품코드"], sheet="상품 짝")
    ads = common.read_table(path, need=["쇼핑몰", "상품코드", "광고비"], sheet="광고비")
    settings = common.read_table(path, need=["항목", "값"], sheet="설정")

    cost["원가"] = cost["원가"].map(common.to_won)
    ads["광고비"] = ads["광고비"].map(common.to_won)
    settings = {r["항목"]: common.to_won(r["값"]) for _, r in settings.iterrows()}

    problems = []
    # 같은 상품코드가 원가 시트에 두 번 있으면, 이어 붙일 때 줄이 두 배로 불어남
    for code in cost["상품코드"][cost["상품코드"].duplicated()]:
        problems.append(f"원가 시트에 상품코드 {code}가 두 번 있어요.")
    # 같은 쇼핑몰 상품명이 두 상품코드에 연결돼 있으면 어느 쪽인지 알 수 없음
    dup = pairs[pairs.duplicated(["쇼핑몰", "쇼핑몰 상품명"], keep=False)]
    for _, r in dup.drop_duplicates(["쇼핑몰", "쇼핑몰 상품명"]).iterrows():
        problems.append(f"상품 짝 시트에 '{r['쇼핑몰 상품명']}'({r['쇼핑몰']})이 두 번 있어요.")
    # 상품 짝에 적힌 코드가 원가 시트에 없으면 원가를 붙일 수 없음
    for code in sorted(set(pairs["상품코드"]) - set(cost["상품코드"])):
        problems.append(f"상품 짝 시트의 상품코드 {code}가 원가 시트에 없어요.")
    for key in ["포장비", "판매자 부담 배송비", "반품 비용"]:
        if key not in settings:
            problems.append(f"설정 시트에 '{key}'가 없어요.")
    if problems:
        raise ValueError("기준 정보 엑셀을 먼저 고쳐 주세요:\n- " + "\n- ".join(problems))

    return {"cost": cost[["상품코드", "상품명", "원가"]], "pairs": pairs[["쇼핑몰", "쇼핑몰 상품명", "상품코드"]],
            "ads": ads[["쇼핑몰", "상품코드", "광고비"]], "settings": settings}
