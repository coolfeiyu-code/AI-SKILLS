# 🛠️ 我的本地 AI 技能外挂库 (Personal AI Skills Hub)

当前已本地化存储的顶级 AI 规范，开新项目时可让 Codex 直接复制对应文件夹。

| 文件夹名称 | 技能中文标签 | 核心功用 | 常用激活命令 |
| :--- | :--- | :--- | :--- |
| `a-stock-data` | **A股全栈数据工具包** | 27 个端点覆盖行情(mootdx+腾讯+百度K线)、研报(东财+同花顺+iwencai)、信号(热点+北向+龙虎榜+解禁+行业)、资金面(融资融券+大宗+股东户数+分红+资金流)、新闻公告、财报三表、F10、巨潮公告 | `帮我估一下 688017 PE/PEG` / `今天哪些股票走强` / `这个人形机器人研报` |
| `agent-reach` | **互联网平台路由器** | 17 平台工具集合，支持搜索/阅读社交/招聘/开发/网页/视频，零配置 8 渠道 | `$agent-reach` / `搜一下` / `读这个链接` |
| `impeccable` | **前端视觉判官** | 像素级审查，干掉AI塑料感审美，死磕色彩间距排版动效，附带 critique / audit / polish / craft 全套子命令 | `$impeccable critique` / `$impeccable polish` |
| `brandkit` | **品牌视觉生成器** | 生成高端品牌指南板、Logo系统、视觉身份套件、品牌色板 | `用 brandkit 生成品牌规范` |
| `brutalist-skill` | **工业布鲁塔尔 UI** | 裸露机械感界面，瑞士字体排印 + 军事终端美学，刚硬网格、极端字号对比 | `用 brutalist 风格做一个仪表盘` |
| `design-system` | **设计 Token 架构** | 三层 token（primitive→semantic→component）、CSS 变量、间距/排版标度、组件规格、策略幻灯片生成 | `生成 design tokens` / `做个品牌演示` |
| `find-skills` | **本地技能发现器** | 快速搜索和发现 AI Skills Hub 中安装的技能，按需推荐合适的技能组合 | `有什么技能` / `找技能` / `find skill` |
| `frontend-design` | **Anthropic 官方前端设计** | 官方审美方向指导：大胆排版、禁用 AI 套路字体(Inter/Roboto/Space Grotesk)、非对称构图、有意动效、CSS 变量调色板 | UI 任务自动触发 / `用 frontend-design 做一个落地页` |
| `gauss314-skills` | **全球行情/回测数据层** | 30+ 数据源技能：Yahoo / Google Finance / Finviz / Alpha Vantage / FRED 宏观 / Alpaca 交易 / 回测，覆盖美股与全球行情、筛选、组合优化 | `用 gauss314 拉 yahoo 行情` / `回测这个策略` |
| `gpt-tasteskill` | **GSAP 动效大师** | 精准 GSAP ScrollTrigger 动效、视差滚动、弹性交互动画、AIDA 页面结构 | `用 gpt-taste 做一个带动效的落地页` |
| `gh-skill-installer` | **GitHub 技能安装器** | 搜索 GitHub → 稀疏克隆 → 安全审计 → 安装到技能库的复用流程，自动跳过已装/重叠项 | `从 GitHub 装个 UI skill` |
| `high-end-visual-design` | **高端视觉规范** | 定义字体、间距、阴影、卡片结构、动效的"昂贵感"标准，封杀廉价默认值 | `用高端视觉规范审查这个页面` |
| `interface-design` | **跨会话一致 UI 工艺** | 仪表盘/SaaS/工具类产品的工艺优先设计，token/状态/视觉方向一致，跨会话持久（`.interface-design/system.md`） | `审查这个后台的 UI` |
| `image-to-code` | **设计图转代码** | 先生成设计参考图，再逐像素还原成可运行的网页代码 | `用 image-to-code 实现这个设计` |
| `imagegen-frontend-mobile` | **移动端界面生成** | 生成 iOS/Android 应用界面概念图，手机 mockup 框架，多屏一致性 | `生成移动端设置页面设计图` |
| `imagegen-frontend-web` | **Web 设计参考图** | 逐 section 生成横版设计参考图，构图多样化，统一色板 | `为落地页每个 section 生成设计图` |
| `InvestSkill` | **美股深度研究套件** | Claude Code plugin 式美股分析：10-K 解读、DCF 估值、基本面/竞品/行业地图、财报电话会、空头论证(bear-case)、完整研报、组合复盘等 20+ 子技能 | `用 InvestSkill 做完整研报` / `bear-case` |
| `minimalist-skill` | **极简编辑风格** | 温暖单色、排版对比、扁平 bento 网格、柔粉色，无渐变无重阴影 | `用 minimalist 风格重做这个页面` |
| `last30days` | **多源热点研究器** | 搜索 Reddit / X / YouTube / TikTok / Hacker News / Polymarket / GitHub / 网页，汇总近 30 天内人们关于任意话题的真实讨论，附来源引用 | `$last30days <话题>` |
| `last30days-cn` | **中文平台热点追踪** | last30days 中文专属版本，8 大中文平台搜索（微博/小红书/抖音/B站/知乎/微信/百度/头条），Playwright 浏览器引擎深度抓取 | `搜下 A股 <话题>` / `看看最近 <话题>` |
| `output-skill` | **完整代码输出器** | 强制完整代码输出，禁止占位符，处理 token 上限拆分 | 自动生效（用于需要完整输出的任务） |
| `redesign-skill` | **存量项目重设计** | 审计现有设计，识别 AI 通用模式，升级到高端标准而不破坏功能 | `用 redesign 升级这个项目的 UI` |
| `stitch-skill` | **Google Stitch 设计系统** | 生成 agent 友好的 DESIGN.md，强制高端反通用 UI 标准 | `为项目生成 Stitch 设计系统文档` |
| `taste-skill` | **反套路前端设计 v2** | 强制真随机布局、AIDA 结构、宽幅排版、GSAP ScrollTrigger，反 AI 模板化 | `用 taste-skill 做一个不AI味的落地页` |
| `Humanizer-zh` | **中文内容人性化** | 将 AI 生成的中文内容改写为自然人类风格，消除机器味 | `用 Humanizer 改写这段文字` |
| `seedance-prompt` | **AI视频真实感提示词** | 为 Seedance/Sora/Kling/Runway/Veo 生成去 AI 感、纪录片质感的结构化视频提示词，内置设备美学缺陷包(DV/VHS/Super 8/手机/监控)、氛围翻译表、去 AI 感自检清单 | `纽约街头早晨，真实手机随拍感` / `帮我把视频 prompt 改得更真实` |
| `serenity-skill` | **供应链瓶颈投研** | 将 AI 转为供应链瓶颈猎手，溯源投研、产业链映射、股票筛选、逻辑压力测试 | `用 Serenity 的方式看` / `深度调研` / `产业链瓶颈` |
| `Ultimate-AI-Skill-Library` | **终极 AI 技能总库** | 17 个规则文件覆盖需求/架构/编码/审查/调试/HTML/Godot/插件/资源/UI/性能/QA，适配 WorkBuddy·ChatGPT Projects·Cursor·Claude Code·Codex | `请读取 Skills 文件夹中的全部规则，整个项目严格遵守` |
| `ui-styling` | **shadcn/Tailwind 组件样式** | shadcn/ui（Radix+Tailwind）可访问组件、Tailwind 工具类、canvas 视觉设计、暗色模式 | `用 ui-styling 搭一个后台` |
| `ui-ux-pro-max` | **UI/UX 设计情报库** | 可搜索本地数据库 84 风格 / 192 配色 / 74 字体组合 / 98 UX 指南 / 16 GSAP 动效 / 22 技术栈，自动生成设计系统 | UI 任务自动触发 / `做一个 fintech 仪表盘` |
| `trading-skills` | **交易纪律工作流** | 事前检查 / 论点验证 / 仓位 sizing / 风险收益 sanity / 盘后复盘，覆盖 idea 发现→构建→执行→复盘全链路（pre-trade-check、thesis-validation、position-sizing…） | `pre-trade-check` / `position-sizing` |
| `yao-meta-skill` | **技能自举元技能** | 从工作流/提示词/对话/文档中创建、重构、评估、打包 agent 技能，用于技能沉淀与团队分发 | `把这个流程做成 skill` |

