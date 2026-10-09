# -*- coding: utf-8 -*-
"""AI-SKILLS 技能管理 Web 仪表盘 —— 零依赖(stdlib only)。

所有机器可直接使用: 仅需 Python 3.11+ 与 git, 无需 tkinter / 无需 pip 安装。
运行:
    python skillsync_web.py [--port 8766] [--host 127.0.0.1]
然后浏览器打开 http://localhost:8766

功能:
    - 表格展示所有技能: 名称 / 作用 / 版本号 / 最后更新 / 来源仓库 / 固定 / 操作
    - 新增技能: 填仓库与子路径, 自动克隆安装并登记到 config/sources.json
    - 删除技能: 从仓库移除并提交删除(需另行同步)
    - 一键: 状态 / 检查更新 / 发现新技能 / 提交本地 / 推送远端
"""
import os
import re
import io
import sys
import json
import shutil
import contextlib
import subprocess
import tempfile
import datetime
import html
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

REPO = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(REPO, "skillsync.py")
SOURCES = os.path.join(REPO, "config", "sources.json")
CATALOG = os.path.join(REPO, "CATALOG.md")
VERSION_FILE = os.path.join(REPO, "VERSION")
START_TS = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# 复用统一连接器(tools/link.py): 探测/连接/撤销/提示词
sys.path.insert(0, os.path.join(REPO, "tools"))
try:
    import link as linker  # noqa: E402
except Exception:  # noqa: BLE001
    linker = None


# ───────────────────────── 元数据提取 ─────────────────────────
def read_version():
    try:
        with open(VERSION_FILE, encoding="utf-8") as f:
            return f.read().strip() or "?"
    except Exception:
        return "?"


def list_skill_dirs():
    out = []
    for name in sorted(os.listdir(REPO)):
        d = os.path.join(REPO, name)
        if os.path.isdir(d) and os.path.isfile(os.path.join(d, "SKILL.md")):
            out.append(name)
    return out


def parse_frontmatter(path):
    """极简 YAML frontmatter 解析: 仅取顶层 key: value。"""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return {}
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        k, v = line.split(":", 1)
        fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def parse_catalog():
    """解析 CATALOG.md 表格: folder -> {label, purpose}。"""
    table = {}
    try:
        with open(CATALOG, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except Exception:
        return table
    for ln in lines:
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip().strip("`") for c in ln.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0] in ("文件夹名称", ""):
            continue
        table[cells[0]] = {"label": cells[1], "purpose": cells[2]}
    return table


