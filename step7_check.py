"""step7_check.py — 화면 없이 엔진과 보고서만 시험. 실행: py step7_check.py"""
import engine, report
paths = {"ss_settle": "스마트스토어_정산내역_202609.xlsx", "ss_order": "스마트스토어_주문내역_202609.xlsx",
         "cp_settle": "쿠팡_정산상세_202609.xlsx", "cp_order": "쿠팡_주문내역_202609.xlsx", "master": "무숙녀_기준정보.xlsx"}
res = engine.run(paths)
print(res["totals"]); print(*res["warnings"], sep="\n")
report.save_report(res, "정산보고서_시험.xlsx"); print("보고서 저장: 정산보고서_시험.xlsx")
