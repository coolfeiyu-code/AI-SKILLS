# TASK.md — AI 接手手册

> 给「下一个接手本项目的 AI / 协作者」的快速上手。读完即可安全维护 `C:/AI-SKILLS` 技能库。

## 0. 一句话目标

把 `C:/AI-SKILLS`（GitHub: `coolfeiyu-code/AI-SKILLS`）这个本地 AI 技能库，管理成一个**版本化、双端（macOS/Win）、可一键更新、可自动发现高星技能、可同步 GitHub** 的项目，且运行时不污染仓库。

## 1. 关键事实（先读）

- 仓库根即技能库：31 个 skill 目录**直接放在根下**（不嵌套 `skills/`）。
- 远程：`origin = https://github.com/coolfeiyu-code/AI-SKILLS.git`，默认分支 `main`。
- 工具链：**Python 3.11+**（建议 3.13）。跨平台靠 Python + `pathlib`，不用平台专属命令。
- 版本：`VERSION` 文件（`1.1.0`），语义化；`CHANGELOG.md` 记录大/中/小版本。
- 无垃圾公约：运行时产物一律写仓库外系统缓存；`.gitignore` 已覆盖常见垃圾。
- 文档：`README.md`（项目复用+工具指向+公约）、`CATALOG.md`（技能清单）、本文件。

## 2. 架构 / 文件职责

| 文件 | 职责 |
| :--- | :--- |
| `skillsync*` | CLI：`update` / `discover` / `sync` / `status` / `version` |
| `config/interests.json` | `discover` 的兴趣主题（决定搜什么） |
| `config/sources.json` | 每个 skill → GitHub repo + 子路径(subpath) + `pinned` 标志（内嵌于 `skillsync.py` 的 `SOURCES` 为兜底） |
| `tools/` | 给其他 Coding 软件的符号链接/配置脚本（`.sh` + `.ps1`） |
| `CATALOG.md` | 技能清单（功能/命令/更新记录） |

## 3. 常用命令

```bash
python skillsync.py update --dry-run   # 只报告有哪些可更新，不改动
python skillsync.py update             # 更新非 pinned 且有上游更新的技能 + 提交
python skillsync.py discover --top 20  # 列出 20 个候选高星相关技能
python skillsync.py sync               # 提交并 push 到 origin/main
python skillsync.py status             # 各技能 本地基线 vs 上游最新 / pinned / 待更新
```

## 4. 数据来源（sources 映射，维护要点）

| 技能 | 上游 repo | subpath | pinned | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| a-stock-data | simonlin1212/a-stock-data | （根） | 否 | |
| agent-reach | Panniantong/Agent-Reach | `agent_reach/skill` | 否 | 上游结构已变，只取子目录 |
| frontend-design | anthropics/skills | `skills/frontend-design` | 否 | |
| grill-me | mattpocock/skills | （根，已本地合并） | **是** | 本地移植版，勿覆盖 |
| Humanizer-zh | op7418/Humanizer-zh | （根） | 否 | |
| impeccable | pbakaus/impeccable | （根） | 否 | 含 tests/gallery，文件多但非垃圾 |
| InvestSkill | yennanliu/InvestSkill | （根） | 否 | SKILL.md 嵌套在 plugins 下 |
| last30days | mvanhorn/last30days-skill | （根） | 否 | |
| last30days-cn | Jesseovo/last30days-skill-cn | （根） | 否 | 需 Playwright |
| serenity-skill | muxuuu/serenity-skill | （根） | 否 | |
| ui-ux-pro-max | nextlevelbuilder/ui-ux-pro-max-skill | （根） | 否 | |
| trading-skills | marian2js/trading-skills | （根） | **是** | 本地比上游新 |
| interface-design | Dammyjay93/interface-design | （根） | **是** | 本地比上游新 |
| gauss314-skills | gauss314/skills | （根） | **是** | 本地比上游新 |
| 其余无上游的技能 | — | — | — | dotnet-mod-recon（自建）、find-skills / gh-skill-installer / output-skill / yao-meta-skill（本地工具）等，无需更新 |

> 更新判定：GitHub API 取 repo 最近提交日期，与 `git log -1 --format=%ci -- <dir>` 本地基线比对；上游更新且非 pinned 时用 `codeload.github.com/.../tar.gz` 下载，解压对应 subpath 覆盖。

## 5. 约定与坑（重要）

1. **严禁覆盖 pinned 技能**：`trading-skills` / `interface-design` / `gauss314-skills`（本地较新）、`grill-me`（本地移植）。覆盖会降级或丢改造。
2. **`agent-reach` 子路径**：上游已把 skill 挪到 `agent_reach/skill/`，更新时只复制该子目录。
3. **更新 ≠ 必 bump 版本**：只有项目本体（脚本/结构/约定）变更才改 `VERSION` 与 `CHANGELOG.md`。
4. **README 合并冲突**：历史上根 README 出现过 `<<<<<<<` 冲突标记，已修复；改动时勿再引入。
5. **无垃圾公约**：下载/解压/缓存全部走仓库外系统缓存，用完清理；提交前 `git status --porcelain` 自检。
6. **不要未经确认 push**：`sync` 由用户触发；`update` 默认只更新+本地提交，不自动 push（或仅带 `--push`）。

## 6. 如何扩展

- **新增受管技能**：在 `config/sources.json` 加一行（folder, repo, subpath, pinned）；首次安装用 `gh-skill-installer` 或稀疏克隆，再纳入 git。注意 `skillsync.py` 内嵌的 `SOURCES` 是兜底，修改后两处需同步。
- **新增兴趣分类**：编辑 `config/interests.json`（见下）。
- **新增 Coding 工具支持**：在 `tools/` 加对应软链脚本，并在 `README.md` 第 5 节补一行。

## 7. 不要做的事

- ❌ 把临时文件 / 日志 / 缓存 / `node_modules` / `build` / `dist` 写进仓库根。
- ❌ 覆盖任何 `pinned` 技能。
- ❌ 未经确认 `git push`。
- ❌ 为「干净」删除还在用的技能目录（删除需用户确认）。
- ❌ 在 README 引入合并冲突标记。

## 8. 兴趣主题基线（discover 用，建议在 `config/interests.yaml` 维护）

- `web/前端设计`：frontend-design, ui, ux, tailwind, shadcn, design-system, animation, figma
- `投研/金融`：stock, investing, finance, trading, quant, a-share, valuation, research
- `中文内容`：chinese, nlp, writing, humanize, prompt
- `agent/工具`：agent, skill, claude-skill, cursor, workflow, automation
- `生产力`：productivity, note, knowledge, search
