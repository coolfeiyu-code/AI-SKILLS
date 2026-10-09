# -*- coding: utf-8 -*-
"""AI-SKILLS 技能管理器 —— 零依赖 Tkinter 图形界面。

仅依赖 Python 标准库 + tkinter(tcl/tk)。
运行方式: 用含 tcl/tk 的 CPython 启动本文件(推荐双击 skillsync-gui.bat)。
"""
import os
import sys
import subprocess
import threading

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
except ModuleNotFoundError:
    sys.stderr.write(
        "错误: 当前 Python 缺少 tkinter 模块(需要带 tcl/tk 的 CPython)。\n"
        "请用 skillsync-gui.bat 启动, 或改用含 tcl/tk 的 Python 解释器。\n"
    )
    sys.exit(1)

REPO = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(REPO, "skillsync.py")

# ---- 主题: 深墨 / Linear-Vercel 克制风 ----
BG = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
TEXT = "#e6edf3"
MUTED = "#8b949e"
ACCENT = "#2ea043"   # 主操作(绿)
BLUE = "#388bfd"     # 次操作(蓝)
WARN = "#d29922"
DANGER = "#f85149"
NEUTRAL = "#21262d"
MONO = ("Consolas", "Cascadia Code", "Menlo", "Courier New", 11)
UI = ("Segoe UI", "Microsoft YaHei", "PingFang SC", 10)


class SkillManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI-SKILLS 技能管理器")
        self.root.geometry("880x620")
        self.root.minsize(720, 480)
        self.root.configure(bg=BG)
        self.running = False
        self.queue = []
        self._build()
        self.log(f"仓库: {REPO}")
        self.log(f"CLI : {os.path.basename(CLI)}  ·  Python {sys.version.split()[0]}")
        self.log("就绪。点击上方按钮执行操作。\n")

    # ---------- UI ----------
    def _build(self):
        # 标题栏
        hdr = tk.Frame(self.root, bg=PANEL, height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="AI-SKILLS 技能管理器", bg=PANEL, fg=TEXT,
                 font=(*UI, 13, "bold")).pack(side="left", padx=16)
        tk.Label(hdr, text="状态 · 更新 · 发现 · 同步", bg=PANEL, fg=MUTED,
                 font=UI).pack(side="left", padx=6)
        self.status_var = tk.StringVar(value="就绪")
        tk.Label(hdr, textvariable=self.status_var, bg=PANEL, fg=BLUE,
                 font=UI, anchor="e").pack(side="right", padx=16)

        # 工具栏
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill="x")
        self.btn_status = self._btn(bar, "状态", BLUE, self.cmd_status)
        self.btn_update = self._btn(bar, "检查更新", WARN, self.cmd_update)
        self.btn_all = self._btn(bar, "一键更新全部", ACCENT, self.cmd_all)
        self.btn_discover = self._btn(bar, "发现新技能", BLUE, self.cmd_discover)
        self.btn_sync = self._btn(bar, "推送同步", BLUE, self.cmd_sync)
        self.btn_version = self._btn(bar, "版本", NEUTRAL, self.cmd_version)
        self._btn(bar, "打开目录", NEUTRAL, self.cmd_open, side="right")

        # 输出区
        out_frame = tk.Frame(self.root, bg=BG)
        out_frame.pack(fill="both", expand=True, padx=12, pady=(2, 12))
        self.out = scrolledtext.ScrolledText(
            out_frame, bg="#0a0e14", fg=TEXT, insertbackground=TEXT,
            font=MONO, relief="flat", borderwidth=0,
            wrap="word", padx=14, pady=12,
            highlightbackground=BORDER, highlightthickness=1,
        )
        self.out.pack(fill="both", expand=True)
        self.out.bind("<Key>", lambda e: "break")  # 只读
        self.out.tag_config("ok", foreground=ACCENT)
        self.out.tag_config("warn", foreground=WARN)
        self.out.tag_config("err", foreground=DANGER)
        self.out.tag_config("cmd", foreground=BLUE, font=(*MONO, "bold"))

    def _btn(self, parent, text, color, cmd, side="left"):
        fg = "#0d1117" if color == NEUTRAL else "#ffffff"
        b = tk.Button(parent, text=text, command=cmd, bg=color, fg=fg,
                      activebackground=color, activeforeground=fg,
                      font=UI, relief="flat", bd=0, padx=14, pady=7, cursor="hand2")
        b.pack(side=side, padx=6, pady=10)
        return b

    # ---------- 日志 ----------
    def log(self, text, tag=None):
        self.out.insert("end", text + "\n", tag)
        self.out.see("end")

    # ---------- 任务队列 ----------
    def _set_running(self, state, label=""):
        self.running = state
        self.status_var.set(label or ("运行中…" if state else "就绪"))
        st = "disabled" if state else "normal"
        for b in (self.btn_status, self.btn_update, self.btn_all,
                  self.btn_discover, self.btn_sync, self.btn_version):
            b.configure(state=st)

    def _enqueue(self, args, label, on_done=None):
        self.queue.append((args, label, on_done))
        if not self.running:
            self.run_queue()

    def run_queue(self):
        if not self.queue:
            self._set_running(False)
            return
        args, label, on_done = self.queue.pop(0)
        self._set_running(True, label)
        self.log(f"$ python {os.path.basename(CLI)} {' '.join(args)}", "cmd")
        threading.Thread(target=self._worker, args=(args, on_done),
                         daemon=True).start()

    def _worker(self, args, on_done):
        try:
            proc = subprocess.Popen(
                [sys.executable, CLI, *args],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, cwd=REPO,
                encoding="utf-8", errors="replace",
            )
            for line in proc.stdout:
                self.root.after(0, self.log, line.rstrip("\n"))
            rc = proc.wait()
            self.root.after(0, self._on_finish, rc, on_done)
        except Exception as exc:  # noqa: BLE001
            self.root.after(0, self.log, f"[异常] {exc}", "err")
            self.root.after(0, self._on_finish, 1, on_done)

    def _on_finish(self, rc, on_done):
        if rc == 0:
            self.log("✓ 完成", "ok")
        else:
            self.log(f"✗ 退出码 {rc}", "err")
        self.log("")
        if on_done:
            on_done(rc)
        self.run_queue()

    # ---------- 命令 ----------
    def cmd_status(self):
        self._enqueue(["status"], "状态")

    def cmd_update(self):
        self._enqueue(["update"], "检查更新")

    def cmd_discover(self):
        self._enqueue(["discover"], "发现新技能")

    def cmd_sync(self):
        self._enqueue(["sync", "--push"], "推送同步")

    def cmd_version(self):
        self._enqueue(["version"], "版本")

    def cmd_all(self):
        # 检查更新 -> 全部更新(本地提交) -> 提交并推送
        self._enqueue(["update"], "检查更新",
                      on_done=lambda rc: (
                          self._enqueue(["sync", "--push"], "推送同步")
                          if rc == 0 else None))

    def cmd_open(self):
        try:
            os.startfile(REPO)
        except Exception:
            subprocess.Popen(["explorer", REPO])


def main():
    if not os.path.exists(CLI):
        try:
            messagebox.showerror("错误", f"未找到 CLI 文件:\n{CLI}")
        except Exception:
            pass
        return
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except Exception:
        pass
    SkillManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
