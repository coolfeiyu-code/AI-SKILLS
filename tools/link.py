#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/link.py — 把本技能库一键连接到本机所有 Coding 工具（零依赖, 跨平台）。

原则(无垃圾公约): 只在【工具侧】创建目录链接(Junction/Symlink)指向技能库,
绝不向技能库仓库写入任何文件; 目标目录已有同名"真实目录"则跳过并报告。

用法:
  python tools/link.py --detect    # 探测本机各 coding 工具的技能目录
  python tools/link.py --all       # 一键: 所有探测到的工具全部连上
  python tools/link.py --to DIR    # 额外连接到指定 skills 目录(可多次, 自动记住)
  python tools/link.py --status    # 查看 连接矩阵
  python tools/link.py --remove    # 撤销本工具创建的所有链接(不动真实目录)
  python tools/link.py --prompt    # 打印可粘贴给任意 coding 工具的"自连接提示词"
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOME = Path.home()
STATE = HOME / ".skillsync-links.json"   # 本机额外目标(存仓库外, 不污染仓库)

# 已知工具的技能目录(按约定 ~/.<工具>/skills); 未知工具靠启发式扫描兜底
KNOWN_TOOLS = [
    ("WorkBuddy", ".workbuddy/skills"),
    ("Claude Code", ".claude/skills"),
    ("CodeBuddy", ".codebuddy/skills"),
    ("Codex CLI", ".codex/skills"),
    ("Cursor", ".cursor/skills"),
    ("Trae", ".trae/skills"),
    ("Windsurf", ".windsurf/skills"),
    ("Cline", ".cline/skills"),
    ("Roo Code", ".roo/skills"),
    ("OpenCode", ".opencode/skills"),
    ("Crush", ".crush/skills"),
    ("Grok CLI", ".grok/skills"),
    ("zcode", ".zcode/skills"),
    ("pi", ".pi/skills"),
    ("commandcode", ".commandcode/skills"),
    ("dsh", ".dsh/skills"),
    ("Gemini CLI", ".gemini/skills"),
    ("Qwen Code", ".qwen/skills"),
    ("iFlow CLI", ".iflow/skills"),
]


def skill_dirs():
    """技能库根下所有含 SKILL.md 的技能目录。"""
    return sorted(p for p in REPO.iterdir()
                  if p.is_dir() and (p / "SKILL.md").is_file())


def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(st):
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def candidate_targets(create=True):
    """返回 [(工具名, skills目录)]; 已知列表 + 启发式扫描(~/.*/skills) + 用户额外(--to)。"""
    found = {}
    for name, rel in KNOWN_TOOLS:
        found[str((HOME / rel).resolve())] = (name, HOME / rel)
    # 启发式: 任何 ~/.<name>/skills 已存在目录都算候选(覆盖未知工具)
    try:
        for p in HOME.iterdir():
            if p.name.startswith(".") and p.is_dir():
                sk = p / "skills"
                if sk.is_dir():
                    found.setdefault(str(sk.resolve()), (p.name.lstrip("."), sk))
    except OSError:
        pass
    for extra in load_state().get("extra_targets", []):
        e = Path(extra)
        found.setdefault(str(e.resolve()), (e.name or "自定义", e))
    out = []
    for _, (name, path) in sorted(found.items(), key=lambda kv: kv[1][0].lower()):
        if path.is_dir():
            out.append((name, path))
        elif create and name in {n for n, _ in KNOWN_TOOLS}:
            out.append((name, path))   # 已知工具允许创建 skills 目录
    return out


def resolve_into_repo(p: Path):
    """路径(链接)最终指向是否在本仓库内。"""
    try:
        return str(Path(p).resolve()).lower().startswith(str(REPO.resolve()).lower())
    except OSError:
        return False


def make_link(link: Path, target: Path):
    if os.name == "nt":
        # mklink 输出为本地编码(GBK), 用字节模式避免解码线程异常
        r = subprocess.run(f'mklink /J "{link}" "{target}"', shell=True,
                           capture_output=True)
        if r.returncode != 0 or not link.exists():
            err = ((r.stderr or b"") + (r.stdout or b"")).decode("utf-8", "replace")
            raise RuntimeError(err.strip() or "mklink 失败")
    else:
        os.symlink(target, link)


def sweep_dangling(targets):
    """清理指向本仓库、但目标技能已被删除的悬挂链接。返回 (数量, 明细行)。"""
    removed, lines = 0, []
    repo_low = str(REPO).lower()
    for tname, tdir in targets:
        if not tdir.is_dir():
            continue
        for p in list(tdir.iterdir()):
            if p.exists():
                continue
            try:
                inside = str(p.resolve()).lower().startswith(repo_low)
            except OSError:
                continue
            if inside:
                try:
                    os.rmdir(p)
                    removed += 1
                    lines.append(f"  [清悬挂] {tname}: {p.name} (指向的技能已被删除)")
                except OSError as e:
                    lines.append(f"  [失败]   {tname}: {p.name} -> {e}")
    return removed, lines


def remove_link(link: Path):
    if link.is_symlink():
        link.unlink()
    else:  # junction: rmdir 只删链接本身
        os.rmdir(link)


