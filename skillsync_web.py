# -*- coding: utf-8 -*-
"""AI-SKILLS 技能管理 Web 仪表盘 —— 零依赖(stdlib only)。

所有机器可直接使用: 仅需 Python 3.11+ 与 git, 无需 tkinter / 无需 pip 安装。
运行:
    python skillsync_web.py [--port 8765] [--host 127.0.0.1]
然后浏览器打开 http://localhost:8765

功能:
    - 表格展示所有技能: 名称 / 作用 / 版本号 / 最后更新 / 来源仓库 / 固定 / 操作
    - 新增技能: 填仓库与子路径, 自动克隆安装并登记到 config/sources.json
    - 删除技能: 从仓库移除并提交删除(需另行同步)
    - 一键: 状态 / 检查更新 / 发现新技能 / 提交本地 / 推送远端
"""
import os
import re
import sys
import json
import shutil
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
        })
    return skills


# ───────────────────────── 新增 / 删除 ─────────────────────────
def sanitize_folder(name):
    s = re.sub(r"[^A-Za-z0-9._-]", "-", name.strip())
    return s.strip("-")


def install_skill(folder, repo, subpath, pinned):
    """安装技能: GitHub API 取默认分支 -> codeload tarball -> 解压复制 subpath。
    与 skillsync update 同一机制(纯 urllib, 免 git clone, 规避代理/schannel 问题)。
    安装成功后才写入 sources.json。"""
    folder = sanitize_folder(folder)
    if not folder:
        return False, "文件夹名无效"
    if "/" not in repo:
        return False, "来源仓库格式应为 owner/name"
    data = load_sources()
    if any(s["folder"] == folder for s in data):
        return False, f"技能目录 {folder} 已存在"
    try:
        with urllib.request.urlopen(f"https://api.github.com/repos/{repo}", timeout=30) as r:
            branch = json.load(r).get("default_branch", "main")
    except Exception as e:  # noqa: BLE001
        return False, f"无法访问仓库 {repo}: {e}"
    tmp = tempfile.mkdtemp(prefix="skillinstall_")
    try:
        tgz = os.path.join(tmp, "repo.tgz")
        urllib.request.urlretrieve(
            f"https://codeload.github.com/{repo}/tar.gz/refs/heads/{branch}", tgz)
        ex = os.path.join(tmp, "ex")
        os.makedirs(ex)
        shutil.unpack_archive(tgz, ex)
        top = next(d for d in os.listdir(ex) if os.path.isdir(os.path.join(ex, d)))
        src = os.path.join(ex, top, subpath) if subpath else os.path.join(ex, top)
        if not os.path.isdir(src):
            return False, f"子路径不存在: {subpath or '(根)'}"
        dest = os.path.join(REPO, folder)
        shutil.copytree(src, dest,
                        ignore=shutil.ignore_patterns(".git", ".gitignore", "node_modules"))
        if not os.path.isfile(os.path.join(dest, "SKILL.md")):
            shutil.rmtree(dest, ignore_errors=True)
            return False, "该仓库/子路径下未找到 SKILL.md, 不是技能目录, 已回滚"
        data.append({"folder": folder, "repo": repo,
                     "subpath": subpath or "", "pinned": bool(pinned)})
        save_sources(data)
        subprocess.run(["git", "add", "-A", folder], cwd=REPO)
        return True, f"已安装 {folder}(来自 {repo}{'/' + subpath if subpath else ''}), 待提交"
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
    return True, f"已删除 {folder}, 待提交/同步"


def run_cli(action):
    allowed = {"status": [], "update": [], "discover": [],
               "sync": [], "syncpush": ["--push"], "version": []}
    if action not in allowed:
        return "不允许的操作"
    try:
        r = subprocess.run([sys.executable, CLI, action.replace("syncpush", "sync"),
                            *allowed[action]], cwd=REPO,
                           capture_output=True, text=True, encoding="utf-8", timeout=600)
        return (r.stdout + r.stderr).strip() or "(无输出)"
    except Exception as e:  # noqa: BLE001
        return f"[异常] {e}"