def load_sources():
    try:
        with open(SOURCES, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_sources(data):
    with open(SOURCES, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def git_last_updated(folder):
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%ci", "--", folder],
            cwd=REPO, capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()[:10]
    except Exception:
        pass
    p = os.path.join(REPO, folder, "SKILL.md")
    if os.path.exists(p):
        return datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d")
    return "—"


# 技能类别归纳(人工归纳, 未命中归入"其他")
# 注: trading-skills / gauss314-skills / InvestSkill / Ultimate-AI-Skill-Library
#     为多技能合集仓库(无根 SKILL.md), 不在本表逐行列出
CATEGORIES = {
    "前端设计": [
        "frontend-design", "brandkit", "design-system", "gpt-tasteskill",
        "soft-skill", "interface-design", "image-to-code-skill",
        "imagegen-frontend-mobile", "imagegen-frontend-web", "minimalist-skill",
        "redesign-skill", "taste-skill", "ui-styling", "ui-ux-pro-max", "impeccable",
    ],
    "投研·交易": [
        "a-stock-data", "serenity-skill",
    ],
    "内容·研究": [
        "Humanizer-zh", "last30days", "last30days-cn", "agent-reach",
    ],
    "工程·效率": [
        "find-skills", "gh-skill-installer", "output-skill",
        "yao-meta-skill", "grill-me", "dotnet-mod-recon",
    ],
    "游戏·攻略": [
        "wanxiang-build",
    ],
}
CAT_ORDER = list(CATEGORIES.keys()) + ["其他"]


def category_of(folder):
    for cat, folders in CATEGORIES.items():
        if folder in folders:
            return cat
    return "其他"


def build_skills():
    sources = {s["folder"]: s for s in load_sources()}
    catalog = parse_catalog()
    skills = []
    for folder in list_skill_dirs():
        fm = parse_frontmatter(os.path.join(REPO, folder, "SKILL.md"))
        cat = catalog.get(folder, {})
        name = fm.get("name") or cat.get("label") or folder
        purpose = cat.get("purpose") or fm.get("description") or "—"
        version = fm.get("version") or "—"
        src = sources.get(folder, {})
        skills.append({
            "folder": folder,
            "name": name,
            "purpose": purpose,
            "version": version,
            "last_updated": git_last_updated(folder),
            "repo": src.get("repo", "—"),
            "subpath": src.get("subpath", ""),
            "pinned": bool(src.get("pinned", False)),
            "category": category_of(folder),
            "risk": risk_scan(folder)[0],
        })
    return skills


# ───────────────────────── 新增 / 删除 ─────────────────────────
_UA = {"User-Agent": "skillsync-web", "Accept": "application/vnd.github+json"}


def _fetch_bytes(url, timeout=120):
    """下载 URL: 先走系统/环境代理, 失败则绕过代理直连重试(规避 Clash 等代理异常)。
    HTTP 4xx/5xx 属于明确拒绝, 不重试直接抛出。"""
    errs = []
    openers = (urllib.request.build_opener(),
               urllib.request.build_opener(urllib.request.ProxyHandler({})))
    for op in openers:
        try:
            req = urllib.request.Request(url, headers=_UA)
            with op.open(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError:
            raise
        except Exception as e:  # noqa: BLE001
            errs.append(str(e))
    raise RuntimeError("网络错误(系统代理与直连均失败): " + " | ".join(errs))


def sanitize_folder(name):
    s = re.sub(r"[^A-Za-z0-9._-]", "-", name.strip())
    return s.strip("-")


def _detect_skill_subdir(root, repo):
    """仓库根无 SKILL.md 时, 在一/两层子目录中找含 SKILL.md 的技能目录;
    多候选时优先与仓库名同名的那个, 仍不唯一则返回 None。"""
    cands = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth >= 2:
            dirnames[:] = []
        if rel != "." and "SKILL.md" in filenames:
            cands.append(rel.replace(os.sep, "/"))
    if not cands:
        return None
    if len(cands) == 1:
        return cands[0]
    name = repo.split("/")[-1].lower()
    for c in cands:
        if c.lower() == name or c.lower().endswith("/" + name):
            return c
    return None


def install_skill(folder, repo, subpath, pinned):
    """安装技能: 默认分支优先复用 skillsync 的 API(带 1h 缓存 + GITHUB_TOKEN);
    API 失败(如 403 限流)则按 main/master 直接下载 codeload tarball(不受 API 限流)。
    根目录无 SKILL.md 时自动探测技能子路径。安装成功后才写入 sources.json。"""
    folder = sanitize_folder(folder)
    if not folder:
        return False, "文件夹名无效"
    if "/" not in repo:
        return False, "来源仓库格式应为 owner/name"
    data = load_sources()
    if any(s["folder"] == folder for s in data):
        return False, f"技能目录 {folder} 已存在"

    # 1) 默认分支: 走带缓存的 API; 失败不阻塞, 稍后按常见分支猜
    branch = None
    note = ""
    try:
        import skillsync as ss
        info = ss.api_get(f"https://api.github.com/repos/{repo}")
        if isinstance(info, dict):
            branch = info.get("default_branch")
    except Exception as e:  # noqa: BLE001
        note = f"(GitHub API 暂不可用[{e}], 已绕过 API 直接下载)"

    # 2) 下载 tarball: 依次尝试 API 给出的分支与常见默认分支
    branches = [b for b in [branch, "main", "master"] if b]
    raw = None
    last = None
    for b in branches:
        try:
            raw = _fetch_bytes(
                f"https://codeload.github.com/{repo}/tar.gz/refs/heads/{b}")
            branch = b
            break
        except Exception as e:  # noqa: BLE001
            last = e
    if raw is None:
        return False, f"下载 tarball 失败({repo}): {last} {note}"

    tmp = tempfile.mkdtemp(prefix="skillinstall_")
    try:
        tgz = os.path.join(tmp, "repo.tgz")
        with open(tgz, "wb") as f:
            f.write(raw)
        ex = os.path.join(tmp, "ex")
        os.makedirs(ex)
        shutil.unpack_archive(tgz, ex)
        root = next(os.path.join(ex, d) for d in os.listdir(ex)
                    if os.path.isdir(os.path.join(ex, d)))
        sub = (subpath or "").strip().strip("/")
        src = os.path.join(root, *sub.split("/")) if sub else root
        detected = ""
        if not os.path.isfile(os.path.join(src, "SKILL.md")):
            if sub:
                return False, f"子路径 {sub} 下没有 SKILL.md, 请核对后重试"
            rel = _detect_skill_subdir(root, repo)
            if rel is None:
                return False, ("仓库根目录及两层子目录内未能唯一确定 SKILL.md 位置, "
                               "请在'子路径'中填写技能所在目录(如 skills/<name>)")
            sub = rel
            src = os.path.join(root, *rel.split("/"))
            detected = f", 子路径自动识别: {rel}"
        dest = os.path.join(REPO, folder)
        shutil.copytree(src, dest,
                        ignore=shutil.ignore_patterns(".git", ".gitignore", "node_modules"))
        if not os.path.isfile(os.path.join(dest, "SKILL.md")):
            shutil.rmtree(dest, ignore_errors=True)
            return False, "复制后未找到 SKILL.md, 已回滚"
        data.append({"folder": folder, "repo": repo,
                     "subpath": sub, "pinned": bool(pinned)})
        save_sources(data)
        subprocess.run(["git", "add", "-A", folder], cwd=REPO)
        level, hits = risk_scan(folder)
        warn = ""
        if level == "high":
            warn = (f"\n⚠ 安全扫描: 发现 {sum(1 for h in hits if h[0] == '高危')}"
                    f" 处高危模式, 安装前请审查该技能内容!")
        elif level == "warn":
            warn = f"\n安全扫描: {len(hits)} 处提示级匹配, 建议查看内容确认"
        return True, (f"已安装 {folder}(来自 {repo}{'/' + sub if sub else ''}){detected}, 待提交"
                      + (f" {note}" if note else "") + warn)
    except Exception as e:  # noqa: BLE001
        return False, f"安装失败: {e}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def delete_skill(folder):
    data = load_sources()
    new = [s for s in data if s["folder"] != folder]
    if len(new) != len(data):
        save_sources(new)
    dest = os.path.join(REPO, folder)
    if os.path.isdir(dest):
        r = subprocess.run(["git", "rm", "-r", "-f", "--", folder], cwd=REPO,
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            shutil.rmtree(dest, ignore_errors=True)
            subprocess.run(["git", "add", "-A", "--", folder], cwd=REPO)
    # 清理各工具侧指向该技能的悬挂链接
    if linker is not None:
        removed_links = 0
        try:
            for _name, tdir in linker.candidate_targets():
                lp = tdir / folder
                if (lp.is_symlink() or lp.exists()) and linker.resolve_into_repo(lp):
                    remove_link_safe(lp)
                    removed_links += 1
            if removed_links:
                print(f"[links] 已清理 {removed_links} 条工具侧悬挂链接")
        except Exception:
            pass
    return True, f"已删除 {folder}, 待提交/同步"


def remove_link_safe(p):
    if p.is_symlink():
        p.unlink()
    else:
        os.rmdir(p)


def run_cli(action):
    allowed = {"status": [], "update": [], "discover": [], "pull": [],
               "sync": [], "syncpush": ["--push"], "version": []}
    if action not in allowed:
        return "不允许的操作"
    # 强制子进程 UTF-8 输出: 中文 Windows 下管道默认 GBK, ⭐/✓ 会令子进程编码崩溃
    # GIT_TERMINAL_PROMPT=0: 推送无凭据时快速报错而非挂起等待输入
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
               GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="NEVER")
    try:
        r = subprocess.run([sys.executable, CLI, action.replace("syncpush", "sync"),
                            *allowed[action]], cwd=REPO,
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           timeout=600, env=env)
        out = ((r.stdout or "") + "\n" + (r.stderr or "")).strip()
        if r.returncode != 0:
            out += f"\n(退出码 {r.returncode})"
        return out or "(无输出)"
    except Exception as e:  # noqa: BLE001
        return f"[异常] {e}"


# ───────────────────────── 页面渲染 ─────────────────────────
PAGE_CSS = """
:root{--bg:#f6f4ef;--panel:#ffffff;--border:#e7e3d8;--text:#2f2e2b;--muted:#8b877c;
--green:#3f8f68;--blue:#4f7ca3;--warn:#a8823c;--danger:#bf5b52;--neutral:#efece3;
--groupbg:#f1eee6;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
font-family:'Segoe UI','Microsoft YaHei','PingFang SC',system-ui,sans-serif;font-size:14px;}
.wrap{max-width:1180px;margin:0 auto;padding:24px 20px 60px;}
header{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;
border-bottom:1px solid var(--border);padding-bottom:14px;margin-bottom:18px;}
header h1{font-size:20px;margin:0;font-weight:650;letter-spacing:.3px;}
header .sub{color:var(--muted);font-size:12.5px;}
.card{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:16px 18px;margin-bottom:18px;
box-shadow:0 1px 2px rgba(70,64,48,.04);}
.card h2{font-size:14px;margin:0 0 12px;color:var(--text);font-weight:600;}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px;}
button{font-family:inherit;font-size:13px;border:0;border-radius:7px;padding:8px 14px;
cursor:pointer;color:#fff;background:var(--blue);transition:filter .15s;}
button:hover{filter:brightness(1.06);}
button:disabled{opacity:.55;cursor:wait;filter:none;}
button.primary{background:var(--green);}
button.neutral{background:var(--neutral);color:var(--muted);border:1px solid var(--border);}
button.danger{background:transparent;color:var(--danger);border:1px solid var(--danger);padding:5px 12px;}
button.danger:hover{background:rgba(191,91,82,.08);}
button.armed{background:var(--danger) !important;color:#fff !important;border-color:var(--danger) !important;filter:none !important;}
table{width:100%;border-collapse:collapse;font-size:13px;}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--border);vertical-align:top;}
th{color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.4px;}
tbody tr:hover{background:#faf8f3;}
tr.group td{background:var(--groupbg);color:#7a766a;font-size:12px;font-weight:600;
letter-spacing:1.5px;padding:8px 12px;}
td .folder{font-family:Consolas,Menlo,monospace;color:var(--blue);font-size:12.5px;}
td.purpose{max-width:380px;color:#6f6c63;font-size:12.5px;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.badge{display:inline-block;font-size:11px;padding:2px 8px;border-radius:999px;
background:#f5efdf;color:var(--warn);border:1px solid #e5d8b8;}
.badge.risk-high{background:#f8e4e2;color:var(--danger);border-color:#eabab5;font-weight:600;}
.badge.risk-warn{background:#f5efdf;color:var(--warn);border-color:#e5d8b8;}
.modal{display:none;position:fixed;inset:0;background:rgba(40,36,30,.45);z-index:50;
align-items:center;justify-content:center;}
.modal.open{display:flex;}
.modal-box{background:var(--panel);border:1px solid var(--border);border-radius:10px;
width:min(880px,94vw);max-height:84vh;display:flex;flex-direction:column;overflow:hidden;
box-shadow:0 12px 40px rgba(50,45,35,.22);}
.modal-head{display:flex;justify-content:space-between;align-items:center;
padding:10px 14px;border-bottom:1px solid var(--border);font-weight:600;font-size:13px;}
.modal-body{margin:0;padding:14px 16px;overflow:auto;flex:1;
font-family:Consolas,Menlo,monospace;font-size:12px;white-space:pre-wrap;color:var(--text);
background:#fbfaf6;}
.muted{color:var(--muted);}
form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 16px;}
label{display:flex;flex-direction:column;gap:5px;font-size:12px;color:var(--muted);}
input[type=text]{background:#fbfaf6;border:1px solid var(--border);border-radius:7px;
padding:9px 11px;color:var(--text);font-size:13px;font-family:inherit;}
input[type=text]:focus{outline:none;border-color:var(--blue);}
.check{display:flex;align-items:center;gap:8px;color:var(--text);font-size:13px;}
.check input{width:16px;height:16px;accent-color:var(--green);}
.form-actions{grid-column:1/-1;display:flex;gap:10px;align-items:center;}
#result{background:#fbfaf6;border:1px solid var(--border);border-radius:8px;padding:14px;
font-family:Consolas,Menlo,monospace;font-size:12px;color:var(--text);white-space:pre-wrap;
max-height:300px;overflow:auto;min-height:60px;margin:12px 0;}
#result.err{color:var(--danger);}
.hint{color:var(--muted);font-size:12px;margin:-6px 0 10px;}
.notice{margin:0 0 12px;padding:9px 12px;border-radius:8px;font-size:12.5px;line-height:1.55;
border-left:4px solid var(--green);background:#f3f8f3;color:#2f5230;}
.notice.warn{border-left-color:var(--warn);background:#fbf3e0;color:#7a5a12;}
.notice.info{border-left-color:var(--blue);background:#eef4fb;color:#2a4a66;}
.notice.ok{border-left-color:var(--green);background:#f3f8f3;color:#2f5230;}
.disc-item{display:flex;gap:10px;align-items:center;padding:8px 0;border-bottom:1px solid var(--border);}
.disc-item:last-child{border-bottom:0;}
.disc-item .d-repo{font-family:Consolas,Menlo,monospace;color:var(--blue);font-size:12.5px;white-space:nowrap;}
.disc-item .d-stars{color:var(--warn);font-size:12px;white-space:nowrap;}
.disc-item .d-desc{color:#6f6c63;font-size:12.5px;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.disc-item button{padding:4px 10px;font-size:12px;flex:none;}
.empty{color:var(--muted);padding:20px;text-align:center;}
"""

PAGE_JS = r"""
function showErr(msg){
  const box = document.getElementById('result');
  box.classList.add('err');
  box.textContent = '[错误] ' + msg;
}
window.onerror = function(msg){ showErr(msg); };

async function post(url, payload){
  const r = await fetch(url, {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(payload)});
  return r.json();
}

async function act(action, btn){
  const box = document.getElementById('result');
  box.classList.remove('err');
  box.textContent = '运行中…';
  box.scrollIntoView({behavior:'smooth', block:'nearest'});
  if(btn){ btn.disabled = true; btn.dataset.old = btn.textContent; btn.textContent = '运行中…'; }
  try{
    const d = await post('/api/action', {action: action});
    box.textContent = (d && d.msg) ? d.msg : '(无输出)';
  }catch(e){
    showErr('请求失败: ' + e + ' —— 请确认服务窗口(skillsync_web.py)仍在运行');
  }finally{
    if(btn){ btn.disabled = false; btn.textContent = btn.dataset.old; }
    refreshBadge();
  }
}

async function refreshBadge(){
  try{
    const d = await fetch('/api/unpushed').then(r=>r.json());
    const b = document.getElementById('unpushedBadge');
    if(!b) return;
    if(d.count > 0){
      b.style.display = '';
      b.textContent = '⚠ 本地领先 ' + d.count + ' 个提交未推送';
    } else {
      b.style.display = 'none';
    }
  }catch(e){ /* 静默 */ }
}

document.querySelectorAll('[data-action]').forEach(b=>{
  b.addEventListener('click', ()=>act(b.dataset.action, b));
});

const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')
  .replace(/>/g,'&gt;').replace(/"/g,'&quot;');

function parseRepo(v){
  v = String(v||'').trim();
  if(!v) return '';
  v = v.replace(/^https?:\/\/(www\.)?github\.com\//i, '')
       .replace(/\.git$/i, '').replace(/\/+$/, '');
  const parts = v.split('/').filter(Boolean);
  return parts.length >= 2 ? parts[0] + '/' + parts[1] : '';
}

const fRepo = document.getElementById('f_repo');
const fFolder = document.getElementById('f_folder');
fFolder.dataset.auto = '1';
fRepo.addEventListener('input', ()=>{
  const r = parseRepo(fRepo.value);
  if(r && fFolder.dataset.auto === '1'){ fFolder.value = r.split('/')[1]; }
});
fFolder.addEventListener('input', ()=>{ fFolder.dataset.auto = '0'; });

async function doDiscover(btn){
  const box = document.getElementById('result');
  box.classList.remove('err');
  box.textContent = '正在搜索 GitHub 高星技能…';
  box.scrollIntoView({behavior:'smooth', block:'nearest'});
  btn.disabled = true; btn.dataset.old = btn.textContent; btn.textContent = '搜索中…';
  try{
    const d = await post('/api/discover', {});
    if(!d.ok){ showErr(d.msg); return; }
    const wrap = document.getElementById('discWrap');
    const list = document.getElementById('discList');
    wrap.style.display = '';
    if(!d.items.length){
      list.innerHTML = '<div class="muted" style="padding:8px 0">没有发现新的相关技能(可能都已安装)</div>';
    }else{
      list.innerHTML = d.items.map(it =>
        '<div class="disc-item">'
        + '<span class="d-repo">' + esc(it.repo) + '</span>'
        + '<span class="d-stars">⭐' + esc(it.stars) + '</span>'
        + '<span class="d-desc" title="' + esc(it.desc) + '">' + esc(it.desc) + '</span>'
        + '<button data-install="' + esc(it.repo) + '">安装</button>'
        + '</div>').join('');
      list.querySelectorAll('[data-install]').forEach(b=>{
        b.addEventListener('click', ()=>installRepo(b.dataset.install, b));
      });
    }
    box.textContent = '发现 ' + d.items.length + ' 个候选技能(已过滤非技能仓库与已安装项)';
  }catch(e){
    showErr('请求失败: ' + e);
  }finally{
    btn.disabled = false; btn.textContent = btn.dataset.old;
  }
}

async function installRepo(repo, btn){
  btn.disabled = true; btn.textContent = '安装中…';
  try{
    const d = await post('/api/add', {folder: repo.split('/')[1], repo: repo,
                                      subpath: '', pinned: false});
    if(d.ok){ location.reload(); }
    else { btn.disabled = false; btn.textContent = '安装'; showErr(d.msg); }
  }catch(e){
    btn.disabled = false; btn.textContent = '安装'; showErr(e);
  }
}

document.getElementById('discBtn').addEventListener('click', e=>doDiscover(e.currentTarget));

/* ───── 连接 Coding 工具 ───── */
async function loadLinks(){
  try{
    const d = await post('/api/links/status', {});
    if(!d.ok){ return; }
    const rows = d.tools.map(t =>
      '<tr>'
      + '<td><span class="folder">' + esc(t.name) + '</span></td>'
      + '<td class="purpose" title="' + esc(t.path) + '">' + esc(t.path) + '</td>'
      + '<td>' + (t.linked ? '<span style="color:var(--green);font-weight:600">' + t.linked + '</span>'
                           : '<span class="muted">0</span>') + '</td>'
      + '<td>' + (t.collide ? t.collide : '<span class="muted">0</span>') + '</td>'
      + '<td>' + t.total + '</td>'
      + '</tr>').join('');
    document.getElementById('linkRows').innerHTML = rows;
    const nb = document.getElementById('linkNotice');
    if(d.needs_relink){
      const sample = d.new_skills.slice(0,3).map(esc).join('、');
      const more = d.new_skills.length > 3 ? ' 等 ' + d.new_skills.length + ' 个' : '';
      nb.className = 'notice warn';
      nb.style.display = '';
      nb.innerHTML = '⚠ 检测到 ' + d.new_skills.length + ' 个新增技能（如 ' + sample + more + '），工具侧尚未生效。点「一键连接全部」即可同步（幂等，不影响已有链接）。';
    } else if(d.removed_skills && d.removed_skills.length){
      const sample = d.removed_skills.slice(0,3).map(esc).join('、');
      const more = d.removed_skills.length > 3 ? ' 等 ' + d.removed_skills.length + ' 个' : '';
      nb.className = 'notice info';
      nb.style.display = '';
      nb.innerHTML = 'ℹ 已删除 ' + d.removed_skills.length + ' 个技能（如 ' + sample + more + '）。工具侧悬挂链接会在下次连接或撤销时自动清理，无需重连。';
    } else if(d.baseline_exists){
      nb.className = 'notice ok';
      nb.style.display = '';
      nb.innerHTML = '✓ 链接已是最新，无需重新连接';
    } else {
      nb.style.display = 'none';
    }
  }catch(e){ /* 静默: 状态加载失败不影响其他功能 */ }
}

async function linksAct(url, btn){
  const box = document.getElementById('result');
  box.classList.remove('err');
  box.textContent = '运行中…';
  box.scrollIntoView({behavior:'smooth', block:'nearest'});
  btn.disabled = true; btn.dataset.old = btn.textContent; btn.textContent = '运行中…';
  try{
    const d = await post(url, {});
    box.textContent = d.msg || '(完成)';
    await loadLinks();
  }catch(e){
    showErr('请求失败: ' + e);
  }finally{
    btn.disabled = false; btn.textContent = btn.dataset.old;
  }
}

document.getElementById('lkConnect').addEventListener('click',
  e=>linksAct('/api/links/connect', e.currentTarget));

let lkRemoveArmed = false, lkRemoveTimer = null;
document.getElementById('lkRemove').addEventListener('click', e=>{
  const btn = e.currentTarget;
  if(!lkRemoveArmed){
    lkRemoveArmed = true;
    btn.dataset.old = btn.textContent;
    btn.textContent = '确认撤销?';
    btn.classList.add('armed');
    lkRemoveTimer = setTimeout(()=>{ lkRemoveArmed = false;
      btn.textContent = btn.dataset.old; btn.classList.remove('armed'); }, 4000);
    return;
  }
  clearTimeout(lkRemoveTimer);
  lkRemoveArmed = false; btn.classList.remove('armed');
  linksAct('/api/links/remove', btn);
});

document.getElementById('lkCopy').addEventListener('click', async e=>{
  const btn = e.currentTarget;
  try{
    const d = await post('/api/links/prompt', {});
    await navigator.clipboard.writeText(d.msg);
    btn.textContent = '已复制 ✓';
    setTimeout(()=>{ btn.textContent = '复制自连接提示词'; }, 2000);
  }catch(err){
    showErr('复制失败(可手动选择文本复制): ' + err);
  }
});

document.getElementById('lkRefresh').addEventListener('click', ()=>loadLinks());
loadLinks();

/* ───── 表格搜索过滤 ───── */
const qBox = document.getElementById('q');
qBox.addEventListener('input', ()=>{
  const kw = qBox.value.trim().toLowerCase();
  const tb = document.getElementById('skillsTable').tBodies[0];
  const rows = [...tb.rows];
  // 分段: 每个组头 + 其后到下一组头之前的数据行
  const segs = [];
  let cur = null;
  for(let i = 0; i < rows.length; i++){
    if(rows[i].className === 'group'){
      if(cur) segs.push(cur);
      cur = {g: i, from: i + 1, to: i};
    } else if(cur){
      cur.to = i;
    }
  }
  if(cur) segs.push(cur);
  for(const seg of segs){
    let any = kw === '';
    for(let i = seg.from; i <= seg.to; i++){
      const hit = kw === '' || rows[i].textContent.toLowerCase().includes(kw);
      rows[i].style.display = hit ? '' : 'none';
      if(hit) any = true;
    }
    rows[seg.g].style.display = any ? '' : 'none';
  }
});

/* ───── 技能查看器 ───── */
document.querySelectorAll('.view').forEach(b=>{
  b.addEventListener('click', async ()=>{
    const f = b.dataset.folder;
    try{
      const d = await fetch('/api/skill?folder=' + encodeURIComponent(f))
        .then(r=>r.json());
      if(!d.ok){ showErr(d.msg || '读取失败'); return; }
      document.getElementById('mTitle').textContent = f + ' / SKILL.md';
      document.getElementById('mBody').textContent = d.content;
      document.getElementById('modal').classList.add('open');
    }catch(e){ showErr('读取失败: ' + e); }
  });
});
document.getElementById('mClose').addEventListener('click',
  ()=>document.getElementById('modal').classList.remove('open'));
document.getElementById('modal').addEventListener('click',
  e=>{ if(e.target.id === 'modal') e.currentTarget.classList.remove('open'); });

/* ───── 回收站 ───── */
async function loadBin(){
  try{
    const d = await post('/api/deleted', {});
    const el = document.getElementById('binList');
    if(!d.ok){ el.innerHTML = '<span class="muted">' + esc(d.msg || '加载失败') + '</span>'; return; }
    if(!d.items.length){
      el.innerHTML = '<span class="muted">没有可恢复的删除记录</span>';
      return;
    }
    el.innerHTML = d.items.map(it =>
      '<div class="disc-item">'
      + '<span class="d-repo">' + esc(it.folder) + '</span>'
      + '<span class="d-desc">' + esc(it.when) + ' · ' + esc(it.msg) + '</span>'
      + '<button data-restore="' + esc(it.folder) + '">恢复</button>'
      + '</div>').join('');
    el.querySelectorAll('[data-restore]').forEach(b=>{
      b.addEventListener('click', async ()=>{
        b.disabled = true; b.textContent = '恢复中…';
        try{
          const r = await post('/api/restore', {folder: b.dataset.restore});
          if(r.ok){ location.reload(); }
          else { b.disabled = false; b.textContent = '恢复'; showErr(r.msg); }
        }catch(e){ b.disabled = false; b.textContent = '恢复'; showErr(e); }
      });
    });
  }catch(e){ /* 静默 */ }
}
loadBin();

document.querySelectorAll('.del').forEach(b=>{
  let armed = false, timer = null;
  b.addEventListener('click', async ()=>{
    const f = b.dataset.folder;
    if(!armed){
      armed = true;
      b.dataset.old = b.textContent;
      b.textContent = '确认删除?';
      b.classList.add('armed');
      timer = setTimeout(()=>{ armed = false; b.textContent = b.dataset.old; b.classList.remove('armed'); }, 4000);
      return;
    }
    clearTimeout(timer);
    b.disabled = true; b.textContent = '删除中…';
    try{
      await post('/api/delete', {folder: f});
      location.reload();
    }catch(e){
      b.disabled = false; b.textContent = b.dataset.old; b.classList.remove('armed'); showErr(e);
    }
  });
});

document.getElementById('addForm').addEventListener('submit', async e=>{
  e.preventDefault();
  const repo = parseRepo(fRepo.value);
  if(!repo){ showErr('来源仓库请填写 GitHub 链接或 owner/name'); return; }
  const p = {
    folder:  fFolder.value.trim() || repo.split('/')[1],
    repo:    repo,
    subpath: document.getElementById('f_sub').value.trim(),
    pinned:  document.getElementById('f_pin').checked
  };
  const btn = document.getElementById('addBtn');
  btn.disabled = true; btn.dataset.old = btn.textContent; btn.textContent = '安装中…';
  try{
    const d = await post('/api/add', p);
    if(d.ok){ location.reload(); }
    else { btn.disabled = false; btn.textContent = btn.dataset.old; showErr(d.msg); }
  }catch(err){
    btn.disabled = false; btn.textContent = btn.dataset.old; showErr(err);
  }
});
"""

PAGE_HTML = """<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI-SKILLS 技能管理</title>
<style>__CSS__</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>AI-SKILLS 技能管理</h1>
    <span class="sub">仓库: __REPO__ · 版本 __VERSION__ · 服务启动于 __START__ · __UNPUSHED__零依赖 Web 仪表盘(所有机器可用)</span>
  </header>

  <div class="card">
    <h2>安装新技能</h2>
    <form id="addForm">
      <label>来源仓库(粘贴 GitHub 链接或 owner/name)<input type="text" id="f_repo" placeholder="https://github.com/Cjy-CN/wanxiang-build"></label>
      <label>文件夹名(粘贴后自动填, 可改)<input type="text" id="f_folder" placeholder="自动生成"></label>
      <label>子路径(留空 = 自动识别)<input type="text" id="f_sub" placeholder="如 skills/<name>"></label>
      <label class="check"><input type="checkbox" id="f_pin"> 固定(pinned, 跳过自动更新)</label>
      <div class="form-actions">
        <button class="primary" type="submit" id="addBtn">安装并登记</button>
        <span class="muted">自动下载 tarball、识别技能子路径并登记到 config/sources.json</span>
      </div>
    </form>
    <div id="discWrap" style="display:none">
      <h2 style="margin-top:18px">发现的高星技能(点「安装」直接入库)</h2>
      <div id="discList"></div>
    </div>
  </div>

  <div class="card">
    <h2>技能总览(__COUNT__ 个)</h2>
    <div class="toolbar">
      <button data-action="status" title="列出各技能本地基线 / 上游最新 / 是否需要更新">状态</button>
      <button class="primary" data-action="update" title="把有上游更新的技能更新到本地并提交">检查更新</button>
      <button id="discBtn" title="搜索 GitHub 高星相关技能, 在列表内可直接安装">发现新技能</button>
      <button data-action="syncpush" title="一键同步: 把改动提交到本地 git 历史并推送到 GitHub">同步到 GitHub</button>
      <button data-action="pull" title="从 GitHub 拉取远端更新(仅快进合并, 有分叉会明确提示)">从 GitHub 拉取</button>
      <button class="neutral" data-action="version" title="显示当前版本号与最近更新内容">版本</button>
      <input type="text" id="q" placeholder="🔍 搜索技能名 / 作用…" style="margin-left:auto;width:220px;background:#fbfaf6;border:1px solid var(--border);border-radius:7px;padding:7px 11px;color:var(--text);font-size:13px;font-family:inherit;">
    </div>
    <div class="hint">同步到 GitHub = 提交改动并推送远端(你说推才由你点) · 从 GitHub 拉取 = 其他机器推送后在此拉取(仅快进) · 风险列 = 安装时对技能内容的自动安全扫描结果</div>
    <div id="result">点击上方按钮, 输出会显示在这里。</div>
    <table id="skillsTable">
      <thead><tr>
        <th>目录</th><th>名称</th><th>作用</th><th>版本</th>
        <th>最后更新</th><th>来源仓库</th><th>固定</th><th>风险</th><th>操作</th>
      </tr></thead>
      <tbody>__ROWS__</tbody>
    </table>
  </div>

  <div class="card">
    <h2>连接 Coding 工具</h2>
    <div class="toolbar">
      <button class="primary" id="lkConnect" title="为下方所有工具的 skills 目录建立指向技能库的链接(幂等)">一键连接全部</button>
      <button class="danger" id="lkRemove" title="撤销所有指向技能库的链接(不碰工具真实目录)">撤销全部链接</button>
      <button class="neutral" id="lkCopy" title="复制提示词, 可粘贴给任何 coding 工具让它自己连接">复制自连接提示词</button>
      <button class="neutral" id="lkRefresh">刷新状态</button>
    </div>
    <div class="hint">连接 = 在工具侧创建指向技能库的目录链接(仓库零写入) · 工具重启后生效 · 新增/删除技能后点一次「一键连接全部」即可</div>
    <div id="linkNotice" class="notice" style="display:none"></div>
    <table>
      <thead><tr><th>工具</th><th>skills 目录</th><th>已连接</th><th>同名占用</th><th>总项</th></tr></thead>
      <tbody id="linkRows"><tr><td colspan="5" class="empty">加载中…</td></tr></tbody>
    </table>
  </div>

  <div class="card">
    <h2>回收站（git 历史中已删除的技能）</h2>
    <div class="hint">恢复 = 从 git 历史把整个目录捞回(删除前版本) · 从未提交过的技能无法恢复 · 删除新技能前建议先「同步到 GitHub」</div>
    <div id="binList"><span class="muted">加载中…</span></div>
  </div>
</div>

<div class="modal" id="modal">
  <div class="modal-box">
    <div class="modal-head"><span id="mTitle">SKILL.md</span>
      <button class="neutral" id="mClose">关闭</button></div>
    <pre class="modal-body" id="mBody"></pre>
  </div>
</div>
<script>__JS__</script>
</body>
</html>"""


def render_rows(skills):
    if not skills:
        return '<tr><td colspan="9" class="empty">未找到含 SKILL.md 的技能目录</td></tr>'
    rows = []
    for cat in CAT_ORDER:
        group = [s for s in skills if s["category"] == cat]
        if not group:
            continue
        rows.append(f'<tr class="group"><td colspan="9">{html.escape(cat)} · {len(group)} 个</td></tr>')
        for s in sorted(group, key=lambda x: x["folder"].lower()):
            pin = '<span class="badge">已固定</span>' if s["pinned"] else '<span class="muted">—</span>'
            risk = {"high": '<span class="badge risk-high">高危</span>',
                    "warn": '<span class="badge risk-warn">注意</span>'}.get(
                        s.get("risk", "clean"), '<span class="muted">✓</span>')
            rows.append(
                "<tr>"
                f'<td><span class="folder">{html.escape(s["folder"])}</span></td>'
                f'<td>{html.escape(s["name"])}</td>'
                f'<td class="purpose" title="{html.escape(s["purpose"], quote=True)}">{html.escape(s["purpose"])}</td>'
                f'<td>{html.escape(s["version"])}</td>'
                f'<td>{html.escape(s["last_updated"])}</td>'
                f'<td><span class="folder">{html.escape(s["repo"])}</span></td>'
                f"<td>{pin}</td>"
                f"<td>{risk}</td>"
                f'<td><button class="neutral view" data-folder="{html.escape(s["folder"])}">查看</button> '
                f'<button class="danger del" data-folder="{html.escape(s["folder"])}">删除</button></td>'
                "</tr>"
            )
    return "\n".join(rows)


def render_page():
    skills = build_skills()
    n = unpushed_count()
    disp = "" if n > 0 else "none"
    unpushed_html = (f'<span class="badge risk-high" id="unpushedBadge" '
                     f'style="display:{disp}">⚠ 本地领先 {n} 个提交未推送</span> ')
    return (PAGE_HTML
            .replace("__CSS__", PAGE_CSS)
            .replace("__JS__", PAGE_JS)
            .replace("__ROWS__", render_rows(skills))
            .replace("__REPO__", html.escape(REPO))
            .replace("__VERSION__", html.escape(read_version()))
            .replace("__START__", html.escape(START_TS))
            .replace("__UNPUSHED__", unpushed_html)
            .replace("__COUNT__", str(len(skills))))


def version_report():
    """版本号 + 最近两节更新说明(取自 CHANGELOG.md)。"""
    head = read_version()
    try:
        with open(os.path.join(REPO, "CHANGELOG.md"), encoding="utf-8") as f:
            text = f.read()
        sections = re.findall(r"(?ms)^## \[.*?(?=^## \[|\Z)", text)
        recent = "\n\n".join(s.strip() for s in sections[:2])
        if len(recent) > 2400:
            recent = recent[:2400] + "\n…(完整内容见 CHANGELOG.md)"
    except Exception as e:  # noqa: BLE001
        recent = f"(CHANGELOG 读取失败: {e})"
    return f"当前版本 {head}\n\n{recent}"


def discover_candidates(top=15, min_stars=50):
    """结构化发现: 复用 skillsync 的 topic 搜索/兴趣匹配/SKILL.md 校验。
    全部 topic 都失败(如限流)时抛 RuntimeError, 由前端给出明确提示。"""
    import skillsync as ss
    existing_repos = {s["repo"].lower() for s in load_sources()}
    existing_folders = set(list_skill_dirs())
    seen = set()
    cands = []
    errors = 0
    for t in ss.DISCOVER_TOPICS:
        try:
            data = ss.api_get(
                f"https://api.github.com/search/repositories"
                f"?q=topic:{t}+stars:%3E{min_stars}&sort=stars&order=desc&per_page=30")
        except Exception:
            errors += 1
            continue
        for it in data.get("items", []):
            full = it["full_name"]
            if full in seen or full.lower() in existing_repos:
                continue
            nm = it["name"].lower()
            if nm in ("claude-code", "cursor", "claude", "codex"):
                continue
            if nm in existing_folders:
                continue
            seen.add(full)
            hay = f"{full} {it.get('description') or ''}".lower()
            if ss.matches_interests(hay):
                cands.append({"repo": full, "stars": it["stargazers_count"],
                              "desc": it.get("description") or "",
                              "url": it["html_url"]})
    if errors == len(ss.DISCOVER_TOPICS):
        raise RuntimeError("GitHub API 不可用(可能已限流 403): 请稍后再试, "
                           "或在 skillsync-web.bat 中取消 GITHUB_TOKEN 注释并填入 PAT")
    cands.sort(key=lambda c: -c["stars"])
    out = []
    for c in cands[:max(top * 2, 20)]:
        try:
            ok = ss.repo_has_skill_md(c["repo"], c["desc"])
        except Exception:
            ok = True
        if ok:
            out.append(c)
        if len(out) >= top:
            break
    return out


def links_status():
    """连接矩阵: 各工具 skills 目录中 指向本仓库的链接数。"""
    if linker is None:
        raise RuntimeError("连接器加载失败(tools/link.py)")
    tools = []
    total = 0
    names = {s.name for s in linker.skill_dirs()}
    st = linker.load_state()
    baseline = st.get("linked_skills")
    if baseline is None:
        new_skills, removed_skills, needs_relink = [], [], False
    else:
        new_skills = sorted(names - set(baseline))
        removed_skills = sorted(set(baseline) - names)
        needs_relink = bool(new_skills)
    for name, tdir in linker.candidate_targets():
        linked = collide = titems = 0
        if tdir.is_dir():
            for p in tdir.iterdir():
                titems += 1
                if p.name in names:
                    if linker.resolve_into_repo(p):
                        linked += 1
                    else:
                        collide += 1
        total += linked
        tools.append({"name": name, "path": str(tdir), "linked": linked,
                      "collide": collide, "total": titems})
    tools.sort(key=lambda t: t["name"].lower())
    return {"ok": True, "tools": tools, "total": total,
            "new_skills": new_skills, "removed_skills": removed_skills,
            "needs_relink": needs_relink, "baseline_exists": baseline is not None}


def _capture(fn, *a, **kw):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*a, **kw)
    return buf.getvalue().strip()


# ───────────────── 安全扫描(安装审查) ─────────────────
RISK_EXTS = {".md", ".txt", ".py", ".js", ".ts", ".sh", ".ps1", ".bat",
             ".cmd", ".yaml", ".yml", ".json", ".zsh", ".toml"}
RISK_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".workbuddy", ".venv"}
RISK_HARD = [
    ("管道执行远程脚本", r"(curl|wget|iwr|invoke-webrequest|invoke-restmethod)[^;\n]{0,100}\|\s*(sudo\s+)?(sh|bash|zsh|pwsh|powershell)\b"),
    ("删除/格式化系统盘", r"(rm\s+-rf\s+/\s|format\s+[cC]:|diskpart|reg\s+delete\s+hk|remove-item\s+[^;\n]{0,60}-force[^;\n]{0,40}-recurse\s+c:\\\\)"),
    ("读取凭据/密钥文件", r"(\.ssh/id_rsa|\.ssh/id_ed25519|\.aws[/\\]credentials|\.netrc|\.git-credentials|ls -(la )?~/?\.ssh)"),
    ("窃取环境变量并外发", r"(printenv|export -p|env)\b[^;\n]{0,60}\|\s*.{0,40}(curl|wget|http)|process\.env[^;\n]{0,80}(fetch\(|axios|XMLHttpRequest|上传|发送)"),
]
RISK_SOFT = [
    ("诱导忽略既有指令", r"(ignore|disregard|bypass|override)[^\n]{0,30}(previous|prior|above|earlier|system)\s+(instructions?|prompts?|rules?)|忽略(之前|以上|先前|系统)(的)?(指令|提示|规则)"),
    ("诱导外发数据", r"(exfiltrat|上传到|发送到|上报到|post to)[^\n]{0,60}https?://"),
    ("诱导下载并执行", r"(下载|download)[^\n]{0,50}(并)?(执行|运行|run|execute)|curl[^\n]{0,60}(-o\s+\S+\s+\|\||\|\|\s*sh)"),
    ("超长Base64块", r"[A-Za-z0-9+/=]{600,}"),
]
_RISK_CACHE = {}


def risk_scan(folder):
    """轻量安装审查: 扫描技能目录文本文件的可疑模式。返回 (level, hits)。
    level: high(发现高危) / warn(仅提示级) / clean。带缓存(按 SKILL.md mtime)。"""
    sk = os.path.join(REPO, folder, "SKILL.md")
    key = folder
    try:
        mtime = os.path.getmtime(sk)
    except OSError:
        mtime = 0
    cached = _RISK_CACHE.get(key)
    if cached and cached[0] == mtime:
        return cached[1], cached[2]
    hits = []
    base = os.path.join(REPO, folder)
    scanned = 0
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in RISK_SKIP_DIRS]
        for fn in filenames:
            if scanned >= 300:
                break
            if os.path.splitext(fn)[1].lower() not in RISK_EXTS:
                continue
            fp = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(fp) > 200_000:
                    continue
                with open(fp, encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        low = line.lower()
                        for pname, pat in RISK_HARD:
                            if re.search(pat, low):
                                hits.append(("高危", pname,
                                             os.path.relpath(fp, base).replace("\\", "/"), i,
                                             line.strip()[:120]))
                        for pname, pat in RISK_SOFT:
                            if re.search(pat, low):
                                hits.append(("提示", pname,
                                             os.path.relpath(fp, base).replace("\\", "/"), i,
                                             line.strip()[:120]))
                scanned += 1
            except OSError:
                continue
    level = "high" if any(h[0] == "高危" for h in hits) else ("warn" if hits else "clean")
    hits.sort(key=lambda h: 0 if h[0] == "高危" else 1)
    hits = hits[:12]
    _RISK_CACHE[key] = (mtime, level, hits)
    return level, hits


def unpushed_count():
    """本地领先 origin/main 的提交数(拿不到则 0)。"""
    try:
        r = subprocess.run(["git", "rev-list", "--count", "origin/main..HEAD"],
                           cwd=REPO, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode == 0:
            return int((r.stdout or "0").strip() or "0")
    except Exception:
        pass
    return 0


def deleted_skills():
    """git 历史中删除过、且当前磁盘上已不存在的顶层技能目录。"""
    r = subprocess.run(
        ["git", "log", "--diff-filter=D", "--name-status",
         "--pretty=format:@@%H|%ad|%s", "--date=short"],
        cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = {}
    cur = None
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("@@"):
            parts = line[2:].split("|", 2)
            if len(parts) == 3:
                cur = parts
        elif cur and (line.startswith("D\t") or line.startswith("D ")):
            # 文件级删除聚合到顶层目录/文件(整目录删除时 git 也可能直接记目录)
            p = line.split("\t", 1)[-1].strip().strip('"')
            top = p.replace("\\", "/").split("/")[0]
            if top not in out and not os.path.isdir(os.path.join(REPO, top)):
                out[top] = {"folder": top, "when": cur[1], "msg": cur[2],
                            "commit": cur[0]}
    return sorted(out.values(), key=lambda v: v["when"], reverse=True)


def restore_skill(folder):
    """从 git 历史恢复整目录(取删除提交的父版本)。"""
    if not re.fullmatch(r"[A-Za-z0-9._-]+", folder or ""):
        return False, "非法目录名"
    r = subprocess.run(["git", "log", "--diff-filter=D", "--format=%H", "-n", "1", "--", folder],
                       cwd=REPO, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    cid = (r.stdout or "").strip()
    if not cid:
        return False, "git 历史中没有该技能的删除记录(可能从未提交过, 无法恢复)"
    r2 = subprocess.run(["git", "checkout", cid + "^", "--", folder], cwd=REPO,
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r2.returncode != 0:
        return False, "恢复失败: " + ((r2.stderr or "").strip()[:200] or "未知错误")
    return True, f"已从历史恢复 {folder}(删除前版本), 待提交/同步"


# ───────────────────────── HTTP 服务 ─────────────────────────
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/favicon.ico":
            self._send(204, b"")
            return
        if path == "/api/unpushed":
            self._send(200, json.dumps({"ok": True, "count": unpushed_count()},
                                       ensure_ascii=False),
                       "application/json; charset=utf-8")
            return
        if path == "/api/skill":
            qs = urlparse(self.path).query
            folder = (urllib.parse.parse_qs(qs).get("folder") or [""])[0]
            if folder not in list_skill_dirs():
                self._send(404, json.dumps({"ok": False, "msg": "技能不存在"},
                                           ensure_ascii=False),
                           "application/json; charset=utf-8")
                return
            fp = os.path.join(REPO, folder, "SKILL.md")
            try:
                with open(fp, encoding="utf-8", errors="replace") as f:
                    content = f.read(80_000)
                if len(content) == 80_000:
                    content += "\n…(过长截断)"
                self._send(200, json.dumps(
                    {"ok": True, "folder": folder, "content": content},
                    ensure_ascii=False), "application/json; charset=utf-8")
            except Exception as e:  # noqa: BLE001
                self._send(200, json.dumps({"ok": False, "msg": str(e)},
                                           ensure_ascii=False),
                           "application/json; charset=utf-8")
            return
        if path in ("/", "/index.html"):
            self._send(200, render_page())
        elif path == "/api/skills":
            self._send(200, json.dumps(build_skills(), ensure_ascii=False),
                       "application/json; charset=utf-8")
        else:
            self._send(404, "Not found")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            data = json.loads(raw)
        except Exception:
            data = {}
        path = urlparse(self.path).path
        if path == "/api/add":
            ok, msg = install_skill(data.get("folder", ""), data.get("repo", ""),
                                    data.get("subpath", ""), data.get("pinned", False))
            self._send(200, json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False),
                       "application/json; charset=utf-8")
        elif path == "/api/delete":
            ok, msg = delete_skill(data.get("folder", ""))
            self._send(200, json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False),
                       "application/json; charset=utf-8")
        elif path == "/api/action":
            a = data.get("action", "")
            msg = version_report() if a == "version" else run_cli(a)
            self._send(200, json.dumps({"ok": True, "msg": msg},
                                       ensure_ascii=False),
                       "application/json; charset=utf-8")
        elif path == "/api/discover":
            try:
                payload = {"ok": True, "items": discover_candidates()}
            except Exception as e:  # noqa: BLE001
                payload = {"ok": False, "msg": str(e)}
            self._send(200, json.dumps(payload, ensure_ascii=False),
                       "application/json; charset=utf-8")
        elif path == "/api/links/status":
            try:
                payload = links_status()
            except Exception as e:  # noqa: BLE001
                payload = {"ok": False, "msg": str(e), "tools": [], "total": 0}
            self._send(200, json.dumps(payload, ensure_ascii=False),
                       "application/json; charset=utf-8")
        elif path == "/api/links/connect":
            try:
                ok, _, collide, fail = linker.link_all(
                    linker.candidate_targets(), linker.skill_dirs())
                self._send(200, json.dumps(
                    {"ok": True,
                     "msg": f"完成: 连接 {ok} · 同名跳过 {collide} · 失败 {fail}"},
                    ensure_ascii=False), "application/json; charset=utf-8")
            except Exception as e:  # noqa: BLE001
                self._send(200, json.dumps({"ok": False, "msg": f"连接失败: {e}"},
                                           ensure_ascii=False),
                           "application/json; charset=utf-8")
        elif path == "/api/links/remove":
            try:
                msg = _capture(linker.cmd_remove) or "(没有可撤销的链接)"
                self._send(200, json.dumps({"ok": True, "msg": msg},
                                           ensure_ascii=False),
                           "application/json; charset=utf-8")
            except Exception as e:  # noqa: BLE001
                self._send(200, json.dumps({"ok": False, "msg": f"撤销失败: {e}"},
                                           ensure_ascii=False),
                           "application/json; charset=utf-8")
        elif path == "/api/links/prompt":
            try:
                msg = _capture(linker.cmd_prompt)
                self._send(200, json.dumps({"ok": True, "msg": msg},
                                           ensure_ascii=False),
                           "application/json; charset=utf-8")
            except Exception as e:  # noqa: BLE001
                self._send(200, json.dumps({"ok": False, "msg": str(e)},
                                           ensure_ascii=False),
                           "application/json; charset=utf-8")
        elif path == "/api/deleted":
            try:
                self._send(200, json.dumps({"ok": True, "items": deleted_skills()},
                                           ensure_ascii=False),
                           "application/json; charset=utf-8")
            except Exception as e:  # noqa: BLE001
                self._send(200, json.dumps({"ok": False, "msg": str(e), "items": []},
                                           ensure_ascii=False),
                           "application/json; charset=utf-8")
        elif path == "/api/restore":
            ok, msg = restore_skill(data.get("folder", ""))
            self._send(200, json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False),
                       "application/json; charset=utf-8")
        else:
            self._send(404, json.dumps({"ok": False, "msg": "unknown"}, ensure_ascii=False),
                       "application/json; charset=utf-8")

    def log_message(self, *a):
        pass


def main():
    import argparse
    ap = argparse.ArgumentParser(description="AI-SKILLS Web 仪表盘")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8766)
    args = ap.parse_args()
    try:
        srv = HTTPServer((args.host, args.port), Handler)
    except OSError as e:
        print(f"[!] 端口 {args.port} 已被占用: {e}")
        print("    很可能有旧的 skillsync_web 实例仍在运行(内存里是旧代码)。")
        print("    请关闭旧的仪表盘窗口后重试, 或换端口: python skillsync_web.py --port %d" % (args.port + 1))
        try:
            input("按回车键退出...")
        except (EOFError, KeyboardInterrupt):
            pass
        sys.exit(1)
    print(f"AI-SKILLS 仪表盘已启动: http://{args.host}:{args.port}  (Ctrl+C 退出)")
    print(f"(本服务进程启动于 {START_TS}; 页面顶部显示的启动时间即当前进程, 可用于确认非旧实例)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        srv.shutdown()


if __name__ == "__main__":
    main()
