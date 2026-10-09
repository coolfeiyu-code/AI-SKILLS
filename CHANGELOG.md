# 更新说明 / Changelog

版本号语义：**主版本.次版本.修订号（MAJOR.MINOR.PATCH）**，从 `1.0.0` 开始。具体步进规则如下，由维护者（或接手 AI）判断：

| 级别 | 格式 | 触发条件（示例） |
| :--- | :--- | :--- |
| **MAJOR 大更新** | `x.0.0` | 不兼容的结构性变更：移动技能目录布局、改名/增删 CLI 子命令、改 `config` 格式、增减平台支持、改仓库结构。需要人工迁移。 |
| **MINOR 中更新** | `1.x.0` | 向后兼容的新功能：新增 `discover` 子命令、支持新的 Coding 工具（Windsurf / Cline 等）、新增兴趣主题分类、成批新增技能。 |
| **PATCH 小更新** | `1.0.x` | 向后兼容的修复/小改：脚本 bug 修复、文档修正、`.gitignore` 收紧、单个技能更新（不改变项目结构）。 |

> **重要约定**：日常 `skillsync update` 刷新技能内容属于运维动作，**不一定**触发版本号步进；只有项目本体（脚本 / 结构 / 约定）变更才按上表 bump。技能自身的版本（如 `a-stock-data` v3.2.2）与本项目版本互不影响，分别记录于各自 `SKILL.md` 与下方的技能更新记录。

## [1.6.0] - 2026-10-09 · 统一连接器：多机多 Coding 工具一键接入

### 新增
- **`tools/link.py`**（零依赖跨平台）取代旧 `tools/link.sh` / `link.ps1`（已移除）：
  - **自动探测**：已知 19 类工具（WorkBuddy/Claude Code/CodeBuddy/Codex/Cursor/Trae/Windsurf/Cline/Roo/OpenCode/Crush/Grok CLI/zcode/pi/commandcode/dsh/Gemini/Qwen/iFlow）+ 启发式扫描任何 `~/.<工具>/skills` 目录，未知工具自动纳入；
  - **一键连接**：`--all` 为每个工具的 skills 目录按技能建 Junction(Windows)/Symlink(macOS/Linux)，幂等可重复；工具侧已有同名真实目录自动跳过；
  - **配套**：`--status` 连接矩阵 / `--remove` 一键撤销(只撤指向本仓库的链接) / `--to DIR` 自定义目标(记于 `~/.skillsync-links.json`, 不进仓库) / `--prompt` 生成"自连接提示词"（方案B：粘给任意 coding 工具让它自己连）。
- **`连接技能.bat` / `连接技能.command`**：双击即完成本机全部连接并显示矩阵。
- 无污染公约落地：链接只建在工具侧，仓库零写入；本机实测 19 工具 × 28 技能 = **532 条链接，0 失败 0 冲突**，运行后 `git status` 保持干净。

## [1.5.2] - 2026-10-09 · 全面去弹窗化 · 一步同步

### 修复
- **删除按钮"没反应"根因**：删除确认依赖浏览器 `confirm()` 弹窗——一旦浏览器勾选过"禁止此页面再显示对话框"，`confirm()` 会静默返回 false，点击删除零反馈且服务端无感知。**整个界面彻底去弹窗化**：
  - 删除改为**两次点击确认**：第一次点按钮变红色「确认删除？」，再点执行，4 秒不点自动复位；
  - 安装/新增/发现的所有 `alert()` 反馈改为页面内输出框显示，浏览器弹窗设置不再影响任何功能。
- **推送逻辑合并**：「提交本地」「推送远端」两步合并为一个 **「同步到 GitHub」** 按钮（= `sync --push`，提交改动并推送一步完成），工具栏提示语同步更新。

## [1.5.1] - 2026-10-09 · 仪表盘端口改 8766，消除与 AI进度 冲突

### 变更
- **默认端口 `8765` → `8766`**：`AI进度/collect.py --serve` 同样常驻 `127.0.0.1:8765`，两个仪表盘谁后启动谁绑定失败。技能库仪表盘全面改用 **8766**（脚本默认值、bat 端口清理与浏览器地址、文档），`AI进度` 侧保持不变。
- 涉及文件：`skillsync_web.py`、`skillsync-web.bat`、`README.md`、`TASK.md`。

## [1.5.0] - 2026-10-09 · 发现即可装 · 表单智能解析 · 版本面板

