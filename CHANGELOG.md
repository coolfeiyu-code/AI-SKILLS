# 更新说明 / Changelog

版本号语义：**主版本.次版本.修订号（MAJOR.MINOR.PATCH）**，从 `1.0.0` 开始。具体步进规则如下，由维护者（或接手 AI）判断：

| 级别 | 格式 | 触发条件（示例） |
| :--- | :--- | :--- |
| **MAJOR 大更新** | `x.0.0` | 不兼容的结构性变更：移动技能目录布局、改名/增删 CLI 子命令、改 `config` 格式、增减平台支持、改仓库结构。需要人工迁移。 |
| **MINOR 中更新** | `1.x.0` | 向后兼容的新功能：新增 `discover` 子命令、支持新的 Coding 工具（Windsurf / Cline 等）、新增兴趣主题分类、成批新增技能。 |
| **PATCH 小更新** | `1.0.x` | 向后兼容的修复/小改：脚本 bug 修复、文档修正、`.gitignore` 收紧、单个技能更新（不改变项目结构）。 |

> **重要约定**：日常 `skillsync update` 刷新技能内容属于运维动作，**不一定**触发版本号步进；只有项目本体（脚本 / 结构 / 约定）变更才按上表 bump。技能自身的版本（如 `a-stock-data` v3.2.2）与本项目版本互不影响，分别记录于各自 `SKILL.md` 与下方的技能更新记录。

## [1.8.9] - 2026-10-10 · 启动体验三连修：bat 乱码 · 关网页即关服务 · macOS 双击启动

### 修复
- **`skillsync-web.bat` 中文乱码并报"不是内部或外部命令"**：bat 之前被保存为 UTF-8，而中文 Windows cmd 按 GBK 代码页逐行解析，中文字节被错读、引号被吞，残句被当作命令执行。现改为**以 ANSI/GBK 编码保存**（文件内注释说明编码要求，勿再转回 UTF-8）。
- **启动不再需要按任意键**：`timeout /t 1` 换成 `ping -n 2 127.0.0.1 >nul` 静默延时（无按键提示、无倒计时），双击 bat 后直接弹出浏览器。
- **关闭网页即自动关闭服务窗口**：页面 JS 每 2 秒向 `/api/ping` 发心跳；服务端看门狗首次收到心跳后武装，连续 10 秒无心跳（页面已关）自动退出。从未被浏览器打开过则不会自动退出（兼容先起服务后开页/无头用法）。
- **macOS 双击启动**：新增 `skillsync-web.command`（双击即开终端运行 `python3 skillsync_web.py`，关终端即停服务）。同步盘可能丢失可执行位，首次使用在终端执行一次 `chmod +x skillsync-web.command`。

## [1.8.8] - 2026-10-10 · 检查更新免 token：限流时自动回退网页版 commits.atom

- 实测代理与直连出口 IP 均被 GitHub 匿名 API 限流（403）后，检查更新仍会失败。新增兜底：`get_latest_commit_date()` 在 API 失败时自动改抓 **`github.com/{repo}/commits.atom`**（网页版提交订阅源，**非 API 端点，不占 60 次/小时限额**），解析首条 `<updated>` 得到最新提交日期；抓取同样"先代理后直连"重试，结果带 1 小时缓存。
- XML 用**字节**解析（`ET.fromstring(raw)`），避免带 encoding 声明的 feed 触发 `ValueError: Unicode strings with encoding declaration are not supported`。
- 效果：不设置 `GITHUB_TOKEN` 也能正常"检查更新"；设置 token 后 API 路径仍优先（数据更精确）。安装/发现新技能等其余 API 调用不受此兜底影响，限流仍建议设置 token。

## [1.8.7] - 2026-10-10 · 修复"检查更新"全部 403

### 修复
- **本地/自制技能不再误报 403**：`cmd_update` / `cmd_status` 对 `repo` 为空的本地技能（"从本机安装"进来的）直接跳过，不再去请求 `api.github.com/repos//commits`（空仓库路径 → 403）。现打印 `[local] 跳过 …（本地/自制技能，无上游）`。
- **GitHub API 限流(403)自动绕过代理重试**：原 `api_get` 仅在「网络层异常」时回退直连，HTTP 403 会直接抛出。现改为：首次走系统代理若遇 403/429，自动改用绕过代理的直连重试（Clash 等数据中心出口 IP 最易被 GitHub 限流，住宅直连通常可用）。
- **限流错误中文可操作化**：HTTP 403/429 时读取响应体，若为限流则提示"设置 `GITHUB_TOKEN`（只读 public PAT）可将 60 次/小时 提升至 5000 次/小时，详见 skillsync-web.bat 注释"，而非只有一行 `HTTP 403`。
- `skillsync-web.bat` 启动时若未检测到 `GITHUB_TOKEN`，打印一行设置提示（token 仍不进仓库）。