## 📋 按场景速查

| 场景 | 推荐技能组合 |
| :--- | :--- |
| **新建落地页** | `imagegen-frontend-web` → `image-to-code` → `impeccable polish` |
| **重设计现有项目** | `redesign-skill` → `impeccable critique` → `impeccable craft` |
| **移动端 App UI** | `imagegen-frontend-mobile` → `image-to-code` |
| **品牌/Logo/身份** | `brandkit` → `stitch-skill` |
| **纯动效页面** | `gpt-tasteskill` + `impeccable animate` |
| **仪表盘/后台** | `brutalist-skill` 或 `minimalist-skill` |
| **A股数据查询** | `a-stock-data` → 直接说股票代码+问题 |
| **中文文案润色** | `Humanizer-zh` |
| **通用视觉提升** | `high-end-visual-design` → `impeccable polish` |
| **网页/社交内容获取** | `agent-reach` → 搜索/阅读各平台内容 |
| **不知用什么技能** | `find-skills` → 搜索和发现推荐 |
| **研究/热点追踪** | `$last30days <话题>` → 多平台近30天讨论汇总（海外平台） / `$last30days-cn <话题>` → 中文平台近30天讨论（微博/B站/知乎/小红书等） |
| **投资研究/产业链分析** | `serenity-skill` → 深度产业链调研、瓶颈识别、股票排序 |

