---
name: find-skills
description: >
  Discover, search, and introspect skills in your local AI Skills Hub.
  Use when you need to know which skills are available, what a specific
  skill does, which skill to use for a given task, or how skills are organized.

  Triggers: "which skill", "find skill", "what skills", "技能推荐",
  "search skills", "list skills", "skill search", "技能搜索", "查看技能"
triggers:
  - discover: 找技能/哪个技能/技能推荐/有什么技能/查看技能/which skill/what skills/list skills
  - search: 搜索技能/技能搜索/search skills/find skill
  - introspect: 技能详情/skill details/技能说明/skill readme
metadata:
  hub: D:\AI SKILLS
---

# Find Skills — 本地技能发现器

帮助你在 AI Skills Hub 中快速找到合适的技能。

## Hub 根路径

```
D:\AI SKILLS
```

## 技能查询方法

### 1. 列出所有技能

```powershell
Get-ChildItem "D:\AI SKILLS" -Directory |
  Where-Object { $_.Name -notmatch '^\.git$' } |
  Select-Object -ExpandProperty Name
```

### 2. 查看技能详情

```powershell
Get-Content "D:\AI SKILLS\<skill-name>\SKILL.md" -Encoding UTF8
```

### 3. 按关键字搜索技能

```powershell
Select-String -Path "D:\AI SKILLS\*\SKILL.md" -Pattern "关键字" -SimpleMatch
```

### 4. 从 README 获取技能速查表

```powershell
Get-Content "D:\AI SKILLS\README.md" -Encoding UTF8
```

## 使用场景

| 用户需求 | 推荐操作 |
|---------|---------|
| 想新建落地页 | 查找 imagegen / taste 相关技能 |
| 想重设计项目 | 查找 redesign / impeccable 技能 |
| 需要中文文案润色 | 查找 Humanizer 技能 |
| 需要前端动效 | 查找 gsap / impeccable animate 技能 |
| 需要提取网页内容 | 查找 agent-reach 技能 |
| 不知道用什么技能 | 列出所有技能并查看描述 |
