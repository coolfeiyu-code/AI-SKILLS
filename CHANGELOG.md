# 更新说明 / Changelog

版本号语义：**主版本.次版本.修订号（MAJOR.MINOR.PATCH）**，从 `1.0.0` 开始。具体步进规则如下，由维护者（或接手 AI）判断：

| 级别 | 格式 | 触发条件（示例） |
| :--- | :--- | :--- |
| **MAJOR 大更新** | `x.0.0` | 不兼容的结构性变更：移动技能目录布局、改名/增删 CLI 子命令、改 `config` 格式、增减平台支持、改仓库结构。需要人工迁移。 |
| **MINOR 中更新** | `1.x.0` | 向后兼容的新功能：新增 `discover` 子命令、支持新的 Coding 工具（Windsurf / Cline 等）、新增兴趣主题分类、成批新增技能。 |
| **PATCH 小更新** | `1.0.x` | 向后兼容的修复/小改：脚本 bug 修复、文档修正、`.gitignore` 收紧、单个技能更新（不改变项目结构）。 |

> **重要约定**：日常 `skillsync update` 刷新技能内容属于运维动作，**不一定**触发版本号步进；只有项目本体（脚本 / 结构 / 约定）变更才按上表 bump。技能自身的版本（如 `a-stock-data` v3.2.2）与本项目版本互不影响，分别记录于各自 `SKILL.md` 与下方的技能更新记录。

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