## [1.8.6] - 2026-10-10 · 重新连接横幅改为红色醒目 + 文案精简

- 「重新连接」横幅（`#relinkBanner` 主页 + 连接子面板 `#linkNotice`）由琥珀色 `warn` 改为红色 `danger` 样式（红底/红左边框/加粗红字，更显眼）。
- 文案精简：由「⚠ 检测到 N 个新增/变更技能（如 …），工具侧尚未生效。点下方『一键连接全部』即可同步（幂等，不影响已有链接）。」缩短为「⚠ 有 N 个新技能未同步到工具侧，点『一键连接全部』即可生效」。

## [1.8.5] - 2026-10-10 · 重新连接提示修复 · 从本机安装支持系统文件夹对话框

### 修复
- **新增技能不弹"重新连接"提示（根因修复）**：原提示靠"连接基线"（首次点「一键连接全部」才生成）对比差异，从未连接过时基线不存在 → 直接不提示；且提示只挂在「连接 Coding 工具」子面板，主页看不到。
  - 新增 `link.py: mark_pending(folders)`：安装/删除技能后写 `pending_relink` 与 `pending_new` 到本机状态文件；`link_all()` 完成后清空标记并写基线。
  - `install_skill`（GitHub）/`install_local_skill`（本机）成功后均调用 `linker.mark_pending([folder])`，**即使从未建立基线也能可靠提示**。
  - `links_status()` 合并 `pending_new` 与基线差异为 `display_new`，返回给前端；主页新增 `#relinkBanner` 横幅，加载即显示"检测到 N 个新增/变更技能，工具侧尚未生效"；子面板提示同步改用 `display_new`。
- **从本机安装支持"打开文件夹对话框"**：新增「浏览…」按钮，优先用 `window.showDirectoryPicker()`（Edge/Chrome 原生系统对话框），读取出目录内全部文件后**以 multipart 上传**安装；不支持时回退到隐藏的 `webkitdirectory` 文件输入框。
  - 关键点：安装完全不依赖浏览器能否拿到绝对路径（即以前"打不开/拿不到路径"坑的根因），改用"上传文件内容"方式，后端 `install_local_skill_from_files()` 重建目录结构并登记。
  - 后端新增 `parse_multipart()`（Python 3.13 已移除 `cgi`，改用 `email` 模块）解析 `multipart/form-data`；`/api/add-local` 同时支持 JSON（绝对路径模式）与 multipart（对话框上传模式）。
  - URL 路径穿越防护：逐文件校验 `..` 与绝对路径，仅落地于 `REPO/<folder>/` 下。

## [1.8.4] - 2026-10-10 · 网页端支持从本机安装技能

- 新增「从本机安装技能」：在仪表盘「安装新技能」卡片内填**本机绝对路径**即可把任意本地目录复制进仓库并登记到 `config/sources.json`，无需 GitHub 仓库。
- 分类支持每技能自定义：`sources.json` 新增可选 `category` 字段；新增「自制SKILL」分组，`category_of()` 优先读取该字段（回退到原 `CATEGORIES` 字典）。
- 本地 / 自制技能安装后默认加入 `.gitignore`，避免含明文密钥等敏感配置被 `git add` 进 GitHub 历史（安全扫描命中高危时也会提示已忽略）。
- 已用此功能把 3 个自制 skill 并入库：`ai-model-vault` / `commandcode-proxy-grok-setup` / `wxq-lineups-update`，分类均为「自制SKILL」。
- 说明：本地安装与 GitHub 安装互不冲突；自制 skill 文件就在仓库目录内，可直接编辑（仪表盘「查看」按钮可预览内容）。

## [1.8.3] - 2026-10-09 · 连接器技能变更提示