## 🔄 更新记录

- **2026-07-20** 新增 5 个 GitHub 热门 UI 设计 skill（安全审计 P2 通过）：`frontend-design`（Anthropic 官方，277K+ 安装）、`ui-ux-pro-max` / `ui-styling` / `design-system`（nextlevelbuilder，#1 社区 88.7k★）、`interface-design`（Dammyjay93，5k★）；并新增 `gh-skill-installer`（GitHub 技能搜索→克隆→审计→安装复用流程）。来源：github.com/anthropics/skills、github.com/nextlevelbuilder/ui-ux-pro-max-skill、github.com/Dammyjay93/interface-design
- **2026-07-20** README 与目录对齐：补列 `InvestSkill` / `gauss314-skills` / `trading-skills` / `yao-meta-skill`（目录有但原表未列）；移除 `taste-skill-v1`（目录已无对应文件夹）。注：`high-end-visual-design` 与 `soft-skill` 为同一技能（文件夹名 soft-skill、技能名 high-end-visual-design），`image-to-code` 对应文件夹 `image-to-code-skill`，均保留。
- **2026-07-20** 新增 `last30days-cn`（来源: github.com/Jesseovo/last30days-skill-cn），中文平台热点追踪技能（微博/B站/知乎/小红书/抖音/微信/百度/头条），需 Playwright Chromium 引擎；新增 `seedance-prompt`（来源: github.com/zhouwei713/seedance-prompt），AI视频真实感提示词技能
- **2026-07-07** 新增 `Ultimate-AI-Skill-Library`，通用 AI 技能总库（17 个规则文件），已安装至 `~/.workbuddy/skills/ultimate-ai-skill-library/`，并设为全局默认项目规范
- **2026-06-15** 新增 `a-stock-data`（来源: github.com/simonlin1212/a-stock-data），A股全栈数据工具包
- **2026-06-12** 新增 `serenity-skill`（来源: github.com/muxuuu/serenity-skill），供应链瓶颈投研技能
- **2026-06-09** 新增 `agent-reach`（来源: github.com/Panniantong/Agent-Reach）、`find-skills`（本地技能发现器）和 `last30days`（来源: github.com/mvanhorn/last30days-skill），更新 README 结构
- **2026-06-08** 初始建立，收录 15 个技能
- `impeccable` 通过 git sparse checkout 安装（来源: pbakaus/impeccable）
- `Humanizer-zh` 通过 git sparse checkout 安装（来源: op7418/Humanizer-zh）
- 其余为 Codex curated list 安装

## 📈 推票 / 投研技能栈（2026-07 增补）

面向「研究后推荐候选标的」而不是自动下单。组合逻辑：

| 层级 | 技能来源 | 干什么 |
| :--- | :--- | :--- |
| A股数据 | `a-stock-data` | 行情/估值/资金/龙虎榜/公告（拉数） |
| 产业链 | `serenity-skill` | 瓶颈/卡点/主题优先研究名单 |
| 分析框架 | `InvestSkill`（`stock-eval`/`stock-screener`/`full-report`/`bear-case`…） | 质量分、筛选排名、完整报告、空方压力测试 |
| 决策纪律 | `trading-skills`（`pre-trade-check`/`thesis-validation`/`position-sizing`…） | 推之前做 go/no-go、证伪、仓位与组合风险 |
| 全球数据 | `gauss314-skills` 精选（yahoo/tradingview/finviz/google-finance/portfolio…） | 美股/全球行情、筛选、组合优化、回测 |
| 舆情补充 | `last30days` | 近30天多平台真实讨论（非行情） |

**推荐推票流水线：** `serenity` 或 主题 → `a-stock-data`/`yahoo-finance` 拉数 → `stock-screener`/`stock-eval` 排名 → `bear-case`+`thesis-validation` 证伪 → `pre-trade-check`+`position-sizing` 才输出候选。

本地路径：
- `D:\AI-SKILLS\trading-skills` ← https://github.com/marian2js/trading-skills
- `D:\AI-SKILLS\InvestSkill` ← https://github.com/yennanliu/InvestSkill
- `D:\AI-SKILLS\gauss314-skills` ← https://github.com/gauss314/skills