### 变更
- **「版本」按钮显示更新内容**：不再只打印版本号，同时展示 CHANGELOG 最近两节更新说明。
- **「安装新技能」表单移到页面顶部**，且粘贴完整 GitHub 链接或 owner/name 后**自动解析文件夹名**（可手动覆盖）；子路径仍可留空自动识别。
- **发现即可装**：「发现新技能」改为结构化列表（⭐星数 + 简介 + 仓库），每个候选带「安装」按钮，点击直接走安装流程入库；已安装/非技能仓库自动过滤；API 全部限流时给出明确提示。
- **提交本地 / 推送远端 语义说明**：工具栏下新增一行提示，两个按钮加悬停说明；推送遇无凭据时快速报错（`GIT_TERMINAL_PROMPT=0`）不再挂起。

## [1.4.1] - 2026-10-09 · 安装流程免疫 GitHub API 限流

### 修复
- **"无法访问仓库 … HTTP 403: rate limit exceeded"**：安装流程原先必须先调 GitHub API 拿默认分支，匿名 API 每小时 60 次的限额被 status/discover 耗尽后安装即被卡死。现改为：默认分支优先复用 `skillsync` 的 `api_get`（带 1 小时缓存 + `GITHUB_TOKEN` 支持），**API 失败自动绕过，按 `main`/`master` 直接下载 codeload tarball**（下载端点不受 API 限流影响）。
- **子路径自动识别**：仓库根无 SKILL.md 时，在一/两层子目录内自动探测技能位置（多候选时优先与仓库名同名者，如 `skills/<name>`），识别结果写入 `sources.json` 供后续 update 使用；无法唯一确定才提示手动填子路径。
- `skillsync-web.bat` 增加可选 `GITHUB_TOKEN` 注释行，填入 PAT 可将 API 限额提升至 5000 次/小时。

## [1.4.0] - 2026-10-09 · 素雅淡色主题 · 技能分类展示

### 变更
- **淡色主题**：深墨色界面整体换为素雅淡色（宣纸暖白底 `#f6f4ef` + 墨色文字 + 灰绿点缀），卡片白底轻阴影，错误提示色随主题适配。
- **技能分类展示**：表格按类别分组，组头行显示「类别 · 数量」。归纳（未命中归入"其他"）：
  - **前端设计**（15）：frontend-design, brandkit, design-system, gpt-tasteskill, soft-skill(即 high-end-visual-design), interface-design, image-to-code-skill, imagegen-frontend-mobile, imagegen-frontend-web, minimalist-skill, redesign-skill, taste-skill, ui-styling, ui-ux-pro-max, impeccable
  - **投研·交易**（2）：a-stock-data, serenity-skill（trading-skills / gauss314-skills / InvestSkill 为多技能合集仓库，无根 SKILL.md，不在表中逐行列出）
  - **内容·研究**（4）：Humanizer-zh, last30days, last30days-cn, agent-reach
  - **工程·效率**（6）：find-skills, gh-skill-installer, output-skill, yao-meta-skill, grill-me, dotnet-mod-recon
  - 类别映射维护于 `skillsync_web.py` 的 `CATEGORIES`；新增技能若未归类会出现在"其他"组。

## [1.3.3] - 2026-10-09 · 旧实例防护（"改了没生效"根因）

### 修复
- **根因**：Web 服务是常驻进程，**修改文件后不重启不会生效**；而重启时新实例绑定 8765 失败会瞬间闪退，浏览器连到的仍是带着旧代码的旧进程——表现为"改了还是一样的报错"。
- `skillsync_web.py`：端口被占用时不再闪退，改为打印明确提示（关闭旧实例 / 换端口）并等待回车；页面头部新增 **服务启动时间** 标识，旧实例一眼可辨；所有响应加 `Cache-Control: no-store`。
- `skillsync-web.bat`：启动前自动清理占用 8765 端口的旧实例，再拉起新进程。

## [1.3.2] - 2026-10-09 · 网络与编码健壮性修复

### 修复
- **Web `run_cli` 加固**：`r.stdout + r.stderr` 在子进程输出异常时可触发 `TypeError: unsupported operand type(s) for +: 'NoneType' and 'NoneType'`（用户实测发现新技能/检查更新均复现）。改为 `(r.stdout or "") + (r.stderr or "")`，并增加 `errors="replace"`、非零退出码提示，异常时不再吞掉真实输出。
- **子进程强制 UTF-8**：中文 Windows 下管道默认 GBK 编码，`discover` 输出的 ⭐ / `status` 输出的 ✓ 可能令子进程编码崩溃；调用子进程时注入 `PYTHONUTF8=1` 与 `PYTHONIOENCODING=utf-8`。
- **网络直连兜底（绕过系统代理）**：Clash 等系统代理异常会导致 urllib/git 全部联网失败（"下载新技能无法下载"、git clone schannel 报错）。`skillsync.py` 新增 `_download` 并在 `api_get`、`apply_update` 中接入"系统代理失败 → 绕过代理直连重试"；Web `install_skill` 同样改为 `_fetch_bytes` 双通道下载（API 取默认分支 + codeload tarball）。