def link_all(targets, skills):
    ok = skip = collide = fail = 0
    swept, swept_lines = sweep_dangling(targets)
    for ln in swept_lines:
        print(ln)
    for tname, tdir in targets:
        tdir.mkdir(parents=True, exist_ok=True)
        for sk in skills:
            link = tdir / sk.name
            if link.exists() or link.is_symlink():
                if resolve_into_repo(link):
                    ok += 1                     # 已连过
                else:
                    collide += 1                # 工具侧同名真实目录
                    print(f"  [同名跳过] {tname}: {sk.name} (工具侧已有真实目录)")
                continue
            try:
                make_link(link, sk)
                ok += 1
                print(f"  [已连接] {tname}: {sk.name}")
            except Exception as e:  # noqa: BLE001
                fail += 1
                print(f"  [失败]   {tname}: {sk.name} -> {e}")
    return ok, skip, collide, fail


def cmd_detect():
    print(f"技能库: {REPO}")
    print(f"技能数: {len(skill_dirs())}")
    print("\n本机探测到的 coding 工具技能目录:")
    for name, path in candidate_targets():
        n = len(list(path.iterdir())) if path.is_dir() else 0
        print(f"  {name:14} {path}   ({n} 项)")
    print("\n提示: 未列出的工具只要遵循 ~/.<工具>/skills 约定, 出现后会被自动识别;")
    print("      也可以用 --to <目录> 手动指定。")


def cmd_all(args):
    targets = candidate_targets()
    if args.to:
        targets += [(Path(t).name or "自定义", Path(t)) for t in args.to]
    skills = skill_dirs()
    print(f"技能库: {REPO}  (技能 {len(skills)} 个)")
    print(f"目标工具: {len(targets)} 个\n")
    ok, _, collide, fail = link_all(targets, skills)
    print(f"\n完成: 连接 {ok} · 同名跳过 {collide} · 失败 {fail}")
    if args.to:
        st = load_state()
        extra = set(st.get("extra_targets", [])) | set(args.to)
        st["extra_targets"] = sorted(extra)
        save_state(st)
        print(f"自定义目标已记住: {sorted(extra)} (存于 {STATE}, 不进仓库)")
    print("工具侧若未立即生效, 重启对应工具即可。")


def cmd_status():
    skills = {s.name for s in skill_dirs()}
    print(f"技能库: {REPO}  (技能 {len(skills)} 个)\n")
    print(f"{'工具':14} {'目录':50} 连接/同名/总项")
    total_linked = 0
    for name, tdir in candidate_targets():
        if not tdir.is_dir():
            continue
        linked = collide = 0
        for p in tdir.iterdir():
            if p.name in skills:
                if resolve_into_repo(p):
                    linked += 1
                else:
                    collide += 1
        total_linked += linked
        print(f"  {name:12} {str(tdir)[:50]:50} {linked:3}   {collide:3}   {len(list(tdir.iterdir())):3}")
    print(f"\n合计连接: {total_linked} 条链接指向本仓库 (零污染: 链接在工具侧, 仓库只读)")


def cmd_remove():
    removed = 0
    for name, tdir in candidate_targets():
        if not tdir.is_dir():
            continue
        for p in list(tdir.iterdir()):
            if p.name in {s.name for s in skill_dirs()} and resolve_into_repo(p):
                try:
                    remove_link(p)
                    removed += 1
                    print(f"  [已撤销] {name}: {p.name}")
                except OSError as e:
                    print(f"  [失败]   {name}: {p.name} -> {e}")
    print(f"\n共撤销 {removed} 条链接; 工具侧真实目录未受影响。")


def cmd_prompt():
    print("=== 把下面整段提示词粘贴给任意 coding 工具即可(方案B: 自连接) ===\n")
    print(f"""本机有一份统一 AI 技能库, 路径: {REPO}
请把你的技能目录与它连接起来, 严格按以下要求执行:
1. 确定你读取技能的目录(通常是 ~/.<你的工具名>/skills, 以你自己的实际配置为准);
2. 扫描技能库根目录, 其中每个包含 SKILL.md 的文件夹就是一个技能;
3. 在你的技能目录内, 为每个技能创建指向技能库对应文件夹的【目录链接】:
   - Windows: cmd /c mklink /J "<你的skills目录>\\<技能名>" "<技能库>\\<技能名>" (junction, 无需管理员)
   - macOS/Linux: ln -s "<技能库>/<技能名>" "<你的skills目录>/<技能名>"
4. 若你的技能目录中已存在同名"真实目录", 跳过该技能并明确告诉我;
5. 【红线】技能库目录是只读来源, 严禁在其中创建/修改/删除任何文件或写入缓存日志;
6. 完成后汇报: 已连接清单 / 同名跳过清单 / 失败清单。""")


def main():
    ap = argparse.ArgumentParser(description="技能库 ↔ coding 工具 连接器")
    ap.add_argument("--detect", action="store_true", help="探测本机工具技能目录")
    ap.add_argument("--all", action="store_true", help="一键连接所有探测到的工具")
    ap.add_argument("--to", action="append", default=[], metavar="DIR",
                    help="额外目标 skills 目录(可多次)")
    ap.add_argument("--status", action="store_true", help="查看连接矩阵")
    ap.add_argument("--remove", action="store_true", help="撤销所有本工具创建的链接")
    ap.add_argument("--prompt", action="store_true", help="打印自连接提示词(方案B)")
    args = ap.parse_args()
    if not any((args.detect, args.all, args.status, args.remove, args.prompt)):
        args.detect = True
        print("(未指定动作, 默认 --detect)\n")
    if args.detect:
        cmd_detect()
    if args.all:
        cmd_all(args)
    if args.status:
        cmd_status()
    if args.remove:
        cmd_remove()
    if args.prompt:
        cmd_prompt()


if __name__ == "__main__":
    main()
