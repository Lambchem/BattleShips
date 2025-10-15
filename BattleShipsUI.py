import os
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# 右键循环值：包含 6（S 独舰），并以 -1 结束回到未知
CYCLE_ORDER = [0, 2, 3, 4, 5, 6, -1]

# 单元格显示
VALUE_TEXT = {
    -1: "",
     1: "·",  # 海水
     0: "■",  # 舰体
     2: "U",
     3: "D",
     4: "L",
     5: "R",
     6: "S",
}
VALUE_BG = {
    -1: "#e8e8e8",  # 未知
     1: "#a6c8ff",  # 海水
     0: "#2e2e2e",  # 舰体
     2: "#3d8b37",  # U
     3: "#3d8b37",  # D
     4: "#3d8b37",  # L
     5: "#3d8b37",  # R
     6: "#ffb000",  # S
}
VALUE_FG = {
    -1: "#333333",
     1: "#113355",
     0: "#ffffff",
     2: "#ffffff",
     3: "#ffffff",
     4: "#ffffff",
     5: "#ffffff",
     6: "#000000",
}

# 键盘快捷键：把按键映射为内部值（S→6）
KEY_TO_VALUE = {
    "w": 1, "W": 1,     # 水
    "u": -1, "U": -1,   # 未知
    "0": 0, "2": 2, "3": 3, "4": 4, "5": 5,
    "s": 6, "S": 6,     # 独舰
}

def default_solver_name():
    if os.name == "nt":
        return "battleship_solver.exe"
    return "./battleship_solver"