## [1.3.1] - 2026-10-09 · 移除桌面 GUI · Web 按钮反馈修复

### 移除
- **删除 `skillsync_gui.py` 与 `skillsync-gui.bat`（Tkinter 桌面管理器）**：依赖 tcl/tk，实际环境无法启动（用户确认弃用）。技能管理统一走 Web 仪表盘 / CLI。

### 修复（Web 仪表盘）
- **按钮"点了没反应"的根因**：操作输出框原本在页面最底部（表格+表单之下，视口外），点击工具栏按钮后输出写进了看不见的框。修复：**输出框移至工具栏正下方**，点击即见；按钮增加运行态（禁用 + 显示"运行中…"，完成后恢复）；`fetch` 失败时错误直接显示在输出框（并提示确认服务窗口仍在运行）；`window.onerror` 全局兜底可见化；事件绑定由内联 `onclick` 改为 `data-action` + `addEventListener`。
- **新增技能改用 codeload tarball**（与 `skillsync update` 同机制：GitHub API 取默认分支 → `codeload.github.com` 下载 → `unpack_archive` 解压），不再 `git clone`，规避 Windows git/schannel 与代理导致的克隆失败；**安装成功后才写入 `sources.json`**（旧逻辑先登记后克隆，失败会残留脏条目）；安装后校验目录含 `SKILL.md`，否则回滚。
- `delete_skill` 兜底 `git add -A` 收窄为 `git add -A -- <folder>`，避免误暂存无关变更。
- `skillsync-web.bat` 启动前检查 `python` 是否可用，缺失时给出明确提示。

## [1.3.0] - 2026-10-09 · Web 仪表盘（跨机器复用 · 增删技能可视化）

> 触发条件（对照步进表）：新增 `skillsync_web.py` 零依赖 Web 仪表盘，支持技能表格化浏览与新增/删除 → 向后兼容新功能 → MINOR。

### 新增
- **`skillsync_web.py`**：零依赖 Web 仪表盘（仅用 Python 标准库 `http.server`，**无需 tkinter、无需 pip 安装**），满足「所有机器可直接使用」：
  - **表格总览**：自动扫描含 `SKILL.md` 的目录，聚合 `SKILL.md` frontmatter（名称/作用/版本号）、`CATALOG.md`（中文标签/功用）、`config/sources.json`（来源仓库/subpath/pinned）、`git log`（最后更新），展示列：目录 / 名称 / 作用 / 版本号 / 最后更新 / 来源仓库 / 固定 / 操作。
  - **新增技能**：填 文件夹名 + 来源仓库(owner/name) + 可选子路径 + 是否 pinned → 自动 `git clone --depth 1` + 复制 subpath（排除 `.git`）+ 写入 `config/sources.json` + `git add`。
  - **删除技能**：按钮触发 `git rm -r -f` 并从 `sources.json` 移除（删除前浏览器二次确认）。
  - **一键操作**：状态 / 检查更新 / 发现新技能 / 提交本地(sync) / 推送远端(sync --push) / 版本，输出回显到页面。
- **`skillsync-web.bat`**：一键启动 Web 仪表盘并打开浏览器（Windows）；macOS/Linux 运行 `python3 skillsync_web.py` 后访问 `http://localhost:8765`。
- 与 `skillsync_gui.py`（桌面，需 tcl/tk）并存：Web 版面向「任意机器零配置复用」，桌面版面向本机有 tcl/tk 的快捷操作。

### 说明
- 元数据解析为轻量实现：`SKILL.md` 仅取顶层 `key: value`；版本号取 `version:` 字段（缺省显示 `—`）；最后更新取该目录 `git log -1`（非 git 跟踪则回退 `SKILL.md` 修改时间）。

## [1.2.0] - 2026-10-09 · 图形界面（Tkinter 桌面管理器）

> 触发条件（对照步进表）：新增 `skillsync_gui.py` 图形界面 + `skillsync-gui.bat` 一键启动器，属向后兼容的新功能 → MINOR。

### 新增
- **`skillsync_gui.py`**：零依赖 Tkinter 桌面管理器（深墨 / Linear-Vercel 克制风），提供按钮式操作：`状态` / `检查更新` / `一键更新全部` / `发现新技能` / `推送同步` / `版本` / `打开目录`，并带实时滚动输出与任务队列（运行中按钮自动禁用）。
  - 「一键更新全部」= `update`（比对并本地更新非 pinned 技能）→ `sync --push`（提交并推送 `origin/main`），两步串行、失败即止。
  - 仅依赖标准库 + tkinter；**必须用带 tcl/tk 的 CPython 启动**（本机为 `C:\Users\13588\AppData\Local\Python\pythoncore-3.14-64\python.exe`，tk 8.6）。缺失 tkinter 时会打印友好提示并退出。
