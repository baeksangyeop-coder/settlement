"""
gui.py — 의뢰인이 쓰는 화면 (tkinter)
화면은 '파일 고르기 → engine.run() 부르기 → 결과 보여 주기'만 함. 계산은 engine과 부품들이 함.
실행: py gui.py   /   exe 만들기: README의 방법 참고
"""
import os, sys, datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import engine, report

FONT = ("맑은 고딕", 10)
FILES = [  # (키, 화면 이름, 파일 이름에 들어 있어야 하는 말)
    ("ss_settle", "스마트스토어 정산", ("스마트스토어", "정산")),
    ("ss_order", "스마트스토어 주문", ("스마트스토어", "주문")),
    ("cp_settle", "쿠팡 정산", ("쿠팡", "정산")),
    ("cp_order", "쿠팡 주문", ("쿠팡", "주문")),
    ("master", "기준 정보", ("기준정보",)),
]


def guess_files(folder):
    """폴더 안의 엑셀 파일 이름을 보고 다섯 칸을 자동으로 채움 (못 찾은 칸은 빈칸)."""
    names = [f for f in os.listdir(folder) if f.lower().endswith((".xlsx", ".xls")) and not f.startswith("~$")]
    found = {}
    for key, _, words in FILES:
        hits = [f for f in names if all(w in f.replace(" ", "") for w in words)]
        if hits:
            # normpath: 폴더 고르기 창은 '/'로, 윈도우는 '\'로 경로를 써서 섞여 보이는 걸 하나로 맞춤
            found[key] = os.path.normpath(os.path.join(folder, sorted(hits)[-1]))   # 여러 개면 이름순 마지막(보통 최신 월)
    return found