class ScrollableArea(ttk.Frame):
    """
    带水平/垂直滚动条且自动居中的区域。
    - 内容小于可视区域：水平/垂直居中显示；
    - 内容更大：显示滚动条，可滚动查看。
    """
    def __init__(self, master, width=900, height=420, bg="#ffffff"):
        super().__init__(master)
        self.canvas = tk.Canvas(self, bg=bg, width=width, height=height, highlightthickness=0)
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.hbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.hbar.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 内部容器（把你的控件放在 self.frame 里）
        self.frame = ttk.Frame(self.canvas)
        self._win_id = self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        # 当内容或视口变化时，更新滚动范围与居中位置
        self.frame.bind("<Configure>", self._update_layout)
        self.canvas.bind("<Configure>", self._update_layout)

        # 鼠标滚轮支持：进入时绑定，离开时解绑
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _update_layout(self, _event=None):
        self.canvas.update_idletasks()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        fw = self.frame.winfo_reqwidth()
        fh = self.frame.winfo_reqheight()

        # 居中：当内容小于画布时，计算偏移；否则置 0
        x = max(0, (cw - fw) // 2)
        y = max(0, (ch - fh) // 2)
        self.canvas.coords(self._win_id, x, y)

        # 滚动区域：至少等于内容大小；当内容小于画布时，用画布大小避免滚动条出现
        sr_w = max(fw, cw)
        sr_h = max(fh, ch)
        self.canvas.configure(scrollregion=(0, 0, sr_w, sr_h))

    def recenter(self):
        self._update_layout()

    def _on_mousewheel(self, event):
        # Windows/Mac：<MouseWheel>; Linux：Button-4/5
        if getattr(event, "num", None) == 4:      # Linux 上滚
            self.canvas.yview_scroll(-2, "units")
        elif getattr(event, "num", None) == 5:    # Linux 下滚
            self.canvas.yview_scroll(2, "units")
        else:
            delta = -1 if event.delta > 0 else 1
            if event.state & 0x0001:  # Shift 键：横向滚动
                self.canvas.xview_scroll(delta, "units")
            else:
                self.canvas.yview_scroll(delta, "units")

    def _bind_mousewheel(self, _event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        # Linux
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event=None):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")


class PuzzleModel:
    def __init__(self, n=10, K=4):
        self.n = n
        self.K = K
        self.board = [[-1 for _ in range(n)] for __ in range(n)]  # -1/0/1/2/3/4/5/6
        self.row_targets = [0 for _ in range(n)]
        self.col_targets = [0 for _ in range(n)]

    def resize(self, n_new):
        old_n = self.n
        old_board = self.board
        old_row_t = self.row_targets
        old_col_t = self.col_targets

        self.n = n_new
        self.board = [[-1 for _ in range(n_new)] for __ in range(n_new)]
        self.row_targets = [0 for _ in range(n_new)]
        self.col_targets = [0 for _ in range(n_new)]

        lim = min(old_n, n_new)
        for r in range(lim):
            for c in range(lim):
                self.board[r][c] = old_board[r][c]
        for r in range(min(lim, len(old_row_t))):
            self.row_targets[r] = old_row_t[r]
        for c in range(min(lim, len(old_col_t))):
            self.col_targets[c] = old_col_t[c]

    def toggle_left(self, r, c):
        # 左键：未知 <-> 海水
        if self.board[r][c] == -1:
            self.board[r][c] = 1
        elif self.board[r][c] == 1:
            self.board[r][c] = -1

    def cycle_right(self, r, c):
        cur = self.board[r][c]
        # 水(1)不在循环内，从循环首开始
        if cur == 1:
            nxt = CYCLE_ORDER[0]
        else:
            try:
                idx = CYCLE_ORDER.index(cur)
                nxt = CYCLE_ORDER[(idx + 1) % len(CYCLE_ORDER)]
            except ValueError:
                nxt = CYCLE_ORDER[0]
        self.board[r][c] = nxt

    def build_engine_matrix_lines(self):
        """
        生成引擎输入文本行（K在第一行，随后 (n+1)x(n+1) 矩阵）
        内部格子允许值为：-1,0,1,2,3,4,5,6
        """
        lines = []
        lines.append(str(int(self.K)))
        # 第一行：-1, col_targets...
        top = [-1] + [int(max(0, t)) for t in self.col_targets]
        lines.append(" ".join(map(str, top)))
        # 接下来 n 行：每行 row_target + n 个格子
        for r in range(self.n):
            row = [int(max(0, self.row_targets[r]))]
            for c in range(self.n):
                v = int(self.board[r][c])
                if v not in (-1, 0, 1, 2, 3, 4, 5, 6):
                    v = -1
                row.append(v)
            lines.append(" ".join(map(str, row)))
        return lines

    @staticmethod
    def parse_solutions_from_output(text, n):
        text = text.strip()
        if "No solution" in text:
            return []
        lines = [ln.strip() for ln in text.splitlines() if ln.strip() != ""]
        sols = []
        i = 0
        if i < len(lines) and lines[i].startswith("Solutions:"):
            i += 1
        while i + n <= len(lines):
            grid = []
            ok = True
            for r in range(n):
                parts = lines[i + r].replace(",", " ").replace(";", " ").split()
                if len(parts) != n:
                    ok = False
                    break
                try:
                    row = [int(x) for x in parts]
                except:
                    ok = False
                    break
                grid.append(row)
            if ok:
                sols.append(grid)
            i += n
        return sols


class BattleshipUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("战舰解谜 UI（适配 C++ 引擎）")
        self.model = PuzzleModel(n=10, K=4)
        self.solver_path = tk.StringVar(value=default_solver_name())

        self._cell_labels = []   # 编辑盘格子 Label
        self._row_entries = []   # 行目标 Entry
        self._col_entries = []   # 列目标 Entry

        self._sol_labels = []    # 解盘格子 Label
        self._solutions = []
        self._sol_index = 0
        self._sol_status = tk.StringVar(value="尚未求解")

        # 调试视图
        self._last_input = ""
        self._last_stdout = ""
        self._last_stderr = ""

        # 求解过程控制
        self._proc = None               # subprocess.Popen 对象
        self._solver_thread = None      # 运行引擎的线程
        self._stopping = False          # 是否正在停止

        self._build_widgets()
        self._rebuild_grids()

        # 关闭窗口时，确保终止引擎
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_widgets(self):
        # 顶部控制区
        ctrl = ttk.Frame(self)
        ctrl.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)

        ttk.Label(ctrl, text="最大舰长 K:").pack(side=tk.LEFT)
        self.entry_K = ttk.Spinbox(ctrl, from_=1, to=50, width=5)
        self.entry_K.set(str(self.model.K))
        self.entry_K.pack(side=tk.LEFT, padx=(4, 12))
        # K 键入也更新
        self.entry_K.bind("<KeyRelease>", lambda e: self._sync_from_entries())

        ttk.Label(ctrl, text="网格大小 n:").pack(side=tk.LEFT)
        self.entry_n = ttk.Spinbox(ctrl, from_=2, to=80, width=5, command=self._on_n_change)
        self.entry_n.set(str(self.model.n))
        self.entry_n.pack(side=tk.LEFT, padx=(4, 12))
        # 键盘输入即时更新地图大小（有效整数时）
        self.entry_n.bind("<KeyRelease>", self._on_n_change_event)
        self.entry_n.bind("<FocusOut>", self._on_n_change_event)
        self.entry_n.bind("<Return>", self._on_n_change_event)

        ttk.Button(ctrl, text="清空棋盘", command=self._clear_board).pack(side=tk.LEFT, padx=4)
        ttk.Button(ctrl, text="未知全设为海水", command=self._fill_unknown_as_water).pack(side=tk.LEFT, padx=4)
        ttk.Button(ctrl, text="按当前盘面统计行/列目标", command=self._recalc_targets_from_board).pack(side=tk.LEFT, padx=4)

        # 求解 & 引擎
        engine = ttk.Frame(self)
        engine.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(0, 8))
        ttk.Label(engine, text="引擎路径:").pack(side=tk.LEFT)
        ttk.Entry(engine, textvariable=self.solver_path, width=42).pack(side=tk.LEFT, padx=4)
        ttk.Button(engine, text="浏览", command=self._browse_solver).pack(side=tk.LEFT, padx=4)
        ttk.Button(engine, text="编译引擎(BattleShips.cpp)", command=self._compile_engine).pack(side=tk.LEFT, padx=8)
        self.btn_solve = ttk.Button(engine, text="求解", command=self._solve)
        self.btn_solve.pack(side=tk.LEFT, padx=4)
        self.btn_stop = ttk.Button(engine, text="停止分析", command=self._stop_solver, state="disabled")
        self.btn_stop.pack(side=tk.LEFT, padx=4)
        ttk.Button(engine, text="导入引擎文本", command=self._open_import_dialog).pack(side=tk.LEFT, padx=4)
        ttk.Button(engine, text="查看引擎输入", command=self._show_last_input).pack(side=tk.LEFT, padx=4)
        ttk.Button(engine, text="查看引擎输出", command=self._show_last_output).pack(side=tk.LEFT, padx=4)

        # 编辑棋盘（带居中与滚动区域）
        self.board_group = ttk.LabelFrame(self, text="编辑棋盘（左键：未知↔海水，右键：0→2→3→4→5→6→-1，键盘：W=水，U=未知，S=独舰）")
        self.board_group.pack(side=tk.TOP, padx=8, pady=8, fill=tk.BOTH, expand=True)
        self.board_sa = ScrollableArea(self.board_group, width=900, height=420, bg="#ffffff")
        self.board_sa.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        # 实际表格容器放在可滚动区域的 frame 中
        self.board_frame = ttk.Frame(self.board_sa.frame)
        self.board_frame.pack()  # 由 ScrollableArea 居中

        # 解显示（带居中与滚动区域）
        sol_ctrl = ttk.Frame(self)
        sol_ctrl.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(0, 4))
        ttk.Button(sol_ctrl, text="上一解", command=self._prev_solution).pack(side=tk.LEFT, padx=4)
        ttk.Button(sol_ctrl, text="下一解", command=self._next_solution).pack(side=tk.LEFT, padx=4)
        ttk.Label(sol_ctrl, textvariable=self._sol_status).pack(side=tk.LEFT, padx=10)

        self.solution_group = ttk.LabelFrame(self, text="求解结果（0=战舰，1=海水）")
        self.solution_group.pack(side=tk.TOP, padx=8, pady=(0, 8), fill=tk.BOTH, expand=True)
        self.solution_sa = ScrollableArea(self.solution_group, width=900, height=300, bg="#ffffff")
        self.solution_sa.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.solution_frame = ttk.Frame(self.solution_sa.frame)
        self.solution_frame.pack()  # 由 ScrollableArea 居中

    def _set_running_state(self, running: bool):
        if running:
            self.btn_solve.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self._sol_status.set("求解中（无超时限制）...")
        else:
            self.btn_solve.configure(state="normal")
            self.btn_stop.configure(state="disabled")

    def _on_n_change_event(self, _ev=None):
        # 键盘实时变化：当输入为合法整数时立刻重建网格
        try:
            n_new = int(self.entry_n.get())
        except:
            return
        if n_new != self.model.n:
            self._on_n_change()

    def _on_n_change(self):
        try:
            n_new = int(self.entry_n.get())
        except:
            return
        n_new = max(2, min(80, n_new))
        if n_new != self.model.n:
            self.model.resize(n_new)
            self._rebuild_grids()

    def _clear_board(self):
        for r in range(self.model.n):
            for c in range(self.model.n):
                self.model.board[r][c] = -1
        self._refresh_board()

    def _fill_unknown_as_water(self):
        for r in range(self.model.n):
            for c in range(self.model.n):
                if self.model.board[r][c] == -1:
                    self.model.board[r][c] = 1
        self._refresh_board()

    def _recalc_targets_from_board(self):
        # 把当前棋盘上“被认为是舰体的格子”（0/2/3/4/5/6）计入行/列目标
        n = self.model.n
        row = [0]*n
        col = [0]*n
        for r in range(n):
            for c in range(n):
                v = self.model.board[r][c]
                if v in (0, 2, 3, 4, 5, 6):
                    row[r] += 1
                    col[c] += 1
        self.model.row_targets = row
        self.model.col_targets = col
        self._refresh_targets()

    def _browse_solver(self):
        path = filedialog.askopenfilename(title="选择引擎可执行文件")
        if path:
            self.solver_path.set(path)

    def _compile_engine(self):
        cpp_path = filedialog.askopenfilename(title="选择 BattleShips.cpp 源文件", filetypes=[("C++ Source", "*.cpp"), ("All files", "*.*")])
        if not cpp_path:
            return
        out_exe = default_solver_name()
        cmd = ["g++", "-std=c++17", "-O2", "-o", out_exe, cpp_path]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                messagebox.showerror("编译失败", f"命令: {' '.join(cmd)}\n\nstderr:\n{proc.stderr}")
                return
            self.solver_path.set(os.path.abspath(out_exe))
            messagebox.showinfo("编译成功", f"已生成: {self.solver_path.get()}")
        except Exception as e:
            messagebox.showerror("编译异常", str(e))

    def _rebuild_grids(self):
        # 清空编辑棋盘与解显示
        for w in self.board_frame.winfo_children():
            w.destroy()
        for w in self.solution_frame.winfo_children():
            w.destroy()
        self._cell_labels.clear()
        self._row_entries.clear()
        self._col_entries.clear()
        self._sol_labels.clear()

        n = self.model.n

        # 编辑棋盘：左上角隐藏（原本是显示 -1 的位置，这里留空）
        corner = ttk.Label(self.board_frame, text="", width=4, anchor="center")
        corner.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")

        # 顶部列目标
        for c in range(n):
            e = ttk.Entry(self.board_frame, width=4, justify="center")
            e.insert(0, str(self.model.col_targets[c]))
            e.grid(row=0, column=c+1, padx=1, pady=1, sticky="nsew")
            self._col_entries.append(e)

        # 行目标 + 单元格
        for r in range(n):
            e = ttk.Entry(self.board_frame, width=4, justify="center")
            e.insert(0, str(self.model.row_targets[r]))
            e.grid(row=r+1, column=0, padx=1, pady=1, sticky="nsew")
            self._row_entries.append(e)

            row_labels = []
            for c in range(n):
                lbl = tk.Label(self.board_frame, width=4, height=2, bd=1, relief="solid")
                self._style_cell(lbl, self.model.board[r][c])
                lbl.grid(row=r+1, column=c+1, padx=1, pady=1, sticky="nsew")
                # 鼠标
                lbl.bind("<Button-1>", lambda ev, rr=r, cc=c: (self._on_left_click(rr, cc), ev.widget.focus_set()))
                lbl.bind("<Button-3>", lambda ev, rr=r, cc=c: self._on_right_click(rr, cc))
                lbl.bind("<Button-2>", lambda ev, rr=r, cc=c: self._on_right_click(rr, cc))  # mac 某些触控板
                # 键盘（S 直接设置独舰）
                lbl.bind("<Key>", lambda ev, rr=r, cc=c: self._on_key(rr, cc, ev))
                row_labels.append(lbl)
            self._cell_labels.append(row_labels)

        # 解显示区域
        for r in range(n):
            row_labels = []
            for c in range(n):
                lbl = tk.Label(self.solution_frame, width=4, height=2, bd=1, relief="ridge", bg="#f5f5f5")
                lbl.grid(row=r, column=c, padx=1, pady=1, sticky="nsew")
                row_labels.append(lbl)
            self._sol_labels.append(row_labels)

        # 刷新并居中滚动区域
        self.board_sa.recenter()
        self.solution_sa.recenter()

        self._update_solution_view()

    def _style_cell(self, lbl, v):
        lbl.config(text=VALUE_TEXT.get(v, "?"),
                   bg=VALUE_BG.get(v, "#cccccc"),
                   fg=VALUE_FG.get(v, "#000000"),
                   font=("Segoe UI", 10, "bold"))

    def _on_left_click(self, r, c):
        self._sync_from_entries()
        self.model.toggle_left(r, c)
        self._style_cell(self._cell_labels[r][c], self.model.board[r][c])

    def _on_right_click(self, r, c):
        self._sync_from_entries()
        self.model.cycle_right(r, c)
        self._style_cell(self._cell_labels[r][c], self.model.board[r][c])

    def _on_key(self, r, c, ev):
        ch = ev.char
        if not ch:
            return
        if ch in KEY_TO_VALUE:
            self._sync_from_entries()
            self.model.board[r][c] = KEY_TO_VALUE[ch]
            self._style_cell(self._cell_labels[r][c], self.model.board[r][c])

    def _refresh_board(self):
        for r in range(self.model.n):
            for c in range(self.model.n):
                self._style_cell(self._cell_labels[r][c], self.model.board[r][c])
        self.board_sa.recenter()

    def _refresh_targets(self):
        for i, e in enumerate(self._row_entries):
            e.delete(0, tk.END)
            e.insert(0, str(self.model.row_targets[i]))
        for i, e in enumerate(self._col_entries):
            e.delete(0, tk.END)
            e.insert(0, str(self.model.col_targets[i]))
        self.board_sa.recenter()

    def _sync_from_entries(self):
        # 同步 K
        try:
            K = int(self.entry_K.get())
            K = max(1, min(100, K))
            self.model.K = K
        except:
            pass
        # 同步目标值
        row = []
        for e in self._row_entries:
            try:
                row.append(max(0, int(e.get())))
            except:
                row.append(0)
        col = []
        for e in self._col_entries:
            try:
                col.append(max(0, int(e.get())))
            except:
                col.append(0)
        if len(row) == self.model.n:
            self.model.row_targets = row
        if len(col) == self.model.n:
            self.model.col_targets = col

    def _solve(self):
        if self._proc is not None:
            messagebox.showinfo("提示", "引擎正在运行，可点击“停止分析”后再开始。")
            return

        self._sync_from_entries()
        lines = self.model.build_engine_matrix_lines()
        input_text = "\n".join(lines) + "\n"
        self._last_input = input_text  # 记录这次喂给引擎的原始输入

        solver = self.solver_path.get().strip()
        if not solver:
            messagebox.showwarning("提示", "请先设置引擎可执行文件路径。")
            return
        if not os.path.exists(solver):
            messagebox.showwarning("提示", f"未找到引擎可执行文件：{solver}")
            return

        self._solutions = []
        self._sol_index = 0
        self._update_solution_view()
        self._set_running_state(True)
        self._stopping = False

        def run_solver():
            try:
                # 用 Popen 以便可中断
                self._proc = subprocess.Popen(
                    [solver],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = self._proc.communicate(input=input_text)
                rc = self._proc.returncode
                # 清理句柄
                self._last_stdout = stdout or ""
                self._last_stderr = stderr or ""
            except Exception as e:
                self._last_stdout = ""
                self._last_stderr = str(e)
                rc = -999
            finally:
                # 线程安全地清理状态
                def finish():
                    self._proc = None
                    self._solver_thread = None
                    if rc == 0 and not self._stopping:
                        sols = PuzzleModel.parse_solutions_from_output(self._last_stdout, self.model.n)
                        self._on_solver_done(sols, None)
                    else:
                        if self._stopping:
                            # 用户主动停止
                            self._on_solver_done([], "已停止")
                        else:
                            msg = (self._last_stderr.strip() or "引擎返回非零退出码")
                            self._on_solver_done([], f"引擎错误: {msg}")
                    self._set_running_state(False)
                    self._stopping = False
                self.after(0, finish)

        self._solver_thread = threading.Thread(target=run_solver, daemon=True)
        self._solver_thread.start()

    def _stop_solver(self):
        if self._proc is None:
            return
        self._stopping = True
        try:
            self._proc.terminate()
        except Exception:
            pass

    def _on_close(self):
        # 窗口关闭：若引擎仍在运行，立刻终止
        if self._proc is not None:
            try:
                self._proc.terminate()
            except Exception:
                pass
        # 不等待线程自然结束，直接销毁窗口（子进程已被终止）
        try:
            self.destroy()
        except Exception:
            pass

    def _on_solver_done(self, solutions, err_msg):
        if err_msg and err_msg != "已停止":
            self._sol_status.set(err_msg)
            messagebox.showerror("求解失败", err_msg)
            self._solutions = []
        else:
            self._solutions = solutions
            if err_msg == "已停止":
                self._sol_status.set("已停止")
            elif not solutions:
                self._sol_status.set("无解")
            else:
                self._sol_status.set(f"共 {len(solutions)} 个解，当前显示第 1 个")
        self._sol_index = 0
        self._update_solution_view()

    def _update_solution_view(self):
        n = self.model.n
        # 清屏
        for r in range(n):
            for c in range(n):
                lbl = self._sol_labels[r][c]
                lbl.config(text="", bg="#f5f5f5", fg="#000000")
        # 显示当前解
        if self._solutions:
            sol = self._solutions[self._sol_index]
            for r in range(n):
                for c in range(n):
                    v = sol[r][c]
                    if v == 0:
                        self._sol_labels[r][c].config(text="0", bg="#2e2e2e", fg="#ffffff")
                    elif v == 1:
                        self._sol_labels[r][c].config(text="1", bg="#a6c8ff", fg="#113355")
                    else:
                        self._sol_labels[r][c].config(text=str(v), bg="#dddddd", fg="#000000")
            self._sol_status.set(f"共 {len(self._solutions)} 个解，当前显示第 {self._sol_index+1} 个")
        # 居中显示
        self.solution_sa.recenter()

    def _prev_solution(self):
        if not self._solutions:
            return
        self._sol_index = (self._sol_index - 1) % len(self._solutions)
        self._update_solution_view()

    def _next_solution(self):
        if not self._solutions:
            return
        self._sol_index = (self._sol_index + 1) % len(self._solutions)
        self._update_solution_view()

    # ===== 导入引擎文本 =====

    def _open_import_dialog(self):
        win = tk.Toplevel(self)
        win.title("导入引擎文本（K 与 (n+1)x(n+1) 数字矩阵）")
        win.geometry("800x520")
        tk.Label(win, text="粘贴引擎输入文本（第一行 K，其后 (n+1)x(n+1) 矩阵；支持空格/逗号/分号分隔）").pack(anchor="w", padx=8, pady=6)
        txt = tk.Text(win, wrap="none")
        txt.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        # 预填一个示例：当前模型导出的引擎文本
        try:
            txt.insert("1.0", "\n".join(self.model.build_engine_matrix_lines()))
        except:
            pass

        bar = ttk.Frame(win)
        bar.pack(fill=tk.X, padx=8, pady=6)
        ttk.Button(bar, text="从文件加载...", command=lambda: self._import_load_file_into_text(txt)).pack(side=tk.LEFT, padx=4)
        ttk.Button(bar, text="解析并导入", command=lambda: self._import_parse_and_apply(txt, win)).pack(side=tk.RIGHT, padx=4)
        ttk.Button(bar, text="取消", command=win.destroy).pack(side=tk.RIGHT, padx=4)

    def _import_load_file_into_text(self, text_widget):
        path = filedialog.askopenfilename(title="选择包含引擎文本的文件")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except:
            # 再试一次用系统缺省编码
            with open(path, "r") as f:
                content = f.read()
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", content)

    def _import_parse_and_apply(self, text_widget, win_to_close=None):
        text = text_widget.get("1.0", tk.END)
        try:
            K, n, col_targets, row_targets, board = self._parse_engine_input_text(text)
        except Exception as e:
            messagebox.showerror("解析失败", f"{e}")
            return

        # 应用到模型
        self.model.K = K
        self.entry_K.delete(0, tk.END)
        self.entry_K.insert(0, str(K))

        if n != self.model.n:
            self.model.resize(n)
            self.entry_n.delete(0, tk.END)
            self.entry_n.insert(0, str(n))

        self.model.col_targets = col_targets
        self.model.row_targets = row_targets
        self.model.board = board

        self._rebuild_grids()
        if win_to_close:
            win_to_close.destroy()
        messagebox.showinfo("导入成功", f"已导入：K={K}, n={n}")

    def _parse_engine_input_text(self, text):
        # 去掉 Solutions 块，只解析前 (1 + m) 行
        raw_lines = [ln.strip() for ln in text.splitlines()]
        # 过滤空行，并将 , ; 转为空格
        lines = []
        for ln in raw_lines:
            if not ln.strip():
                continue
            ln = ln.replace(",", " ").replace(";", " ")
            # 遇到 "Solutions:" 就停止（导入仅关心输入）
            if ln.lower().startswith("solutions:"):
                break
            lines.append(ln)

        if len(lines) < 2:
            raise ValueError("缺少 K 或矩阵首行")

        # 解析 K
        try:
            K = int(lines[0].split()[0])
        except:
            raise ValueError("第一行 K 解析失败")

        # 解析矩阵第一行（长度 m = n+1）
        try:
            top = [int(x) for x in lines[1].split()]
        except:
            raise ValueError("矩阵首行解析失败")
        m = len(top)
        if m < 2:
            raise ValueError("矩阵首行长度不足，应为 n+1")
        # 需要再有 m-1 行
        if len(lines) < 1 + m:
            raise ValueError(f"矩阵行数不足，应至少有 {m} 行（包含首行）")

        grid = [top]
        for i in range(m - 1):
            # 从 lines[2] 开始读取每一行
            try:
                row = [int(x) for x in lines[2 + i].split()]
            except:
                raise ValueError(f"矩阵第 {i+2} 行解析失败")
            if len(row) != m:
                raise ValueError(f"矩阵第 {i+2} 行长度应为 {m}，实际 {len(row)}")
            grid.append(row)

        # 生成 n、行列目标、棋盘
        n = m - 1
        col_targets = grid[0][1:]
        row_targets = [grid[r][0] for r in range(1, m)]

        # 校验值域
        board = [[-1 for _ in range(n)] for __ in range(n)]
        for r in range(n):
            for c in range(n):
                v = grid[r + 1][c + 1]
                if v not in (-1, 0, 1, 2, 3, 4, 5, 6):
                    raise ValueError(f"内部格子({r+1},{c+1})非法值 {v}（仅允许 -1/0/1/2/3/4/5/6）")
                board[r][c] = v

        # 非负目标
        for idx, t in enumerate(row_targets, 1):
            if t < 0:
                raise ValueError(f"第 {idx} 行目标为负数：{t}")
        for idx, t in enumerate(col_targets, 1):
            if t < 0:
                raise ValueError(f"第 {idx} 列目标为负数：{t}")

        return K, n, col_targets, row_targets, board

    # ===== 调试显示 =====

    def _show_last_input(self):
        if not self._last_input:
            messagebox.showinfo("引擎输入", "尚未求解或无记录。")
            return
        self._show_text_window("引擎输入", self._last_input)

    def _show_last_output(self):
        if not (self._last_stdout or self._last_stderr):
            messagebox.showinfo("引擎输出", "尚未求解或无记录。")
            return
        text = "[STDOUT]\n" + (self._last_stdout or "") + "\n\n[STDERR]\n" + (self._last_stderr or "")
        self._show_text_window("引擎输出", text)

    def _show_text_window(self, title, content):
        win = tk.Toplevel(self)
        win.title(title)
        txt = tk.Text(win, wrap="none", width=100, height=30)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", content)
        txt.configure(state="disabled")


if __name__ == "__main__":
    app = BattleshipUI()
    app.mainloop()