# ───────────────────────── 页面渲染 ─────────────────────────
PAGE_CSS = """
:root{--bg:#0d1117;--panel:#161b22;--border:#30363d;--text:#e6edf3;--muted:#8b949e;
--green:#2ea043;--blue:#388bfd;--warn:#d29922;--danger:#f85149;--neutral:#21262d;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
font-family:'Segoe UI','Microsoft YaHei','PingFang SC',system-ui,sans-serif;font-size:14px;}
.wrap{max-width:1180px;margin:0 auto;padding:24px 20px 60px;}
header{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;
border-bottom:1px solid var(--border);padding-bottom:14px;margin-bottom:18px;}
header h1{font-size:20px;margin:0;font-weight:650;letter-spacing:.3px;}
header .sub{color:var(--muted);font-size:12.5px;}
.card{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:16px 18px;margin-bottom:18px;}
.card h2{font-size:14px;margin:0 0 12px;color:var(--text);font-weight:600;}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px;}
button{font-family:inherit;font-size:13px;border:0;border-radius:7px;padding:8px 14px;
cursor:pointer;color:#fff;background:var(--blue);transition:filter .15s;}
button:hover{filter:brightness(1.12);}
button:disabled{opacity:.55;cursor:wait;filter:none;}
button.primary{background:var(--green);}
button.neutral{background:var(--neutral);color:var(--muted);}
button.danger{background:transparent;color:var(--danger);border:1px solid var(--danger);padding:5px 12px;}
button.danger:hover{background:rgba(248,81,73,.12);}
table{width:100%;border-collapse:collapse;font-size:13px;}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--border);vertical-align:top;}
th{color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.4px;}
tbody tr:hover{background:rgba(56,139,253,.06);}
td .folder{font-family:Consolas,Menlo,monospace;color:var(--blue);font-size:12.5px;}
td.purpose{max-width:380px;color:var(--muted);font-size:12.5px;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.badge{display:inline-block;font-size:11px;padding:2px 8px;border-radius:999px;
background:rgba(210,153,34,.16);color:var(--warn);border:1px solid rgba(210,153,34,.4);}
.muted{color:var(--muted);}
form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 16px;}
label{display:flex;flex-direction:column;gap:5px;font-size:12px;color:var(--muted);}
input[type=text]{background:#0a0e14;border:1px solid var(--border);border-radius:7px;
padding:9px 11px;color:var(--text);font-size:13px;font-family:inherit;}
input[type=text]:focus{outline:none;border-color:var(--blue);}
.check{display:flex;align-items:center;gap:8px;color:var(--text);font-size:13px;}
.check input{width:16px;height:16px;accent-color:var(--green);}
.form-actions{grid-column:1/-1;display:flex;gap:10px;align-items:center;}
#result{background:#0a0e14;border:1px solid var(--border);border-radius:8px;padding:14px;
font-family:Consolas,Menlo,monospace;font-size:12px;color:var(--text);white-space:pre-wrap;
max-height:300px;overflow:auto;min-height:60px;margin:12px 0;}
.empty{color:var(--muted);padding:20px;text-align:center;}
"""