### 新增
- **连接器"技能变更提示"**：「连接 Coding 工具」卡片新增横幅。新增技能时提示"检测到 N 个新增技能，工具侧尚未生效，点『一键连接全部』即可同步（幂等，不影响已有链接）"；删除技能时提示"已删除 M 个，工具侧悬挂链接会在下次连接或撤销时自动清理，无需重连"。
- **连接基线**：连接时在机器本地状态文件 `~/.skillsync-links.json`（仓库外、零污染）记录"上次连接时的技能清单"；状态接口对比当前仓库技能集与基线，算出新增/删除；**无基线时不误报**。
- 删除技能无需重新连接：悬挂链接由连接器既有 `sweep_dangling` 在下次连接时自动清理，不影响其他技能、不断链。

## [1.8.2] - 2026-10-09 · 未推送徽标动态刷新

### 修复
- **推送成功后徽标不更新**：表头徽标是页面加载时的静态快照，推送后不刷新页面就停留在旧值。改为动态：新增 `/api/unpushed` 接口，每次按钮操作完成后自动重新查询并更新/隐藏徽标。
- `sync` 输出文案更明确：无改动时提示「本地无新改动(工作区干净)」，推送成功追加「✓ 已推送到 GitHub」。

## [1.8.0] - 2026-10-09 · 安全扫描 · 未推送徽标 · 拉取 · 回收站 · 搜索 · 查看器 · 悬挂清扫

### 新增（7 项改进一次落地）
1. **安装安全扫描**：安装/加载时对技能内容做轻量风险扫描（高危：管道执行远程脚本/格式化系统盘/读取凭据/窃取环境变量；提示：诱导忽略指令/外发数据/下载执行/超长 Base64）。表格新增 **风险列**（高危/注意/✓），安装结果直接给出风险摘要。
2. **未推送提交徽标**：表头常驻「⚠ 本地领先 N 个提交未推送」——因 .git 不进同步盘，未推送提交只在本机，红色提醒防历史丢失；推送后自动消失。
3. **「从 GitHub 拉取」按钮**：新增 CLI `pull` 子命令（`--ff-only` 仅快进，有分叉明确报错），仪表盘一键拉取，多机闭环补全。
4. **回收站面板**：列出 git 历史中删除过且已不在磁盘的技能（删除日期+提交说明），一键「恢复」（从删除提交的父版本整目录捞回）；从未提交过的技能无法恢复，界面有明示。
5. **表格即时搜索**：按名称/作用实时过滤，分组行智能跟随显隐。
6. **技能查看器**：每行「查看」按钮，弹层显示该技能 SKILL.md 原文（80KB 内）。
7. **悬挂链接自动清扫**：连接器在连接前自动清理"指向本仓库但技能已被删除"的失效链接（经实证：悬挂 junction 的 resolve 仍指向仓库内路径，检测可靠）。

### 修复
- `skillsync.py git()` 输出强制 UTF-8（中文 Windows 管道 GBK 乱码隐患）；`make_link` 改字节模式避免 GBK 解码线程异常。

## [1.7.1] - 2026-10-09 · 删除功能真修复（真浏览器验证）

### 修复
- **删除从未生效的真正根因**：删除按钮 class 为 `danger`，而 JS 绑定选择器是 `.del`——**选择器匹配不到任何按钮，处理器从未挂上**（此前静态检查把 `class="danger"` 计入"删除按钮数"导致自我误判）。修复：按钮 class 改为 `danger del`。
- **真浏览器(Playwright+Edge)端到端验证**：点击删除 → 变"确认删除?" → 再点 → `POST /api/delete` HTTP 200 → 页面刷新后按钮消失 → 磁盘目录删除 ✓。
- 删除技能时**同步清理各工具侧的悬挂链接**（该技能在 19 个工具目录里的 junction 一并移除）。
- 补 `favicon.ico` 204 响应，控制台不再报 404。

## [1.7.0] - 2026-10-09 · 连接器入驻 Web 仪表盘（一个界面完成一切）

### 新增
- 仪表盘新增 **「连接 Coding 工具」** 卡片（复用 `tools/link.py`，方案A/B 全部入网页）：
  - **连接矩阵自动加载**：各工具 skills 目录 / 已连接数 / 同名占用 / 总项一目了然；
  - **一键连接全部** / **撤销全部链接**（两次点击确认，与删除同款防误触）/ **复制自连接提示词**（一键进剪贴板）/ 刷新状态；
  - 操作输出统一回显到页面输出框，全程零弹窗。

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
