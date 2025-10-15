#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BattleShips Puzzle UI
A Tkinter-based UI for the BattleShips puzzle solver
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import re


def default_solver_name():
    if os.name == "nt":
        return "battleship_solver.exe"
    return "./battleship_solver"


class PuzzleModel:
    def __init__(self, n=10, K=4):
        self.n = n
        self.K = K
        self.board = [[-1 for _ in range(n)] for _ in range(n)]
        self.row_targets = [0] * n
        self.col_targets = [0] * n

    def resize(self, n_new):
        old_n = self.n
        self.n = n_new
        
        # Resize board
        new_board = [[-1 for _ in range(n_new)] for _ in range(n_new)]
        for r in range(min(old_n, n_new)):
            for c in range(min(old_n, n_new)):
                new_board[r][c] = self.board[r][c]
        self.board = new_board
        
        # Resize targets
        new_row_targets = [0] * n_new
        new_col_targets = [0] * n_new
        for i in range(min(old_n, n_new)):
            new_row_targets[i] = self.row_targets[i]
            new_col_targets[i] = self.col_targets[i]
        self.row_targets = new_row_targets
        self.col_targets = new_col_targets

    def toggle_left(self, r, c):
        """Toggle between unknown (-1) and water (0)"""
        if self.board[r][c] == -1:
            self.board[r][c] = 0
        else:
            self.board[r][c] = -1

    def cycle_right(self, r, c):
        """Cycle through: 0 -> 2 -> 3 -> 4 -> 5 -> 6 -> -1 -> 0"""
        val = self.board[r][c]
        if val == 0:
            self.board[r][c] = 2
        elif val == 2:
            self.board[r][c] = 3
        elif val == 3:
            self.board[r][c] = 4
        elif val == 4:
            self.board[r][c] = 5
        elif val == 5:
            self.board[r][c] = 6
        elif val == 6:
            self.board[r][c] = -1
        else:
            self.board[r][c] = 0

    def build_engine_matrix_lines(self):
        """
        Generate engine input text lines (K on first line, then (n+1)x(n+1) matrix)
        Interior cells can have values: -1,0,1,2,3,4,5,6
        """
        lines = []
        lines.append(str(int(self.K)))
        # First line: -1, col_targets...
        top = [-1] + [int(max(0, t)) for t in self.col_targets]
        lines.append(" ".join(map(str, top)))
        # Next n lines: each line row_target + n cells
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
        """Parse solver output to extract solution grids"""
        solutions = []
        lines = text.strip().split('\n')
        
        i = 0
        while i < len(lines):
            if lines[i].startswith('--- Solution'):
                # Read next n lines as solution
                sol = []
                for j in range(1, n + 1):
                    if i + j < len(lines):
                        row_str = lines[i + j].strip()
                        row = list(map(int, row_str.split()))
                        sol.append(row)
                if len(sol) == n:
                    solutions.append(sol)
                i += n + 1
            else:
                i += 1
        
        return solutions


class BattleshipUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("战舰解谜 UI（适配 C++ 引擎）")
        self.model = PuzzleModel(n=10, K=4)
        self.solver_path = tk.StringVar(value=default_solver_name())

        self._cell_labels = []   # Edit board cell Labels
        self._row_entries = []   # Row target Entries
        self._col_entries = []   # Column target Entries

        self._sol_labels = []    # Solution board cell Labels
        self._solutions = []
        self._sol_index = 0
        self._sol_status = tk.StringVar(value="尚未求解")

        # Debug views
        self._last_input = ""
        self._last_stdout = ""
        self._last_stderr = ""

        # Solver process control
        self._proc = None               # subprocess.Popen object
        self._stop_requested = False
        self._solver_thread = None

        self._build_widgets()
        self._update_board_display()

    def _build_widgets(self):
        # Top control frame
        controls = ttk.Frame(self)
        controls.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)

        # Board size controls
        ttk.Label(controls, text="棋盘大小:").pack(side=tk.LEFT)
        self.size_var = tk.IntVar(value=self.model.n)
        ttk.Entry(controls, textvariable=self.size_var, width=5).pack(side=tk.LEFT, padx=4)
        ttk.Button(controls, text="调整大小", command=self._resize_board).pack(side=tk.LEFT, padx=4)

        ttk.Label(controls, text="K(最大舰长):").pack(side=tk.LEFT, padx=(16, 0))
        self.k_var = tk.IntVar(value=self.model.K)
        ttk.Entry(controls, textvariable=self.k_var, width=5).pack(side=tk.LEFT, padx=4)

        # Engine controls
        engine = ttk.Frame(self)
        engine.pack(side=tk.TOP, fill=tk.X, padx=8, pady=4)

        ttk.Label(engine, text="引擎路径:").pack(side=tk.LEFT)
        ttk.Entry(engine, textvariable=self.solver_path, width=42).pack(side=tk.LEFT, padx=4)
        ttk.Button(engine, text="浏览", command=self._browse_solver).pack(side=tk.LEFT, padx=4)
        ttk.Button(engine, text="编译引擎(BattleShips.cpp)", command=self._compile_engine).pack(side=tk.LEFT, padx=8)
        self.btn_solve = ttk.Button(engine, text="求解", command=self._solve)
        self.btn_solve.pack(side=tk.LEFT, padx=4)
        self.btn_stop = ttk.Button(engine, text="停止分析", command=self._stop_solver, state="disabled")
        self.btn_stop.pack(side=tk.LEFT, padx=4)

        # Debug controls
        debug = ttk.Frame(self)
        debug.pack(side=tk.TOP, fill=tk.X, padx=8, pady=4)

        ttk.Button(debug, text="导入引擎文本", command=self._open_import_dialog).pack(side=tk.LEFT, padx=4)
        ttk.Button(debug, text="查看引擎输入", command=self._show_last_input).pack(side=tk.LEFT, padx=4)
        ttk.Button(debug, text="查看引擎输出", command=self._show_last_output).pack(side=tk.LEFT, padx=4)

        # Edit board (centered with scroll area)
        self.board_group = ttk.LabelFrame(self, text="编辑棋盘（左键：未知↔海水，右键：0→2→3→4→5→6→-1，键盘：W=水，U=未知，S=独舰）")
        self.board_group.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Solution display
        self.sol_group = ttk.LabelFrame(self, text="解决方案")
        self.sol_group.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=8)

        sol_ctrl = ttk.Frame(self.sol_group)
        sol_ctrl.pack(side=tk.TOP, fill=tk.X, padx=4, pady=4)

        ttk.Label(sol_ctrl, textvariable=self._sol_status).pack(side=tk.LEFT, padx=4)
        ttk.Button(sol_ctrl, text="上一个", command=self._prev_solution).pack(side=tk.LEFT, padx=4)
        ttk.Button(sol_ctrl, text="下一个", command=self._next_solution).pack(side=tk.LEFT, padx=4)

    def _resize_board(self):
        try:
            new_n = self.size_var.get()
            if new_n < 2 or new_n > 20:
                messagebox.showwarning("警告", "棋盘大小应在 2-20 之间")
                return
            self.model.resize(new_n)
            self._update_board_display()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")

    def _update_board_display(self):
        # Clear existing widgets
        for widget in self.board_group.winfo_children():
            widget.destroy()

        n = self.model.n
        self._cell_labels = []
        self._row_entries = []
        self._col_entries = []

        # Create grid container
        grid_frame = ttk.Frame(self.board_group)
        grid_frame.pack(padx=10, pady=10)

        # Top-left corner
        ttk.Label(grid_frame, text="", width=3).grid(row=0, column=0)

        # Column targets
        for c in range(n):
            entry = ttk.Entry(grid_frame, width=3)
            entry.grid(row=0, column=c + 1, padx=1, pady=1)
            entry.insert(0, str(self.model.col_targets[c]))
            entry.bind("<FocusOut>", lambda e, col=c: self._update_col_target(col, e.widget.get()))
            self._col_entries.append(entry)

        # Rows
        for r in range(n):
            # Row target
            entry = ttk.Entry(grid_frame, width=3)
            entry.grid(row=r + 1, column=0, padx=1, pady=1)
            entry.insert(0, str(self.model.row_targets[r]))
            entry.bind("<FocusOut>", lambda e, row=r: self._update_row_target(row, e.widget.get()))
            self._row_entries.append(entry)

            # Cells
            row_labels = []
            for c in range(n):
                lbl = tk.Label(grid_frame, text=self._cell_display(r, c), 
                             width=3, height=1, relief=tk.RAISED,
                             bg=self._cell_color(r, c), font=("Arial", 10, "bold"))
                lbl.grid(row=r + 1, column=c + 1, padx=1, pady=1)
                lbl.bind("<Button-1>", lambda e, rr=r, cc=c: self._on_left_click(rr, cc))
                lbl.bind("<Button-3>", lambda e, rr=r, cc=c: self._on_right_click(rr, cc))
                row_labels.append(lbl)
            self._cell_labels.append(row_labels)

        # Update solution display
        self._update_solution_display()

    def _cell_display(self, r, c):
        val = self.model.board[r][c]
        if val == -1:
            return "?"
        elif val == 0:
            return "~"
        elif val == 1:
            return "■"
        else:
            return str(val)

    def _cell_color(self, r, c):
        val = self.model.board[r][c]
        if val == -1:
            return "lightgray"
        elif val == 0:
            return "lightblue"
        elif val == 1:
            return "black"
        else:
            return "yellow"

    def _on_left_click(self, r, c):
        self.model.toggle_left(r, c)
        self._cell_labels[r][c].config(text=self._cell_display(r, c), bg=self._cell_color(r, c))

    def _on_right_click(self, r, c):
        self.model.cycle_right(r, c)
        self._cell_labels[r][c].config(text=self._cell_display(r, c), bg=self._cell_color(r, c))

    def _update_row_target(self, row, value):
        try:
            self.model.row_targets[row] = int(value)
        except ValueError:
            pass

    def _update_col_target(self, col, value):
        try:
            self.model.col_targets[col] = int(value)
        except ValueError:
            pass

    def _browse_solver(self):
        path = filedialog.askopenfilename(title="选择求解器可执行文件")
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

    def _solve(self):
        # Update K from UI
        try:
            self.model.K = self.k_var.get()
        except ValueError:
            messagebox.showerror("错误", "K 值无效")
            return

        solver_exe = self.solver_path.get()
        if not os.path.exists(solver_exe):
            messagebox.showerror("错误", f"求解器不存在: {solver_exe}")
            return

        # Build input
        lines = self.model.build_engine_matrix_lines()
        self._last_input = "\n".join(lines)

        # Disable solve button, enable stop button
        self.btn_solve.config(state="disabled")
        self.btn_stop.config(state="normal")
        self._stop_requested = False

        # Run solver in thread
        self._solver_thread = threading.Thread(target=self._run_solver, args=(solver_exe,))
        self._solver_thread.daemon = True
        self._solver_thread.start()

    def _run_solver(self, solver_exe):
        try:
            self._proc = subprocess.Popen(
                [solver_exe],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = self._proc.communicate(input=self._last_input, timeout=30)
            
            self._last_stdout = stdout
            self._last_stderr = stderr

            if self._stop_requested:
                self.after(0, lambda: self._sol_status.set("求解已取消"))
            elif self._proc.returncode == 0:
                # Parse solutions
                solutions = PuzzleModel.parse_solutions_from_output(stdout, self.model.n)
                self._solutions = solutions
                self._sol_index = 0
                
                if solutions:
                    self.after(0, lambda: self._sol_status.set(f"找到 {len(solutions)} 个解"))
                    self.after(0, self._update_solution_display)
                else:
                    self.after(0, lambda: self._sol_status.set("无解"))
            else:
                self.after(0, lambda: messagebox.showerror("求解失败", f"返回码: {self._proc.returncode}\n\nstderr:\n{stderr}"))
        except subprocess.TimeoutExpired:
            if self._proc:
                self._proc.kill()
            self.after(0, lambda: messagebox.showerror("超时", "求解超过 30 秒"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("异常", str(e)))
        finally:
            self.after(0, lambda: self.btn_solve.config(state="normal"))
            self.after(0, lambda: self.btn_stop.config(state="disabled"))
            self._proc = None

    def _stop_solver(self):
        self._stop_requested = True
        if self._proc:
            self._proc.terminate()

    def _update_solution_display(self):
        # Clear existing solution widgets
        for widget in self.sol_group.winfo_children():
            if widget != self.sol_group.winfo_children()[0]:  # Keep control frame
                widget.destroy()

        if not self._solutions:
            return

        if self._sol_index < 0 or self._sol_index >= len(self._solutions):
            return

        # Update status
        self._sol_status.set(f"解 {self._sol_index + 1} / {len(self._solutions)}")

        # Create solution grid
        sol = self._solutions[self._sol_index]
        n = len(sol)

        grid_frame = ttk.Frame(self.sol_group)
        grid_frame.pack(padx=10, pady=10)

        self._sol_labels = []
        for r in range(n):
            row_labels = []
            for c in range(n):
                val = sol[r][c]
                text = "~" if val == 0 else "■"
                bg = "lightblue" if val == 0 else "black"
                lbl = tk.Label(grid_frame, text=text, width=3, height=1, 
                             relief=tk.RAISED, bg=bg, font=("Arial", 10, "bold"))
                lbl.grid(row=r, column=c, padx=1, pady=1)
                row_labels.append(lbl)
            self._sol_labels.append(row_labels)

    def _prev_solution(self):
        if not self._solutions:
            return
        self._sol_index = (self._sol_index - 1) % len(self._solutions)
        self._update_solution_display()

    def _next_solution(self):
        if not self._solutions:
            return
        self._sol_index = (self._sol_index + 1) % len(self._solutions)
        self._update_solution_display()

    def _open_import_dialog(self):
        win = tk.Toplevel(self)
        win.title("导入引擎文本")
        win.geometry("600x400")

        ttk.Label(win, text="粘贴或加载引擎格式文本：").pack(padx=8, pady=8)

        txt = scrolledtext.ScrolledText(win, width=70, height=20)
        txt.pack(padx=8, pady=8, fill=tk.BOTH, expand=True)

        bar = ttk.Frame(win)
        bar.pack(fill=tk.X, padx=8, pady=6)
        ttk.Button(bar, text="从文件加载...", command=lambda: self._import_load_file_into_text(txt)).pack(side=tk.LEFT, padx=4)
        ttk.Button(bar, text="解析并导入", command=lambda: self._import_parse_and_apply(txt, win)).pack(side=tk.RIGHT, padx=4)
        ttk.Button(bar, text="取消", command=win.destroy).pack(side=tk.RIGHT, padx=4)

    def _import_load_file_into_text(self, text_widget):
        path = filedialog.askopenfilename(title="选择文本文件", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", content)

    def _import_parse_and_apply(self, text_widget, window):
        content = text_widget.get("1.0", tk.END).strip()
        lines = content.split('\n')
        
        try:
            # Parse K
            K = int(lines[0].strip())
            
            # Parse first data line
            first_line = list(map(int, lines[1].split()))
            col_targets = first_line[1:]  # Skip -1
            n = len(col_targets)
            
            # Parse board
            row_targets = []
            board = []
            for i in range(2, 2 + n):
                row_data = list(map(int, lines[i].split()))
                row_targets.append(row_data[0])
                board.append(row_data[1:])
            
            # Update model
            self.model.n = n
            self.model.K = K
            self.model.row_targets = row_targets
            self.model.col_targets = col_targets
            self.model.board = board
            
            self.size_var.set(n)
            self.k_var.set(K)
            
            self._update_board_display()
            window.destroy()
            messagebox.showinfo("成功", f"已导入 {n}x{n} 棋盘")
        except Exception as e:
            messagebox.showerror("解析失败", str(e))

    def _show_last_input(self):
        self._show_text_window("引擎输入", self._last_input)

    def _show_last_output(self):
        self._show_text_window("引擎输出（stdout）", self._last_stdout + "\n\n=== stderr ===\n" + self._last_stderr)

    def _show_text_window(self, title, content):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("700x500")

        txt = scrolledtext.ScrolledText(win, width=80, height=30)
        txt.pack(padx=8, pady=8, fill=tk.BOTH, expand=True)
        txt.insert("1.0", content)
        txt.config(state="disabled")

        ttk.Button(win, text="关闭", command=win.destroy).pack(pady=8)


def main():
    app = BattleshipUI()
    app.geometry("1200x800")
    app.mainloop()


if __name__ == "__main__":
    main()