def won(n):
    return f"{n:,}원"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("무숙녀 정산 도우미 (스마트스토어·쿠팡)")
        self.geometry("1080x720")
        self.option_add("*Font", FONT)
        self.result = None
        self.vars = {key: tk.StringVar() for key, _, _ in FILES}

        # ---- 파일 고르기 ----
        top = ttk.LabelFrame(self, text="1. 파일 고르기", padding=10)
        top.pack(fill="x", padx=12, pady=(12, 6))
        ttk.Button(top, text="폴더 고르기 (파일 이름으로 자동 채움)", command=self.pick_folder).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        for i, (key, label, _) in enumerate(FILES, 1):
            ttk.Label(top, text=label, width=16).grid(row=i, column=0, sticky="w")
            ttk.Entry(top, textvariable=self.vars[key], width=90).grid(row=i, column=1, sticky="we", padx=6, pady=2)
            ttk.Button(top, text="찾기", command=lambda k=key: self.pick_file(k)).grid(row=i, column=2)
        top.columnconfigure(1, weight=1)

        # ---- 실행 ----
        mid = ttk.Frame(self, padding=(12, 0)); mid.pack(fill="x")
        ttk.Button(mid, text="2. 계산하기", command=self.calculate).pack(side="left")
        self.save_btn = ttk.Button(mid, text="3. 보고서 엑셀로 저장", command=self.save, state="disabled")
        self.save_btn.pack(side="left", padx=8)
        self.status = ttk.Label(mid, text="파일 다섯 개를 고르고 계산하기를 눌러 주세요.", foreground="#566170")
        self.status.pack(side="left", padx=8)

        # ---- 결과 탭 ----
        self.tabs = ttk.Notebook(self); self.tabs.pack(fill="both", expand=True, padx=12, pady=12)
        self.tab_summary = ttk.Frame(self.tabs, padding=10); self.tabs.add(self.tab_summary, text="요약")
        self.tree_profit = self._tree("상품별 순이익", ["쇼핑몰", "상품명", "판매수량", "정산금액", "원가합계", "포장비", "배송비", "광고비", "반품비용", "순이익"])
        self.tree_issue = self._tree("받을 돈과 오류", ["종류", "쇼핑몰", "상품주문번호", "상품", "내용", "금액"])
        self.warn_text = tk.Text(self.tabs, wrap="word", height=10, padx=10, pady=10)
        self.tabs.add(self.warn_text, text="확인할 것")

        # 시작할 때 파일 칸 자동 채우기: exe면 exe가 있는 폴더, py gui.py로 실행하면 지금 폴더
        start = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd()
        found = guess_files(start)
        if found:
            self.fill(found)
            self.status.config(text=f"이 폴더에서 파일 {len(found)}개를 찾아 채웠어요. 맞는지 보고 계산하기를 눌러 주세요.")

        # 계산 전 요약 탭 안내
        ttk.Label(self.tab_summary, text="계산하기를 누르면 여기에 정산금액, 순이익, 받을 돈과 상품별 그래프가 나와요.",
                  foreground="#566170").pack(anchor="w")

    def _tree(self, title, columns):
        frame = ttk.Frame(self.tabs); self.tabs.add(frame, text=title)
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for c in columns:
            tree.heading(c, text=c)
            tree.column(c, width=320 if c in ("내용",) else 200 if c in ("상품명", "상품") else 90,
                        anchor="e" if c in ("판매수량", "정산금액", "원가합계", "포장비", "배송비", "광고비", "반품비용", "순이익", "금액") else "w")
        bar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=bar.set)
        tree.pack(side="left", fill="both", expand=True); bar.pack(side="right", fill="y")
        tree.tag_configure("minus", foreground="#B42335")
        return tree

    # ---------- 파일 ----------
    def fill(self, found):
        for key, path in found.items():
            self.vars[key].set(path)

    def pick_folder(self):
        folder = filedialog.askdirectory(title="엑셀 파일들이 있는 폴더")
        if folder:
            found = guess_files(folder); self.fill(found)
            self.status.config(text=f"파일 {len(found)}개를 찾았어요." + ("" if len(found) == 5 else " 비어 있는 칸은 '찾기'로 골라 주세요."))

    def pick_file(self, key):
        path = filedialog.askopenfilename(filetypes=[("엑셀", "*.xlsx *.xls")])
        if path:
            self.vars[key].set(os.path.normpath(path))

    # ---------- 계산 ----------
    def calculate(self):
        paths = {k: v.get().strip() for k, v in self.vars.items()}
        empty = [label for key, label, _ in FILES if not paths[key]]
        if empty:
            messagebox.showwarning("파일을 골라 주세요", "비어 있는 칸: " + ", ".join(empty)); return
        self.status.config(text="계산 중…"); self.update_idletasks()
        try:
            self.result = engine.run(paths)
        except PermissionError:
            messagebox.showerror("파일을 열 수 없어요", "고른 엑셀 파일이 다른 프로그램에서 열려 있는지 확인해 주세요."); return
        except Exception as e:   # 부품들이 알려 주는 오류 문구를 그대로 보여 줌
            messagebox.showerror("계산하지 못했어요", str(e)); self.status.config(text="오류가 있어요."); return
        self.show(); self.save_btn.config(state="normal")
        warn = len(self.result["warnings"])
        self.status.config(text="계산을 마쳤어요." + (f" 확인할 것 {warn}건이 있어요." if warn else ""))

    def show(self):
        r, t = self.result, self.result["totals"]
        for w in self.tab_summary.winfo_children(): w.destroy()
        ttk.Label(self.tab_summary, text=f"주문 기간 {r['period'][0]} ~ {r['period'][1]}", foreground="#566170").pack(anchor="w")
        kpis = ttk.Frame(self.tab_summary); kpis.pack(anchor="w", pady=8)
        rate = t["순이익"] / t["정산금액"] if t["정산금액"] else 0
        for i, (k, v) in enumerate([("정산금액", won(t["정산금액"])), ("순이익", won(t["순이익"])), ("순이익률", f"{rate:.1%}"),
                                    ("받을 돈", won(t["받을 돈"])), ("금액 오류", f"{t['오류 건수']}건")]):
            box = ttk.Frame(kpis, padding=(0, 0, 28, 0)); box.grid(row=0, column=i)
            ttk.Label(box, text=k, foreground="#566170").pack(anchor="w")
            ttk.Label(box, text=v, font=("맑은 고딕", 15, "bold"), foreground="#B42335" if k in ("받을 돈", "금액 오류") and v not in ("0원", "0건") else "#1C2330").pack(anchor="w")
        self.draw_chart()

        for tree in (self.tree_profit, self.tree_issue): tree.delete(*tree.get_children())
        for row in r["summary"].itertuples(index=False):
            vals = [row.쇼핑몰, row.상품명, row.판매수량] + [f"{x:,}" for x in (row.정산금액, row.원가합계, row.포장비, row.배송비, row.광고비, row.반품비용, row.순이익)]
            self.tree_profit.insert("", "end", values=vals, tags=("minus",) if row.순이익 < 0 else ())
        for row in r["issues"].itertuples(index=False):
            self.tree_issue.insert("", "end", values=[row.종류, row.쇼핑몰, row.상품주문번호, row.상품, row.내용, f"{row.금액:,}"])
        self.warn_text.delete("1.0", "end")
        self.warn_text.insert("1.0", "\n\n".join(f"• {w}" for w in r["warnings"]) or "확인할 것이 없어요.")

    def draw_chart(self):
        """상품별 순이익 (두 쇼핑몰 합) 가로 막대. 그림 도구 없이 tkinter 캔버스로 직접 그림 (exe가 가벼워지게)"""
        data = self.result["summary"].groupby("상품명")["순이익"].sum().sort_values(ascending=False)   # 큰 상품이 위로
        ttk.Label(self.tab_summary, text="상품별 순이익 (두 쇼핑몰 합)", font=("맑은 고딕", 11, "bold")).pack(anchor="w", pady=(8, 4))
        c = tk.Canvas(self.tab_summary, height=28 * len(data) + 20, bg="white", highlightthickness=0)
        c.pack(fill="x")
        self.update_idletasks()
        width = max(c.winfo_width(), 700)
        left, right = 220, 140                      # 왼쪽은 상품명, 오른쪽은 금액 글자 자리
        pos, neg = max(data.max(), 0), max(-data.min(), 0)
        scale = (width - left - right) / ((pos + neg) or 1)   # 1원이 몇 픽셀인지
        zero = left + neg * scale                    # 0원 위치 (손해 상품이 있으면 오른쪽으로 밀림)
        for i, (name, v) in enumerate(data.items()):
            y = 10 + i * 28
            x2 = zero + v * scale
            c.create_text(left - 10, y + 10, text=name, anchor="e", font=FONT)
            c.create_rectangle(min(zero, x2), y + 2, max(zero, x2), y + 18, fill="#B42335" if v < 0 else "#2C5AA0", width=0)
            c.create_text(max(zero, x2) + 6, y + 10, text=won(int(v)), anchor="w", font=FONT)

    # ---------- 저장 ----------
    def save(self):
        month = self.result["period"][0][:7]
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"무숙녀_정산보고서_{month}.xlsx",
                                            filetypes=[("엑셀", "*.xlsx")])
        if not path: return
        try:
            report.save_report(self.result, path)
        except PermissionError:
            messagebox.showerror("저장하지 못했어요", "같은 이름의 보고서가 엑셀에서 열려 있어요. 닫고 다시 저장해 주세요."); return
        self.status.config(text=f"보고서를 저장했어요: {os.path.basename(path)}")
        if messagebox.askyesno("저장했어요", "보고서를 지금 열어 볼까요?"):
            os.startfile(path)


if __name__ == "__main__":
    App().mainloop()
