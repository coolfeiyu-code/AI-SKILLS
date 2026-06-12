# 🛠️ 我的本地 AI 技能外挂库 (Personal AI Skills Hub)

当前已本地化存储的顶级 AI 规范，开新项目时可让 Codex 直接复制对应文件夹。

| 文件夹名称 | 技能中文标签 | 核心功用 | 常用激活命令 |
| :--- | :--- | :--- | :--- |
| `agent-reach` | **互联网平台路由器** | 17 平台工具集合，支持搜索/阅读社交/招聘/开发/网页/视频，零配置 8 渠道 | `$agent-reach` / `搜一下` / `读这个链接` |
| `impeccable` | **前端视觉判官** | 像素级审查，干掉AI塑料感审美，死磕色彩间距排版动效，附带 critique / audit / polish / craft 全套子命令 | `$impeccable critique` / `$impeccable polish` |
| `brandkit` | **品牌视觉生成器** | 生成高端品牌指南板、Logo系统、视觉身份套件、品牌色板 | `用 brandkit 生成品牌规范` |
| `brutalist-skill` | **工业布鲁塔尔 UI** | 裸露机械感界面，瑞士字体排印 + 军事终端美学，刚硬网格、极端字号对比 | `用 brutalist 风格做一个仪表盘` |
| `find-skills` | **本地技能发现器** | 快速搜索和发现 AI Skills Hub 中安装的技能，按需推荐合适的技能组合 | `有什么技能` / `找技能` / `find skill` |
| `gpt-tasteskill` | **GSAP 动效大师** | 精准 GSAP ScrollTrigger 动效、视差滚动、弹性交互动画、AIDA 页面结构 | `用 gpt-taste 做一个带动效的落地页` |
| `high-end-visual-design` | **高端视觉规范** | 定义字体、间距、阴影、卡片结构、动效的"昂贵感"标准，封杀廉价默认值 | `用高端视觉规范审查这个页面` |
| `image-to-code` | **设计图转代码** | 先生成设计参考图，再逐像素还原成可运行的网页代码 | `用 image-to-code 实现这个设计` |
| `imagegen-frontend-mobile` | **移动端界面生成** | 生成 iOS/Android 应用界面概念图，手机 mockup 框架，多屏一致性 | `生成移动端设置页面设计图` |
| `imagegen-frontend-web` | **Web 设计参考图** | 逐 section 生成横版设计参考图，构图多样化，统一色板 | `为落地页每个 section 生成设计图` |
| `minimalist-skill` | **极简编辑风格** | 温暖单色、排版对比、扁平 bento 网格、柔粉色，无渐变无重阴影 | `用 minimalist 风格重做这个页面` |
| `last30days` | **多源热点研究器** | 搜索 Reddit / X / YouTube / TikTok / Hacker News / Polymarket / GitHub / 网页，汇总近 30 天内人们关于任意话题的真实讨论，附来源引用 | `$last30days <话题>` |
| `output-skill` | **完整代码输出器** | 强制完整代码输出，禁止占位符，处理 token 上限拆分 | 自动生效（用于需要完整输出的任务） |
| `redesign-skill` | **存量项目重设计** | 审计现有设计，识别 AI 通用模式，升级到高端标准而不破坏功能 | `用 redesign 升级这个项目的 UI` |
| `stitch-skill` | **Google Stitch 设计系统** | 生成 agent 友好的 DESIGN.md，强制高端反通用 UI 标准 | `为项目生成 Stitch 设计系统文档` |
| `taste-skill` | **反套路前端设计 v2** | 强制真随机布局、AIDA 结构、宽幅排版、GSAP ScrollTrigger，反 AI 模板化 | `用 taste-skill 做一个不AI味的落地页` |
| `taste-skill-v1` | **反套路前端 v1** | v2 的旧版，保留用于需要精确向后兼容的项目 | 同 taste-skill |
| `Humanizer-zh` | **中文内容人性化** | 将 AI 生成的中文内容改写为自然人类风格，消除机器味 | `用 Humanizer 改写这段文字` |
| `serenity-skill` | **供应链瓶颈投研** | 将 AI 转为供应链瓶颈猎手，溯源投研、产业链映射、股票筛选、逻辑压力测试 | `用 Serenity 的方式看` / `深度调研` / `产业链瓶颈` |

## 📋 按场景速查

| 场景 | 推荐技能组合 |
| :--- | :--- |
| **新建落地页** | `imagegen-frontend-web` → `image-to-code` → `impeccable polish` |
| **重设计现有项目** | `redesign-skill` → `impeccable critique` → `impeccable craft` |
| **移动端 App UI** | `imagegen-frontend-mobile` → `image-to-code` |
| **品牌/Logo/身份** | `brandkit` → `stitch-skill` |
| **纯动效页面** | `gpt-tasteskill` + `impeccable animate` |
| **仪表盘/后台** | `brutalist-skill` 或 `minimalist-skill` |
| **中文文案润色** | `Humanizer-zh` |
| **通用视觉提升** | `high-end-visual-design` → `impeccable polish` |
| **网页/社交内容获取** | `agent-reach` → 搜索/阅读各平台内容 |
| **不知用什么技能** | `find-skills` → 搜索和发现推荐 |
| **研究/热点追踪** | `$last30days <话题>` → 多平台近30天讨论汇总 |
| **投资研究/产业链分析** | `serenity-skill` → 深度产业链调研、瓶颈识别、股票排序 |

## 🔄 更新记录

- **2026-06-12** 新增 `serenity-skill`（来源: github.com/muxuuu/serenity-skill），供应链瓶颈投研技能
- **2026-06-09** 新增 `agent-reach`（来源: github.com/Panniantong/Agent-Reach）、`find-skills`（本地技能发现器）和 `last30days`（来源: github.com/mvanhorn/last30days-skill），更新 README 结构
- **2026-06-08** 初始建立，收录 15 个技能
- `impeccable` 通过 git sparse checkout 安装（来源: pbakaus/impeccable）
- `Humanizer-zh` 通过 git sparse checkout 安装（来源: op7418/Humanizer-zh）
- 其余为 Codex curated list 安装
