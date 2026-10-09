#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skillsync.py — AI-SKILLS 技能库跨平台管理 CLI（零依赖，仅 Python 标准库）

子命令:
  status              查看每个受管技能的 本地基线 / 上游最新 / 是否待更新 / pinned
  update [--dry-run]  一键更新：仅对「上游更新且非 pinned」的技能用 tarball 覆盖并更新
  discover [--top N]  在 GitHub 按 star 发现与你兴趣相关的高星技能，仅列出候选（已校验仓库含 SKILL.md，过滤非 skill 框架）
  sync [--push]       提交本地变更（--push 才推送到 origin/main）
  version             打印项目版本号

设计原则（无垃圾公约）:
  - 所有下载的 tarball / 解压 / 缓存 / 日志一律写入仓库【外】的系统缓存目录，
    绝不写入本仓库；提交前用 git status --porcelain 自检。
  - 运行时产物外置路径:
      Win : %LOCALAPPDATA%/skillsync
      Mac : ~/Library/Caches/skillsync 或 ~/.cache/skillsync
"""

import os
import sys
import json
import time
import shutil
import argparse
import subprocess
import urllib.request
import urllib.error
import datetime

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(REPO_ROOT, "VERSION")

# ---------------------------------------------------------------------------
# 受管技能映射（单一事实源；可被 config/sources.json 覆盖）
#   folder  : 仓库内的技能目录名
#   repo    : GitHub owner/name
#   subpath : 技能在仓库内的子路径（空=仓库根）；适配上游结构变化
#   pinned  : True 表示跳过自动更新（本地较新 / 本地移植版，覆盖会降级或丢改造）
# ---------------------------------------------------------------------------
SOURCES = [
    {"folder": "a-stock-data",                 "repo": "simonlin1212/a-stock-data",                 "subpath": "",                   "pinned": False},
    {"folder": "agent-reach",                  "repo": "Panniantong/Agent-Reach",                  "subpath": "agent_reach/skill",  "pinned": False},
    {"folder": "frontend-design",              "repo": "anthropics/skills",                        "subpath": "skills/frontend-design", "pinned": False},
    {"folder": "grill-me",                     "repo": "mattpocock/skills",                        "subpath": "",                   "pinned": True},
    {"folder": "Humanizer-zh",                 "repo": "op7418/Humanizer-zh",                     "subpath": "",                   "pinned": False},
    {"folder": "impeccable",                   "repo": "pbakaus/impeccable",                      "subpath": "",                   "pinned": False},
    {"folder": "InvestSkill",                  "repo": "yennanliu/InvestSkill",                    "subpath": "",                   "pinned": False},
    {"folder": "last30days",                   "repo": "mvanhorn/last30days-skill",               "subpath": "",                   "pinned": False},
    {"folder": "last30days-cn",                "repo": "Jesseovo/last30days-skill-cn",            "subpath": "",                   "pinned": False},
    {"folder": "serenity-skill",               "repo": "muxuuu/serenity-skill",                   "subpath": "",                   "pinned": False},
    {"folder": "ui-ux-pro-max",                "repo": "nextlevelbuilder/ui-ux-pro-max-skill",    "subpath": "",                   "pinned": False},
    {"folder": "trading-skills",               "repo": "marian2js/trading-skills",                 "subpath": "",                   "pinned": True},
    {"folder": "interface-design",             "repo": "Dammyjay93/interface-design",              "subpath": "",                   "pinned": True},
    {"folder": "gauss314-skills",              "repo": "gauss314/skills",                          "subpath": "",                   "pinned": True},
]

# ---------------------------------------------------------------------------
# discover 的兴趣主题（可被 config/interests.json 覆盖）
# ---------------------------------------------------------------------------
INTERESTS = [
    {"category": "web/前端设计", "keywords": ["frontend-design", "ui", "ux", "tailwind", "shadcn", "design-system", "animation", "figma", "css", "landing-page", "web"]},
    {"category": "投研/金融",    "keywords": ["stock", "investing", "finance", "trading", "quant", "a-share", "valuation", "research", "portfolio", "investment"]},
    {"category": "中文内容",      "keywords": ["chinese", "nlp", "writing", "humanize", "prompt", "copywriting", "中文"]},
    {"category": "agent/工具",    "keywords": ["agent", "skill", "claude-skill", "cursor", "workflow", "automation", "mcp", "agentic"]},
    {"category": "生产力",        "keywords": ["productivity", "note", "knowledge", "search", "memory", "second-brain"]},
]

# 只在这些「技能相关」topic 下搜索，避免把 n8n/dify 这类大项目误判为 skill
DISCOVER_TOPICS = ["claude-code", "claude-skill", "cursor-rules", "agent-skill", "skills", "prompt-engineering"]


# ---------------------------------------------------------------------------
# 缓存与网络
# ---------------------------------------------------------------------------
def cache_dir() -> str:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    else:
        base = os.path.join(os.path.expanduser("~"), "Library", "Caches")
        if not os.path.isdir(base):
            base = os.path.expanduser("~/.cache")
    d = os.path.join(base, "skillsync")
    os.makedirs(d, exist_ok=True)
    return d


def _download(url: str, path: str, timeout: int = 120) -> None:
    """下载文件到 path: 先走系统代理, 失败绕过代理直连重试(规避 Clash 等代理异常)。"""
    try:
        urllib.request.urlretrieve(url, path)
        return
    except urllib.error.HTTPError:
        raise
    except Exception:
        pass
    req = urllib.request.Request(url, headers={"User-Agent": "skillsync"})
    direct = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with direct.open(req, timeout=timeout) as r, open(path, "wb") as f:
        f.write(r.read())


def api_get(url: str):
    """带文件缓存的 GitHub API GET（缓存 1 小时，尊重 60次/小时 限流）。
    网络层先走系统代理，失败自动绕过代理直连重试（规避 Clash 等系统代理异常）。"""
    cfile = os.path.join(cache_dir(), "api_cache.json")
    cache = {}
    if os.path.isfile(cfile):
        try:
            cache = json.load(open(cfile, encoding="utf-8"))
        except Exception:
            cache = {}
    if url in cache:
        entry = cache[url]
        if time.time() - entry.get("ts", 0) < 3600:
            return entry["data"]
    req = urllib.request.Request(url, headers={"User-Agent": "skillsync", "Accept": "application/vnd.github+json"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    try:
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode())
        except urllib.error.HTTPError:
            raise
        except Exception:
            direct = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with direct.open(req, timeout=30) as r:
                data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} for {url}")
    except Exception as e:
        raise RuntimeError(f"网络错误: {e}")
    cache[url] = {"ts": time.time(), "data": data}
    try:
        json.dump(cache, open(cfile, "w", encoding="utf-8"))
    except Exception:
        pass
    return data


def get_default_branch(repo: str) -> str:
    data = api_get(f"https://api.github.com/repos/{repo}")
    return data.get("default_branch", "main")


def get_latest_commit_date(repo: str):
    data = api_get(f"https://api.github.com/repos/{repo}/commits?per_page=1")
    if isinstance(data, list) and data:
        return data[0]["commit"]["author"]["date"][:10]
    return None


def git(*args):
    return subprocess.run(["git", "-C", REPO_ROOT, *args], capture_output=True, text=True)


def local_baseline(folder: str):
    try:
        out = git("log", "-1", "--format=%ci", "--", folder).stdout.strip()
        return out[:10] if out else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 子命令实现
# ---------------------------------------------------------------------------
def cmd_status(args):
    print(f"{'技能':32} {'本地基线':12} {'上游最新':12} 状态")
    print("-" * 70)
    for s in SOURCES:
        base = local_baseline(s["folder"])
        try:
            up = get_latest_commit_date(s["repo"])
        except Exception:
            up = "?"
        if s.get("pinned"):
            flag = "pinned(跳过)"
        elif up == "?" or not base:
            flag = "未知"
        elif up > base:
            flag = "⚠ 需要更新"
        else:
            flag = "✓ 最新"
        print(f"{s['folder']:32} {str(base):12} {str(up):12} {flag}")


def apply_update(s: dict) -> None:
    repo = s["repo"]
    sub = s.get("subpath", "")
    branch = get_default_branch(repo)
    safe = repo.replace("/", "_")
    tgz = os.path.join(cache_dir(), f"{safe}.tgz")
    _download(f"https://codeload.github.com/{repo}/tar.gz/refs/heads/{branch}", tgz)
    ex = os.path.join(cache_dir(), safe)
    if os.path.isdir(ex):
        shutil.rmtree(ex)
    os.makedirs(ex)
    shutil.unpack_archive(tgz, ex)
    top = next(d for d in os.listdir(ex) if os.path.isdir(os.path.join(ex, d)))
    src = os.path.join(ex, top, sub) if sub else os.path.join(ex, top)
    folder = os.path.join(REPO_ROOT, s["folder"])
    if os.path.isdir(folder):
        git("rm", "-r", "-q", "--ignore-unmatch", s["folder"])
    shutil.copytree(src, folder)


def cmd_update(args):
    dry = args.dry_run
    updated = []
    for s in SOURCES:
        folder = s["folder"]
        if s.get("pinned"):
            print(f"[pinned] 跳过 {folder}（本地定制，覆盖会降级/丢改造）")
            continue
        base = local_baseline(folder)
        try:
            up = get_latest_commit_date(s["repo"])
        except Exception as e:
            print(f"[warn] {folder}: 无法获取上游 ({e})")
            continue
        if not base:
            print(f"[skip] {folder}: 本地无 git 基线，请手动安装")
            continue
        if up and up > base:
            print(f"[update] {folder}: {base} -> {up}  ({s['repo']})")
            if not dry:
                try:
                    apply_update(s)
                    updated.append(folder)
                except Exception as e:
                    print(f"[error] {folder} 更新失败: {e}")
        else:
            print(f"[ok] {folder} 已是最新 ({base})")
    if updated and not dry:
        msg = "chore: 更新技能 " + ", ".join(updated)
        git("add", "-A")
        git("commit", "-q", "-m", msg)
        print(f"\n已提交更新: {msg}")
    elif dry:
        print("\n(dry-run，未做任何改动)")


def matches_interests(text: str) -> bool:
    text = text.lower()
    for cat in INTERESTS:
        for kw in cat["keywords"]:
            if kw.lower() in text:
                return True
    return False


def repo_has_skill_md(full: str, desc: str = "") -> bool:
    """校验仓库根目录是否真的含 SKILL.md 或 skills/ 子目录，过滤掉 dify/n8n 这类非 skill 框架。
    - 正常：按 contents API 结果判定。
    - 命中限流(403/429)：改用廉价文本启发式（名称/描述含 'skill' 才保留），避免大框架漏入。
    - 其他网络错误：保守返回 True，保留候选而非误删。"""
    try:
        data = api_get(f"https://api.github.com/repos/{full}/contents/")
    except RuntimeError as e:
        msg = str(e)
        if "403" in msg or "429" in msg:
            hay = f"{full} {desc}".lower()
            return "skill" in hay
        return True
    except Exception:
        return True
    if not isinstance(data, list):
        return True
    for it in data:
        n = (it.get("name") or "").lower()
        if n == "skill.md":
            return True
        if it.get("type") == "dir" and n in ("skills", "skill"):
            return True
    return False


def cmd_discover(args):
    n = args.top
    min_stars = args.min_stars
    existing_repos = {s["repo"].lower() for s in SOURCES}
    existing_folders = {
        d for d in os.listdir(REPO_ROOT)
        if os.path.isdir(os.path.join(REPO_ROOT, d)) and os.path.isfile(os.path.join(REPO_ROOT, d, "SKILL.md"))
    }
    seen = set()
    cands = []
    for t in DISCOVER_TOPICS:
        try:
            data = api_get(
                f"https://api.github.com/search/repositories?q=topic:{t}+stars:%3E{min_stars}&sort=stars&order=desc&per_page=30"
            )
        except Exception as e:
            print(f"[warn] topic {t}: {e}")
            continue
        for it in data.get("items", []):
            full = it["full_name"]
            if full in seen or full.lower() in existing_repos:
                continue
            name = it["name"].lower()
            if name in ("claude-code", "cursor", "claude", "codex"):
                continue
            if name in existing_folders:
                continue
            seen.add(full)
            hay = f"{full} {it.get('description') or ''}".lower()
            if matches_interests(hay):
                cands.append((it["stargazers_count"], full, it.get("description", ""), it["html_url"]))
    # 仅对高星候选做 SKILL.md 校验（控制 API 调用量），过滤非 skill 仓库
    cands.sort(reverse=True)
    verify_cap = max(n * 2, 20)
    results = []
    skipped = 0
    for stars, full, desc, url in cands[:verify_cap]:
        if repo_has_skill_md(full, desc):
            results.append((stars, full, desc, url))
        else:
            skipped += 1
        if len(results) >= n:
            break
    print(f"发现 {len(results)} 个候选高星相关技能（按 star 降序；已过滤 {skipped} 个非 skill 仓库）：\n")
    for stars, full, desc, url in results:
        print(f"- **{full}**  ⭐{stars}\n  {desc}\n  {url}\n")
    out = os.path.join(cache_dir(), "discover-candidates.md")
    with open(out, "w", encoding="utf-8") as f:
        for stars, full, desc, url in results:
            f.write(f"- **{full}** ⭐{stars} — {desc} ({url})\n")
    print(f"(候选清单已存至仓库外缓存，不污染本仓库: {out})")


def cmd_sync(args):
    st = git("status", "--porcelain")
    if st.stdout.strip():
        git("add", "-A")
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        git("commit", "-q", "-m", f"chore: 同步技能库 {ts}")
        print("已提交本地变更。")
    else:
        print("无本地变更，无需提交。")
    if args.push:
        r = git("push", "origin")
        print(r.stdout or r.stderr)
    else:
        print("未推送。如需推送到 GitHub，加 --push（或运行 skillsync sync --push）。")


def cmd_version(args):
    try:
        print(open(VERSION_FILE, encoding="utf-8").read().strip())
    except Exception:
        print("unknown")


# ---------------------------------------------------------------------------
# 可选配置覆盖（config/*.json 若存在则覆盖内嵌默认值）
# ---------------------------------------------------------------------------
def load_config():
    global SOURCES, INTERESTS
    p = os.path.join(REPO_ROOT, "config", "sources.json")
    if os.path.isfile(p):
        try:
            SOURCES = json.load(open(p, encoding="utf-8"))
        except Exception:
            pass
    p = os.path.join(REPO_ROOT, "config", "interests.json")
    if os.path.isfile(p):
        try:
            INTERESTS = json.load(open(p, encoding="utf-8"))
        except Exception:
            pass


def main():
    load_config()
    parser = argparse.ArgumentParser(description="AI-SKILLS 技能库跨平台管理 CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="查看各技能 本地基线/上游最新/更新状态")
    p_up = sub.add_parser("update", help="一键更新技能（默认本地提交，不推送）")
    p_up.add_argument("--dry-run", action="store_true", help="只报告，不改动")
    p_dc = sub.add_parser("discover", help="发现相关高星技能（仅列出候选）")
    p_dc.add_argument("--top", type=int, default=20, help="返回候选数量")
    p_dc.add_argument("--min-stars", type=int, default=50, help="最低 star 阈值（默认 50）")
    p_sy = sub.add_parser("sync", help="提交本地变更（默认不推送）")
    p_sy.add_argument("--push", action="store_true", help="提交并推送到 origin/main")
    sub.add_parser("version", help="打印项目版本号")

    args = parser.parse_args()
    {"status": cmd_status, "update": cmd_update, "discover": cmd_discover,
     "sync": cmd_sync, "version": cmd_version}[args.cmd](args)


if __name__ == "__main__":
    main()
