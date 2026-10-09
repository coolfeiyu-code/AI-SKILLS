# AI-SKILLS · 跨平台 AI 技能库管理器

> 一个**带版本号、可一键更新、可自动发现高星技能、可同步到 GitHub** 的本地 AI 技能库。macOS / Windows 双端通用；并指导 Cursor / Claude Code / Codex / WorkBuddy / Cline / Windsurf 等把技能库指向此处，且**运行时不污染本仓库**。

**当前版本：`1.0.0`**（版本定义见 [`VERSION`](./VERSION)，更新说明见 [`CHANGELOG.md`](./CHANGELOG.md)）。

---

## 1. 这是什么

`C:/AI-SKILLS`（GitHub: [`coolfeiyu-code/AI-SKILLS`](https://github.com/coolfeiyu-code/AI-SKILLS)）既是技能仓库，也是被管理的项目。库内 31 个 skill 目录直接放在仓库根下，覆盖：投研（A股/美股/产业链/交易纪律）、前端设计（Anthropic 官方 + 一整套反套路/审查/组件技能）、内容（中文人性化、配图）、研究（多平台热点）、效率（需求拷问、技能自举）、以及 `.NET` Mod 逆向。

项目提供一套工具（`skillsync`），把「人工逐个去 GitHub 比对更新」变成一条命令，并能在 GitHub 上发现你可能感兴趣的高星技能、一键同步到远端。

## 2. 目录结构

```
AI-SKILLS/
├── README.md        # 本文件：项目复用说明 + 其他 Coding 软件指向指引 + 无垃圾公约
├── TASK.md          # AI 接手手册（架构/命令/约定/坑）
├── CATALOG.md       # 技能清单（功能/激活命令/更新记录）
├── VERSION          # 语义化版本号（1.0.0）
├── CHANGELOG.md     # 大/中/小版本更新说明
├── skillsync*       # 跨平台 CLI（update / discover / sync / status）
├── config/          # discover 的兴趣主题配置
├── tools/           # 给其他 Coding 软件的符号链接/配置脚本
├── .gitignore       # 已覆盖常见垃圾文件
└── <31 个 skill 目录>/
```

## 3. 快速开始（Mac / Win）

| | macOS | Windows |
| :--- | :--- | :--- |
| 运行时 | 系统自带或 `brew install python` | Git Bash（随 Git 安装）或 PowerShell + Python 3.11+ |
| 克隆 | `git clone https://github.com/coolfeiyu-code/AI-SKILLS.git` | 同上 |
| 运行 | `python3 skillsync.py <命令>` | `python skillsync.py <命令>`（或 Git Bash 内同左） |

所有命令均**跨平台**，依靠 Python + `pathlib`，不依赖任何平台专属命令。

## 4. 核心功能

| 命令 | 作用 |
| :--- | :--- |
| `skillsync update [--dry-run]` | **一键更新**：比对每个受管技能的上游最近提交，仅对确有更新的、且非 `pinned` 的技能用 tarball 覆盖更新，并提交。 |
| `skillsync discover [--top N]` | **自动发现**：在 GitHub 按 star 数搜索与你兴趣主题相关的高星 skill，去重后给出候选清单（含 stars / 简介 / 仓库地址）。 |
| `skillsync sync` | **同步到 GitHub**：`git add -A` → 提交 → `git push origin`（默认分支 `main`）。 |
| `skillsync status` | 列出每个技能的本地基线 vs 上游最新、是否 `pinned`、是否有待更新。 |

详见 [`TASK.md`](./TASK.md)。

## 5. 给其他 Coding 软件：把技能库指向此处

默认情况下，各 AI 编码工具在自己的目录（如 `~/.workbuddy/skills`、`~/.claude/skills`）读取技能。**推荐做法是把该目录软链（symlink）到本仓库根**，或逐技能软链，让所有工具共享同一份受管技能库：

| 工具 | 技能/规则目录（示意） | 指向方式 |
| :--- | :--- | :--- |
| **WorkBuddy** | `~/.workbuddy/skills/` | 软链整个目录到本仓库根，或逐技能软链到各 skill 子目录 |
| **Claude Code** | `~/.claude/skills/` 或项目 `.claude/skills/` | 同上 |
| **Cursor** | `.cursor/rules` 或 `~/.cursor/rules` | 软链规则目录引用本仓库（规则类技能） |
| **Codex / ChatGPT** | 项目 `agents/` 或 `commands/` | 引用本仓库对应技能 |
| **Cline / Roo** | 项目 `.clinerules` 或技能目录 | 引用本仓库 |
| **Windsurf** | `.windsurf/rules` 或技能目录 | 引用本仓库 |

- **跨平台软链脚本**放在 `tools/`（含 `.sh` 与 `.ps1`），按工具一键生成软链。
- ⚠️ **只读引用**：工具应把本仓库当作技能**来源**，不要在本仓库内写入中间文件 / 缓存 / 日志。

## 6. 无垃圾公约（No-Garbage Pact）

本仓库只放「技能目录 + 项目文档 + 工具脚本」。任何运行时产物严禁写入仓库：

1. **运行时产物外置**：下载的 tarball、临时解压、缓存、日志一律写到仓库外的系统缓存
   （Win: `%LOCALAPPDATA%/skillsync`；Mac: `~/Library/Caches/skillsync` 或 `~/.cache/skillsync`），运行后清理。
2. **`.gitignore` 已覆盖**：`*.log`、`tmp/`、`**/.cache/`、`node_modules/`、`output/`、`reports/`、`dist/`、`build/`、`*.db`、`.env` 等常见垃圾。
3. **提交前自检**：`git status --porcelain` 若出现意外文件，先排查来源，不要直接 `add -A` 提交垃圾。
4. **其他工具遵守**：第 5 节指向本仓库的工具须设为只读引用，不在内留痕。

## 7. 版本与更新说明

- 版本号在 [`VERSION`](./VERSION)（当前 `1.0.0`），步进规则见 [`CHANGELOG.md`](./CHANGELOG.md)：
  - **大更新 `x.0.0`**：不兼容结构变更（移动目录、改 CLI、改 config 格式、增减平台）。
  - **中更新 `1.x.0`**：向后兼容新功能（新增 `discover`、支持新工具、新增兴趣分类）。
  - **小更新 `1.0.x`**：修复/小改（脚本 bug、文档、`.gitignore`、单技能更新）。
- 日常 `update` 刷新技能内容**不一定** bump 版本；只有项目本体变更才 bump。

## 8. 已知约定与坑（务必先读）

- **`pinned` 技能（跳过自动更新，覆盖=降级或丢改造）**：
  - `trading-skills` / `interface-design` / `gauss314-skills` —— 本地副本比上游提交还新。
  - `grill-me` —— 本地移植合并版（合并 grill-me + grilling 逻辑）。
- **`agent-reach`** 上游结构已变，skill 文件在 `agent_reach/skill/` 子目录，更新时只取该子目录。
- 仓库根 README 曾出现 git 合并冲突标记，已修复；改动 README 注意别再引入。
- 不要未经确认就 `git push`；`sync` 由用户触发。

## 9. 相关文档

- [`TASK.md`](./TASK.md) — AI 接手手册
- [`CATALOG.md`](./CATALOG.md) — 技能清单
- [`CHANGELOG.md`](./CHANGELOG.md) — 更新说明
- [`VERSION`](./VERSION) — 版本号
