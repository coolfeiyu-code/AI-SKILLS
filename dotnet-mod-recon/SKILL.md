---
name: dotnet-mod-recon
description: 只读逆向分析 .NET / Unity BepInEx Mod 的架构与实现原理（有 ilspycmd 优先反编译拿签名，无则 Python 提取符号）。当用户要求"研究/分析/看看这个 mod / 这个 DLL 怎么实现的 / 某功能是怎么做出来的"，且目标是 .NET 程序集（.dll）、BepInEx 插件目录或 Unity 游戏 Mod 时使用。也适用于只读勘察游戏/软件的运行时数据目录（SQLite 库、配置、缓存、回放文件）。
agent_created: true
---

# .NET / BepInEx Mod 只读逆向勘察

能用 `ilspycmd`（本机已装全局 dotnet tool）时**优先反编译**：直接拿确切方法签名、IL 与 `[HarmonyPatch]` 目标类型，远比纯符号准。没有反编译器时，才用 Python + 正则从元数据堆里提取符号做架构级还原。准确率对"架构级问题"足够高。

## 铁律

1. **默认只读。** 用户说"不要改动"时尤其严格：不写入、不删除、不让工具产生副作用文件。
2. **读 SQLite 必须先复制副本。** 直接打开会生成 `-wal` / `-shm` / `-journal` 污染原目录。
3. **先验证再下结论。** 符号名是证据，不要凭功能猜实现。找不到证据就说找不到。

## 环境注意（Windows / Git Bash）

- Python 用托管版绝对路径，例如 `C:/Users/<user>/.workbuddy/binaries/python/versions/3.13.12/python.exe`。
- Git Bash 的 `/tmp` **Python 无法识别**，临时文件一律用 Windows 绝对路径。
- 路径含空格必须加引号。

## 步骤

### 1. 摸清盘面

```bash
ls -la "<目标目录>"
ls -la "<游戏根>/BepInEx/plugins"     # 插件本体在这里，不在数据目录
cat  "<游戏根>/BepInEx/config/*.cfg"  # 配置项自带注释，是最好的功能清单
head -60 "<游戏根>/BepInEx/LogOutput.log"  # 启动日志直接列出加载的插件和 patch 名
```

配置文件的 `##` 注释行往往把每个功能解释得比任何文档都清楚，优先读。

### 2. 提取程序集符号

两个堆分别用不同正则：

```python
import re
d = open('Target.dll','rb').read()

# #Strings 堆 —— 类型名/方法名/字段名，UTF-8 单字节
ids = set(x.decode('ascii') for x in re.findall(rb'[A-Za-z_][A-Za-z0-9_`<>.]{3,90}', d))

# #US 堆 —— 用户字符串（URL、日志事件、UI 文案），UTF-16LE
us = set(x.decode('utf-16le') for x in re.findall(rb'(?:[\x20-\x7e]\x00){5,}', d))

# 中文 UI 文案
cn = set()
for m in re.finditer(rb'((?:.[\x4e-\x9f]){2,40})', d, re.S):
    try: s = m.group(1).decode('utf-16le')
    except: continue
    if all('\u4e00' <= c <= '\u9fff' for c in s): cn.add(s)
```

### 2b. 有 ilspycmd 时优先反编译（拿确切签名）

纯符号只能到类名级别，拿不到方法签名和 IL。本环境 `ilspycmd` 10.1 已全局安装，直接反编译：

```bash
ilspycmd "<dll>" -l c > types.txt            # 列出所有 class（c/i/s/d/e 过滤实体类型）
ilspycmd "<dll>" -t "Namespace.Type" > t.cs  # 反编译单个类型（C#）
ilspycmd "<dll>" -t "Ns.Type" -il            # 只要 IL
```

要点：
- 游戏本体的 managed 程序集通常在 `<游戏根>/<Game>_Data/Managed/`（如 `TheBazaarRuntime.dll`、`Assembly-CSharp.dll`）。插件 DLL 与游戏 DLL 分开，原生类型/方法要去游戏 DLL 里找。
- 想看模组 hook 了哪个原生方法，反编译对应的 `*Patch` 类，读 `[HarmonyPatch(typeof(NativeType), "MethodName")]` 与 Postfix 参数 —— 这直接给出**确切的原生签名**，是最稳的 hook 锚点证据。
- 确认"某功能是否按状态变化重算"：反编译宿主 Controller，找触发方法（如 `Open()` / `OnStateChanged`），看它读的是实时快照还是缓存。符号推断在这里最容易翻车，必须以 IL 为准。

### 3. 按线索追问

| 想知道 | 过滤什么 |
|---|---|
| 模块划分 | 以 `<产品名>.` 开头的完整命名空间 |
| Hook 了游戏什么 | 宿主命名空间（如 `BazaarGameShared.*`）+ 以 `Patch` 结尾的类名 |
| 数据从哪来 | `*Event` / `*Message` / `*Reader` / `*Subscription` |
| 算法思路 | `*Aggregator` / `*Projector` / `*Accumulator` / `*Attribution` / `*Resolver` |
| 网络行为 | `http` 开头的串、`/api`、域名片段 |
| 功能全景 | 形如 `xxx.yyy.zzz` 的小写点分日志事件名，一个前缀 = 一个功能模块 |
| UI 长什么样 | 中文/英文文案串、USS/class 名 |

命名是最强的信号：`ImpactTransitionClaim` + `IsClaimedByAnotherExecution` 就说明作者在防重复归因；`periodic-impact-v6` 说明这套方案迭代过 6 版。

### Hook 可行性快速评估

用户问"能不能 hook 某功能"时，先测绘现有 hook 面再下结论：

1. **枚举 Harmony patch**：`grep -n "Patch\b" strings.txt`。patch 类名（`XxxTooltipPatch` / `YyyShowPatch`）直接暴露模组已经 patch 了哪些原生 UI —— 这些就是"已验证可稳 hook"的目标，新功能优先复用同族模式。
2. **枚举原生 Controller**：`grep -n "Controller" strings.txt`。`*VisualController` / `*TooltipController` 是注入 UI 的候选锚点。
3. **判断确定性**：
   - 数据侧：找模组内部持有的运行时状态字段（如 `_recommendations` / `_matches` / `_liveSnapshot`），反射读取即可，零新逻辑 → 确定性最高。
   - UI 侧：`*TooltipPatch` 系列最稳（只往 tooltip 追加文本，不碰布局）；patch 原生视觉/列表布局方法风险最高，且依赖游戏版本、签名易变。
4. 唯一必须 IL 确认的是"具体原生方法签名"；符号名只能给到类名级别。

### 4. 只读查 SQLite

```bash
cp "<原库>" "<工作区>/tmp/copy.db"
```
```python
sqlite3.connect('file:C:/绝对路径/copy.db?mode=ro', uri=True)   # 必须 Windows 绝对路径
```
先 `sqlite_master` 看建表语句（CHECK 约束和索引会暴露业务规则），再 `count(*)`，最后抽样。用完删副本。

### 5. 交付

用流程图讲清数据链路，再用文字补细节。附上关键符号名作为证据，读者可自行复核。涉及上传/账号/隐私的配置项要主动点出来。

## 反面清单

- 不要拿 `strings` 命令糊弄，UTF-16 串会全部丢失。
- 不要把混淆后的编译器生成名（`<Xxx>b__0_1`、`k__BackingField`）当业务符号讲。
- 不要在没看到证据时描述"它应该是这样实现的"。