PAGE_JS = """
function showErr(msg){
  const box = document.getElementById('result');
  box.style.color = '#f85149';
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
  box.style.color = '';
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
  }
}

document.querySelectorAll('[data-action]').forEach(b=>{
  b.addEventListener('click', ()=>act(b.dataset.action, b));
});

document.querySelectorAll('.del').forEach(b=>{
  b.addEventListener('click', async ()=>{
    const f = b.dataset.folder;
    if(!confirm('确认删除技能目录: '+f+' ?\\n将从仓库移除并提交删除(需另行同步)')) return;
    b.disabled = true; b.dataset.old = b.textContent; b.textContent = '删除中…';
    try{
      const d = await post('/api/delete', {folder: f});
      alert(d.msg); location.reload();
    }catch(e){
      b.disabled = false; b.textContent = b.dataset.old; showErr(e);
    }
  });
});

document.getElementById('addForm').addEventListener('submit', async e=>{
  e.preventDefault();
  const p = {
    folder:  document.getElementById('f_folder').value.trim(),
    repo:    document.getElementById('f_repo').value.trim(),
    subpath: document.getElementById('f_sub').value.trim(),
    pinned:  document.getElementById('f_pin').checked
  };
  if(!p.folder || !p.repo){ alert('文件夹名与来源仓库为必填'); return; }
  const btn = document.getElementById('addBtn');
  btn.disabled = true; btn.dataset.old = btn.textContent; btn.textContent = '安装中…';
  try{
    const d = await post('/api/add', p);
    alert(d.msg);
    if(d.ok){ location.reload(); }
    else { btn.disabled = false; btn.textContent = btn.dataset.old; }
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
    <span class="sub">仓库: __REPO__ · 版本 __VERSION__ · 零依赖 Web 仪表盘(所有机器可用)</span>
  </header>

  <div class="card">
    <h2>技能总览(__COUNT__ 个)</h2>
    <div class="toolbar">
      <button data-action="status">状态</button>
      <button class="primary" data-action="update">检查更新</button>
      <button data-action="discover">发现新技能</button>
      <button data-action="sync">提交本地</button>
      <button class="primary" data-action="syncpush">推送远端</button>
      <button class="neutral" data-action="version">版本</button>
    </div>
    <div id="result">点击上方按钮, 输出会显示在这里。</div>
    <table>
      <thead><tr>
        <th>目录</th><th>名称</th><th>作用</th><th>版本</th>
        <th>最后更新</th><th>来源仓库</th><th>固定</th><th>操作</th>
      </tr></thead>
      <tbody>__ROWS__</tbody>
    </table>
  </div>

  <div class="card">
    <h2>新增技能</h2>
    <form id="addForm">
      <label>文件夹名(必填)<input type="text" id="f_folder" placeholder="my-new-skill"></label>
      <label>来源仓库 owner/name(必填)<input type="text" id="f_repo" placeholder="op7418/Humanizer-zh"></label>
      <label>子路径(可选, 技能在仓库内的目录)<input type="text" id="f_sub" placeholder="skills/foo 或留空取根"></label>
      <label class="check"><input type="checkbox" id="f_pin"> 固定(pinned, 跳过自动更新)</label>
      <div class="form-actions">
        <button class="primary" type="submit" id="addBtn">安装并登记</button>
        <span class="muted">会自动下载、复制到技能库并写入 config/sources.json</span>
      </div>
    </form>
  </div>
</div>
<script>__JS__</script>
</body>
</html>"""


def render_rows(skills):
    if not skills:
        return '<tr><td colspan="8" class="empty">未找到含 SKILL.md 的技能目录</td></tr>'
    rows = []
    for s in skills:
        pin = '<span class="badge">已固定</span>' if s["pinned"] else '<span class="muted">—</span>'
        rows.append(
            "<tr>"
            f'<td><span class="folder">{html.escape(s["folder"])}</span></td>'
            f'<td>{html.escape(s["name"])}</td>'
            f'<td class="purpose" title="{html.escape(s["purpose"], quote=True)}">{html.escape(s["purpose"])}</td>'
            f'<td>{html.escape(s["version"])}</td>'
            f'<td>{html.escape(s["last_updated"])}</td>'
            f'<td><span class="folder">{html.escape(s["repo"])}</span></td>'
            f"<td>{pin}</td>"
            f'<td><button class="danger" data-folder="{html.escape(s["folder"])}">删除</button></td>'
            "</tr>"
        )
    return "\n".join(rows)


def render_page():
    skills = build_skills()
    return (PAGE_HTML
            .replace("__CSS__", PAGE_CSS)
            .replace("__JS__", PAGE_JS)
            .replace("__ROWS__", render_rows(skills))
            .replace("__REPO__", html.escape(REPO))
            .replace("__VERSION__", html.escape(read_version()))
            .replace("__COUNT__", str(len(skills))))


# ───────────────────────── HTTP 服务 ─────────────────────────
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
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
            self._send(200, json.dumps({"ok": True, "msg": run_cli(data.get("action", ""))},
                                       ensure_ascii=False), "application/json; charset=utf-8")
        else:
            self._send(404, json.dumps({"ok": False, "msg": "unknown"}, ensure_ascii=False),
                       "application/json; charset=utf-8")

    def log_message(self, *a):
        pass


def main():
    import argparse
    ap = argparse.ArgumentParser(description="AI-SKILLS Web 仪表盘")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    srv = HTTPServer((args.host, args.port), Handler)
    print(f"AI-SKILLS 仪表盘已启动: http://{args.host}:{args.port}  (Ctrl+C 退出)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        srv.shutdown()


if __name__ == "__main__":
    main()