- **`skillsync-gui.bat`**：一键启动器。自动定位带 tcl/tk 的 Python，双击即弹出管理器窗口；无需命令行。
- CLI（`skillsync.py`）与 GUI 共用同一解释器（`sys.executable`）调用，避免 PATH 混乱；CLI 仍为纯标准库，可在任意 3.11+ Python 运行。

### 说明
- GUI 与 CLI 并行存在：命令行用户继续用 `python skillsync.py ...`；偏好图形界面的用户双击 `skillsync-gui.bat` 即可。

## [1.1.1] - 2026-10-09 · discover 精度优化

### 修复 / 改进
- `discover` 对候选仓库增加 **SKILL.md 存在性校验**：用 GitHub API 检查仓库根目录是否含 `SKILL.md` 或 `skills/` 子目录，过滤掉 dify / n8n / langchain 这类被 topic 误命中但实际不是 skill 的大框架；仅对高星候选（前 `max(top*2, 20)`）做校验以控制 API 调用。校验失败时保守保留候选，不因限流误删。
- 校验逻辑：`repo_has_skill_md(full)`，网络/限流异常时返回 `True`（保留），避免漏掉真实技能。

## [1.1.0] - 2026-10-09 · CLI 落地

> 触发条件（对照步进表）：新增 `discover` 子命令 + 新增 `config/` 兴趣与来源配置 + 新增 `tools/` 软链脚本 → 向后兼容的新功能，按约定 bump 为 MINOR。

### 新增
- 跨平台 CLI `skillsync.py`（零依赖 Python 3.11+）正式落地，覆盖 5 个子命令：
  - `status`：各技能 本地 git 基线 / 上游最新提交 / pinned / 待更新 一览。
  - `update [--dry-run]`：仅对「上游更新且非 pinned」的技能用 `codeload.github.com` tarball 覆盖并本地提交。
  - `discover [--top N] [--min-stars]`：在 GitHub 按 star 发现相关高星技能，**仅列出候选**供人工决策（默认最小 50★，限定 `claude-code/claude-skill/cursor-rules/agent-skill/skills/prompt-engineering` 等 skill 相关 topic，已过滤 claude-code/cursor/claude/codex 等泛名与已存在项）。
  - `sync [--push]`：提交本地变更，`--push` 才推送到 `origin/main`。
  - `version`：打印 `VERSION` 文件内容。
- `config/sources.json`：受管技能映射（repo / subpath / pinned）的单一事实源，可被 `skillsync.py` 内嵌 `SOURCES` 兜底覆盖。
- `config/interests.json`：`discover` 的 5 类兴趣关键词（web/前端设计、投研/金融、中文内容、agent/工具、生产力）。
- `tools/link.sh`（macOS/Linux）与 `tools/link.ps1`（Windows）：把每个含 `SKILL.md` 的技能目录以符号链接 / Junction 指向 WorkBuddy / Claude / Cursor 等 Coding 软件，实现「技能库指向此处」且不复制、不污染本仓库。

### 修复 / 一致性
- 从 `config/sources.json` 与 `skillsync.py` 内嵌 `SOURCES` 中移除已被用户删除的 `ian-xiaohei-illustrations`、`seedance-prompt`，防止 `update` 在后续上游有新提交时误复活已删技能。
- 同步修正 `TASK.md`（版本号、`config/*.json` 文件名、删除技能行）与 `CATALOG.md`（删除记录说明），保持文档与仓库一致。

### 已知限制（待后续讨论）
- `discover` 基于 GitHub topic 搜索，仍可能混入少量非 skill 的大型仓库（如 dify 类）；候选仅作人工筛选参考，不直接安装。

## [1.0.0] - 2026-10-09 · 项目化基线

### 新增
- 建立项目文档体系：`README.md`（项目复用说明 + 其他 Coding 软件指向指引 + 无垃圾公约）、`TASK.md`（AI 接手手册）、`VERSION`、`CHANGELOG.md`、`CATALOG.md`（技能清单，由旧 README 迁移）。
- 确立版本号与「大/中/小」步进策略（起点 `1.0.0`）。
- 确立跨平台（macOS / Windows）基线：以 Python 3.11+ 驱动的 `skillsync` 工具承载一键更新 / 自动发现 / 同步（详见 `TASK.md`）。
- 确立「无垃圾公约」：所有运行时产物（下载的 tarball、临时解压、缓存、日志）一律写到**仓库外**的系统缓存目录；`.gitignore` 已覆盖常见垃圾文件。
- 技能目录维持原位（仓库根）；此前已裁剪 4 个不匹配技术栈/审美的 skill，并修复了 README 残留的 git 合并冲突标记。

### 说明
- 本版本为文档与约定基线；CLI（`skillsync`）实现落地后将作为 MINOR 更新 bump 至 `1.1.0`。
