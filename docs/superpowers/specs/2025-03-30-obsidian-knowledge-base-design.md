# Obsidian 知识库管理技能设计文档

## 1. 项目概述

### 1.1 技能名称
`obsidian-knowledge-base`

### 1.2 技能描述
为 Claude Code、OpenClaude 等 AI Agent 提供标准化的 Obsidian 知识库管理能力。通过封装 Obsidian CLI 命令，实现 PARA 方法（Projects, Areas, Resources, Archives）的完整知识管理工作流。

### 1.3 核心目标
- 将零散的想法转化为结构化项目
- 建立笔记之间的双向链接
- 自动化归档和知识整理
- 提供知识库健康度检查
- 支持自然语言意图识别

### 1.4 设计理念
- **标准化工作流程**：每个操作都有明确的步骤和输出
- **渐进式处理**：从收件箱 → 项目/研究 → 知识库 → 归档
- **链接优先**：通过双向链接建立知识网络
- **用户可控**：关键决策点询问用户确认

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Obsidian 知识库技能                   │
│                      (Python Skill)                      │
├─────────────────────────────────────────────────────────┤
│  命令层                                                   │
│  ├── /start-my-day    →  每日规划工作流                    │
│  ├── /kickoff         →  项目启动工作流                    │
│  ├── /research        →  研究笔记工作流                    │
│  ├── /brainstorm      →  头脑风暴工作流                    │
│  ├── /archive         →  归档工作流                      │
│  ├── /ask             →  快速查询工作流                  │
│  ├── /review          →  知识库回顾                      │
│  ├── /health-check    →  健康检查                        │
│  ├── /mocs            →  MOC 管理                        │
│  ├── /moc-review      →  MOC 维护                        │
│  └── obsidian CLI     →  通用钩子（执行 obsidian --help）│
├─────────────────────────────────────────────────────────┤
│  工具层                                                   │
│  ├── workflows/       - Python 工作流模块                │
│  ├── utils/           - 工具函数（ID生成、Frontmatter等）│
│  └── vault.py         - Obsidian CLI 封装                │
├─────────────────────────────────────────────────────────┤
│  模板层                                                 │
│  └── 99_模板/                                        │
│      ├── 项目启动模板.md                               │
│      ├── 研究笔记模板.md                                 │
│      ├── 头脑风暴模板.md                               │
│      ├── 每日规划模板.md                               │
│      └── MOC 模板.md                                   │
├─────────────────────────────────────────────────────────┤
│  数据层                                                   │
│  └── /Volumes/SSD/ObsidianVault/                          │
│      ├── 00_收件箱/                                    │
│      ├── 10_项目/                                      │
│      ├── 20_领域/                                      │
│      ├── 30_研究/                                      │
│      ├── 40_知识库/                                    │
│      ├── 50_归档/                                      │
│      ├── 99_模板/                                      │
│      ├── metadata/                                     │
│      │   └── backups/                                  │
│      └── Daily/                                        │
└─────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

**核心语言**: Python 3.8+
- **理由**: 支持 AST 解析、复杂 JSON 处理、类型安全

**主要依赖**:
- `markdown-it-py` - Markdown AST 解析（第 9.5 节要求）
- `pydantic` - JSON Schema 验证（第 9.6 节要求）
- `pyyaml` - YAML 处理
- `click` - CLI 框架

**外部工具**:
- `obsidian` CLI 工具 - 与 Obsidian 通信

**Agent 接口**:
- Bash 脚本作为薄封装（如果 Agent 只支持 Bash）
- 实际调用 Python 模块

**架构示意**:
```
Agent (Bash hook)
    ↓
bin/obsidian-kb (Bash wrapper)
    ↓
python -m obsidian_kb.cli (Python核心)
    ↓
obsidian CLI / 文件系统
```

---

## 3. 数据层设计

### 3.1 文件夹结构

```
/Volumes/SSD/ObsidianVault/
├── 00_收件箱/                    # 临时笔记、快速记录
│   └── （平铺，无子文件夹）
│
├── 10_项目/                      # 进行中的项目
│   └── <领域>/                   # 按领域分组
│       ├── <项目名>.md
│       └── <项目名>_头脑风暴_<日期>.md
│
├── 20_领域/                    # 责任领域（Areas）
│   └── <领域名>/
│       └── （领域相关笔记）
│
├── 30_研究/                    # 研究笔记、学习资料
│   └── <领域>/                 # 按主题分组
│       └── <研究主题>_<日期>.md
│
├── 40_知识库/                  # 整理后的永久笔记
│   ├── moc/                    # 内容地图（MOC）- 用户导航入口
│   │   └── moc-<领域>.md       # 如: moc-编程.md, moc-工作.md
│   └── <类别>/                 # 按类别分组
│       └── <笔记名>.md
│
├── 50_归档/                    # 已完成的项目和旧笔记
│   └── YYYY-MM/                # 按月份分组
│       └── （归档笔记）
│
├── 99_模板/                  # 笔记模板
│   ├── 项目启动模板.md
│   ├── 研究笔记模板.md
│   ├── 头脑风暴模板.md
│   ├── 每日规划模板.md
│   └── MOC 模板.md
│
├── metadata/                   # 系统元数据（非用户内容）
│   ├── schema.md               # 数据结构定义
│   ├── tag-definitions.md      # 标签定义
│   ├── id-registry.json        # ID 注册表
│   └── backups/                # 自动备份
│
└── Daily/                      # 每日笔记
    └── YYYY-MM-DD.md
```

### 3.2 笔记 Frontmatter 标准（含唯一 ID）

所有笔记必须包含唯一 ID，用于稳定引用。

#### 通用字段（所有笔记类型）

```yaml
---
id: <唯一标识符>           # 格式: kb-YYYYMMDD-HHMMSS-XXXX
title: <标题>
type: <笔记类型>           # daily-note | project | research | brainstorm | moc | archive
date: YYYY-MM-DD
created: YYYY-MM-DD HH:MM
updated: YYYY-MM-DD HH:MM
tags: [标签1, 标签2]
---
```

#### 按类型的扩展字段

| 字段 | 类型 | 说明 | 适用笔记类型 |
|------|------|------|-------------|
| `status` | string | 进行中 / 已完成 / 已归档 / 待处理 | project, research |
| `area` | string | 所属领域 | project, research, brainstorm, moc |
| `mocs` | [string] | 关联的 MOC 列表 | project, research |
| `related_project` | string | 关联的项目（wiki 链接格式） | brainstorm |
| `inbox_count` | int | 收件箱数量 | daily-note |
| `active_projects` | int | 进行中项目数量 | daily-note |
| `todo_count` | int | 待办数量 | daily-note |

#### 各类型的完整 Frontmatter 示例

**project（项目）**:
```yaml
---
id: kb-20250330-143052-a3f9
title: AI 写作助手
type: project
date: 2025-03-30
created: 2025-03-30 14:30
updated: 2025-03-30 14:30
tags: [项目, 编程]
status: 进行中
area: 编程
mocs:
  - "moc-编程"
---
```

**research（研究）**:
```yaml
---
id: kb-20250330-143052-b7c2
title: Python 异步编程
type: research
date: 2025-03-30
created: 2025-03-30 14:30
updated: 2025-03-30 14:30
tags: [研究, 编程]
status: 进行中
area: 编程
mocs:
  - "moc-编程"
---
```

**brainstorm（头脑风暴）**:
```yaml
---
id: kb-20250330-143052-c8d3
title: 盈利模式 头脑风暴
type: brainstorm
date: 2025-03-30
created: 2025-03-30 14:30
updated: 2025-03-30 14:30
tags: [头脑风暴, 工作]
area: 工作
related_project: "[[AI 写作助手]]"
---
```

**moc（内容地图）**:
```yaml
---
id: kb-20250330-143052-d4e5
title: 编程 MOC
type: moc
date: 2025-03-30
created: 2025-03-30 14:30
updated: 2025-03-30 14:30
tags: [MOC, 编程]
area: 编程
---
```

**daily-note（每日规划）**:
```yaml
---
id: kb-20250330-143052-e5f6
title: 2025-03-30 每日规划
type: daily-note
date: 2025-03-30
created: 2025-03-30 08:00
tags: [每日规划]
inbox_count: 3
active_projects: 2
todo_count: 5
---
```

**archive（归档）**:
```yaml
---
id: kb-20250330-143052-f6g7
title: 已完成的项目名
type: archive
date: 2025-03-30
created: 2025-03-30 14:30
updated: 2025-03-30 14:30
tags: [已归档, 编程]
status: 已归档
---
```

**ID 生成规则**:
- 格式: `kb-YYYYMMDD-HHMMSS-<随机4位>` (日期时间 + 随机码)
- 示例: `kb-20250330-143052-a3f9`, `kb-20250330-143052-b7c2`
- 要求: 全库唯一，创建时自动生成，永不修改
- 优点: 并发安全，无需读取现有文件，时间戳可排序

**ID 与双链的使用策略**:

1. **ID 位置**: 仅存在于 YAML frontmatter（内部使用）
   ```yaml
   ---
   id: kb-20250330-143052-a3f9
   title: Python 装饰器详解
   ---
   ```

2. **正文双链**: 使用 Obsidian 标准格式（用户可读）
   ```markdown
   [[Python装饰器详解]]
   或带别名：
   [[Python装饰器详解|Python Decorator Guide]]
   ```

3. **ID 用途**:
   - Agent 内部维护知识图谱
   - 文件重命名/移动时追踪文件流向
   - Embedding 复用和去重
   - **不暴露在正文双链中**

4. **链接更新策略**:
   - 当文件移动/重命名时，通过 ID 找到所有引用该文件的笔记
   - 更新这些笔记中的双链路径（保持标题别名不变）
   - 示例：移动文件时，更新从 `[[旧路径/笔记|标题]]` 到 `[[新路径/笔记|标题]]`

**关键原则**:
- 用户看到的双链：**可读的文件名和标题**
- Agent 内部追踪：**不可见的 ID**
- 两者通过 frontmatter 中的 `id` 字段关联

**为什么必须 ID**:
- 文件名会改、标题会改、路径会移动
- 没有 ID 会导致引用断裂、双链失效
- ID 是知识图谱和 Embedding 复用的基础

### 3.3 MOC 结构

```markdown
---
type: moc
date: YYYY-MM-DD
created: YYYY-MM-DD HH:MM
updated: YYYY-MM-DD HH:MM
tags: [MOC, 领域]
---

# <领域> MOC

> 汇集所有<领域>相关的笔记、项目和资源

---

## 进行中的项目
- [[项目名]] #进行中

## 研究主题
- [[研究笔记]]

## 知识库
- [[知识笔记]]

## 待归档
- [[旧笔记]] #已完成

## 相关资源
- [外部链接](URL)

---

**统计:**
- 项目: X
- 研究: Y
- 知识: Z
- 总计: N
```

---

### 3.4 外部内容输入格式

当其他 skill 向 obsidian-kb 传递内容时，应使用以下标准格式：

**JSON 格式（推荐）**：
```json
{
  "source": "twitter|web|github|rss|local|skill",
  "source_url": "https://...",
  "title": "内容标题",
  "content": "正文内容",
  "author": "作者名（可选）",
  "date": "YYYY-MM-DD（可选）",
  "tags": ["可选标签"],
  "type_hint": "article|tutorial|snippet|knowledge（可选）",
  "area_hint": "建议领域（可选）"
}
```

**纯文本格式（简化）**：
```
标题: <第一行或提取>
正文: <剩余内容>
```

**Agent 处理规则**：

| 输入字段 | 处理方式 |
|---------|---------|
| `source` | 写入 frontmatter.source |
| `source_url` | 写入 frontmatter.source_url |
| `title` | 作为文件名和 frontmatter.title |
| `content` | 作为笔记正文 |
| `author` | 正文开头追加 `> 作者: @author` |
| `date` | 无则使用当前日期 |
| `tags` | 合入 frontmatter.tags |
| `type_hint` | 影响 Agent 的存放位置判断 |
| `area_hint` | 作为默认 area，用户可调整 |

**Skill 协作示例**：

```
reach-agent skill 返回:
{
  "source": "twitter",
  "source_url": "https://twitter.com/python_dev/status/123",
  "title": "Python Async Best Practices",
  "content": "完整文章内容...",
  "author": "@python_dev",
  "date": "2025-03-30"
}

obsidian-kb skill 接收:
→ 解析 JSON
→ 推断 type_hint=knowledge（内容完整、结构清晰）
→ 推断 area_hint=编程（内容包含 Python 关键词）
→ 询问用户确认存放位置
→ 创建笔记
```

---

## 4. 命令详细设计

### 4.1 `/start-my-day` 每日规划

**触发条件**:
- 用户直接调用: `/start-my-day`

**工作流程**:

1. **检查缓存**
   - 检查 `Daily/YYYY-MM-DD.md` 是否存在
   - 如果存在 → 读取现有内容，进入智能合并模式
   - 如果不存在 → 创建新笔记

2. **创建/读取每日笔记**
   - 使用模板: `99_模板/每日规划模板.md`
   - 初始化 frontmatter:
     ```yaml
     ---
     type: daily-note
     date: YYYY-MM-DD
     created: YYYY-MM-DD HH:MM
     inbox_count: 0
     active_projects: 0
     todo_count: 0
     ---
     ```

3. **扫描收件箱**
   - 执行: `obsidian files folder="00_收件箱"`
   - **限制**: 仅分析最近/最旧的 5 个笔记（避免 Token 溢出）
   - 如果收件箱笔记数 > 5 → 提示用户运行 `/review inbox`
   - 对 5 个笔记分别提取: frontmatter + 前 200 字符摘要
   - 按时间排序，给出处理建议
   - 统计：收件箱总数 X 个（超过 5 个的部分不分析）

4. **列出进行中的项目**
   - 执行: `obsidian search query="#进行中" path="10_项目"`
   - **限制**: 最多显示 10 个项目
   - 提取项目列表
   - 更新 frontmatter: `active_projects`

5. **提取今日待办**
   - 执行: `obsidian tasks todo path="Daily"`
   - 从所有笔记中提取未完成任务
   - 更新 frontmatter: `todo_count`

6. **生成建议**
   - AI 分析收件箱内容，给出处理建议
   - 分析进行中的项目，给出今日重点建议
   - 生成本日优先级排序

7. **智能合并**
   - 如果笔记已存在 → 在"今日规划"部分追加新内容
   - 保留用户已写的手动内容
   - 添加分隔线区分 AI 建议和用户内容

**输出示例**:
```
📅 2025-03-30 每日规划
━━━━━━━━━━━━━━━━━━━━
📥 收件箱待处理: 3 项
   - [[某个灵感想法]]（2天前）→ 建议 /kickoff
   - [[阅读笔记]]（昨天）→ 建议链接到相关 MOC
   - [[会议记录]]（昨天）→ 建议提取行动项

🚀 进行中项目: 2 个
   - [[Python 学习项目]] #进行中
   - [[网站重构]] #进行中

✅ 今日建议重点:
   1. 处理 [[会议记录]] → 提取行动项
   2. 继续 [[Python 学习项目]]
   3. 归档已完成的想法

💡 MOC 维护建议:
   - 建议将 [[阅读笔记]] 链接到 [[moc-编程]]

已更新: Daily/2025-03-30.md
```

**降级策略**:
- Obsidian CLI 不可用: 提示用户打开 Obsidian
- 无待处理事项: 生成"今日暂无待处理事项"

---

### 4.2 `/kickoff <想法名称>` 项目启动

**触发条件**:
- 用户直接调用: `/kickoff "想法名称"`

**工作流程**:

1. **查找原想法**
   - 在 `00_收件箱/` 搜索匹配的想法笔记
   - 如果找到多个 → 列出让用户选择
   - 如果没有找到 → 询问是否从空白创建

2. **询问项目详情**
   - 项目属于哪个领域？（A/B/C/D/其他）
   - 期望完成时间？（1周/1个月/3个月/长期）
   - 关键目标是什么？

3. **创建项目文档**
   - 在 `10_项目/<领域>/` 创建项目文档
   - 使用模板: `99_模板/项目启动模板.md`
   - 包含：目标、成功指标、阶段、时间线、资源、相关笔记链接

4. **归档原想法**
   - 将原想法笔记移动到 `50_归档/YYYY-MM/`
   - 在原位置创建链接指向新项目

5. **MOC 维护建议**
   - 询问是否链接到相关 MOC
   - 如果相关 MOC 不存在 → 询问是否创建

**输出示例**:
```
🚀 项目启动: AI写作助手
━━━━━━━━━━━━━━━━━━━━
从 [[00_收件箱/AI写作助手想法.md]] 创建项目...

✅ 已创建: 10_项目/编程/AI写作助手.md
📋 项目文档包含:
   - 目标: 开发 AI 写作助手
   - 成功指标: 能生成文章大纲
   - 阶段: 3个阶段（调研→开发→测试）
   - 时间线: 1个月内完成

🗂️ 归档原想法: 50_归档/2025-03/AI写作助手想法.md
🔗 已创建链接指向新项目

💡 MOC 维护建议:
   - 建议链接到 [[moc-编程]]？

用户: 确认
✅ 已更新 [[moc-编程]]
```

---

### 4.3 `/research <主题>` 研究笔记

**触发条件**:
- 用户直接调用: `/research "主题"`

**工作流程**:

1. **检查缓存**
   - 检查是否已存在相同主题的研究笔记
   - 如果存在 → 询问打开现有还是新建

2. **询问研究详情**
   - 这个研究属于哪个领域？（用于确定子文件夹）
   - 预期研究深度？（快速了解/深入学习/精通掌握）

3. **深度调研**
   - 使用 AI 搜索/分析能力进行深度调研
   - 提取核心概念、关键资源、学习路径

4. **创建研究笔记**
   - 在 `30_研究/<领域>/<主题>_YYYY-MM-DD.md` 创建
   - 使用模板: `99_模板/研究笔记模板.md`
   - 包含：概述、核心概念、学习资源、下一步行动

5. **提取核心知识**
   - 将核心概念提取到 `40_知识库/`
   - 建立研究笔记 ↔ 知识笔记的双向链接

6. **MOC 维护建议**
   - 询问是否链接到相关 MOC
   - 如果相关 MOC 不存在 → 询问是否创建

**输出示例**:
```
🔬 研究: Python 异步编程
━━━━━━━━━━━━━━━━━━━━
检查到不存在相同主题研究，开始新建...

📁 选择领域: 编程/Python
📝 正在深度调研...

✅ 已创建研究笔记:
   30_研究/编程/Python异步编程_2025-03-30.md

📚 核心概念已提取到 40_知识库/:
   - [[asyncio 核心概念]]
   - [[async/await 语法]]
   - [[协程与事件循环]]

🔗 已建立链接关系

💡 建议链接到 [[moc-编程]]？
用户: 确认
✅ 已更新 [[moc-编程]]
```

---

### 4.4 `/brainstorm <想法/项目名>` 头脑风暴

**触发条件**:
- 用户直接调用: `/brainstorm "想法名称"`

**工作流程**:

1. **查找关联项目**
   - 在 `10_项目/` 搜索关联项目
   - 如果找到 → 关联到该项目
   - 如果没有 → 询问是否从空白开始

2. **创建头脑风暴笔记**
   - 在 `10_项目/<领域>/<项目名>_头脑风暴_YYYY-MM-DD.md` 创建
   - 使用模板: `99_模板/头脑风暴模板.md`

3. **互动式头脑风暴**
   - AI 引导提问，深入挖掘想法
   - 记录所有思考过程和发散想法
   - 支持多轮对话

4. **提取精华**
   - 头脑风暴结束后，AI 提取核心要点
   - 生成结构化总结

5. **更新原项目**
   - 询问是否将精华内容追加到原项目文档
   - 如果确认 → 智能合并到项目文档

**输出示例**:
```
💡 头脑风暴: AI写作助手
━━━━━━━━━━━━━━━━━━━━
找到相关项目: [[AI写作助手]]

问题 1: 这个写作助手主要解决什么痛点？
A) 写作灵感  B) 文章润色  C) 结构优化

...（多轮对话）...

📝 头脑风暴精华:
   - 核心功能: 灵感生成 + 大纲建议
   - 技术方案: 调用 Claude API
   - 差异化: 结合个人知识库

✅ 已保存: 10_项目/编程/AI写作助手_头脑风暴_2025-03-30.md

💡 是否将精华追加到 [[AI写作助手]]？
用户: 是
✅ 已更新项目文档
```

---

### 4.5 `/archive <笔记路径>` 归档

**触发条件**:
- 用户直接调用: `/archive "笔记名称"`

**支持模式**:
1. **单个归档**: `/archive "项目名"`
2. **批量归档**: `/archive --folder "00_收件箱"`

**工作流程**:

1. **查找笔记/文件夹**
   - 搜索匹配的笔记或文件夹
   - 如果找到多个 → 列出让用户选择

2. **检查关联**
   - 检查是否有其他笔记链接到该笔记
   - 如果有 → 提示更新链接

3. **确认归档**
   - 显示归档详情：原位置 → 目标位置
   - 询问确认

4. **执行归档**
   - 移动到 `50_归档/YYYY-MM/`
   - 保持原文件夹结构（相对路径）
   - 更新 frontmatter: `status: 已归档`

5. **更新链接**
   - 在原位置创建重定向链接（可选）
   - 更新相关 MOC 的状态标记

**输出示例**:
```
📦 归档: AI写作助手
━━━━━━━━━━━━━━━━━━━━
找到项目: 10_项目/编程/AI写作助手.md

检查项目状态:
- 任务完成度: 100% (5/5)
- 相关笔记: 3 个

⚠️  发现 2 个反向链接，将更新为指向归档位置

确认归档？
- 移动到: 50_归档/2025-03/10_项目/编程/AI写作助手.md
- 更新相关链接

用户: 确认

✅ 已归档
🔗 已更新相关链接
📋 已更新 [[moc-编程]] 状态为 #已完成
```

---

### 4.6 `/ask <问题>` 快速查询

**触发条件**:
- 用户直接调用: `/ask "问题"`

**工作流程**:

1. **知识库搜索**
   - 执行: `obsidian search query="问题关键词"`
   - 查找相关笔记

2. **AI 回答**
   - 基于搜索结果生成回答
   - 引用相关笔记链接

3. **相关笔记推荐**
   - 列出最相关的 2-3 篇笔记

4. **保存选项**
   - 询问是否保存此回答到知识库
   - 如果确认 → 保存为快速查询笔记

**输出示例**:
```
🤔 查询: Python 装饰器是什么
━━━━━━━━━━━━━━━━━━━━

Python 装饰器是一种高阶函数，用于在不修改原函数代码的情况下扩展功能...

📚 找到相关笔记:
- [[Python 装饰器详解]] (40_知识库/)
- [[函数式编程学习笔记]] (30_研究/编程/)

💡 是否保存此回答到知识库？
用户: 是
✅ 已保存到 40_知识库/Python装饰器_快速查询_2025-03-30.md
```

---

### 4.7 `/review [范围]` 知识库回顾

**触发条件**:
- 用户直接调用: `/review [inbox|projects|all]`

**范围选项**:
- `/review inbox` - 仅回顾收件箱
- `/review projects` - 仅回顾项目
- `/review all` - 全面回顾（默认）

**工作流程**:

1. **收件箱回顾**（如果范围包含 inbox）
   - 扫描 `00_收件箱/` 所有笔记
   - 按时间分组：今天/本周/更早
   - 给出处理建议：/kickoff 或 /archive
   - 统计：超过 7 天未处理的数量

2. **项目回顾**（如果范围包含 projects）
   - 扫描 `10_项目/` 所有项目
   - 检查：最后更新时间、任务完成度
   - 识别僵尸项目（30 天未更新）
   - 给出建议：激活、归档、继续推进

3. **生成回顾报告**
   - 结构化的回顾结果
   - 优先级排序的行动建议
   - 可选保存到 `Daily/YYYY-MM-DD_回顾.md`

**输出示例**:
```
📊 知识库回顾报告 (2025-03-30)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📥 收件箱 (5 项待处理)
   🔴 超过 7 天: 2 项
      - [[旧想法]] → 建议 /kickoff 或 /archive
   🟡 本周新增: 3 项
      - [[新文章]] → 建议整理到对应领域

🚀 项目状态 (4 个活跃)
   ⚠️ 僵尸项目: 1 个
      - [[旧项目]] → 建议激活或归档
   ✅ 即将完成: 1 个
      - [[快完成的项目]] → 90% 完成

💡 建议的下一步行动:
   1. 处理僵尸项目 [[旧项目]]
   2. 归档收件箱中的 [[旧想法]]
```

**`/review inbox` 批量处理模式**：

当收件箱有多条内容时，支持批量处理：

```
📥 收件箱回顾
━━━━━━━━━━━━━━━━━━━━

待处理: 5 条

1. "学习Rust的想法"
   → 建议: 启动研究 /research Rust 或 启动项目 /kickoff

2. "AI写作助手项目想法"
   → 建议: 启动项目 /kickoff AI写作助手 --area=工作

3. "看到一篇好文章链接"
   → 建议: 导入内容 /import 或 手动处理

4. "会议记录片段"
   → 建议: 整理到 Daily 或 归档

5. "周末计划草稿"
   → 建议: 创建项目或归档

━━━━━━━━━━━━━━━━━━━━

处理方式:
- A. 逐条处理（Agent 引导每条）
- B. 批量启动（多个 /kickoff 或 /research）
- C. 全部归档（清理收件箱）

选择处理方式？
```

**逐条处理执行**：

用户选择 A 后，Agent 逐条引导：
```
处理第 1 条: "学习Rust的想法"

建议操作:
1. 启动研究笔记 /research Rust
2. 启动项目 /kickoff Rust学习（如果是实践目标）
3. 暂不处理

选择？ 用户: 1

✅ 创建研究笔记: 30_研究/编程/Rust学习_2025-03-31.md
✅ 原想法已归档到: 50_归档/2025-03/

继续处理下一条？ (y/n)
```

---

### 4.8 `/health-check [类型]` 健康检查

**触发条件**:
- 用户直接调用: `/health-check [orphans|deadlinks|tags|all]`

**检查类型**:
- `/health-check orphans` - 孤儿笔记
- `/health-check deadlinks` - 死链
- `/health-check tags` - 标签一致性
- `/health-check all` - 全面检查（默认）

**工作流程**:

1. **孤儿笔记检测（按 PARA 分级）**

   **天生可以有孤儿的目录**（放宽标准）：
   - `00_收件箱/` - 临时存放，尚未处理
   - `10_项目/` - 进行中，可能还未建立完整链接
   - `20_领域/` - Areas 本身就是分类容器
   - `99_模板/` - 模板文件
   - `Daily/` - 每日笔记

   **必须有链接的目录**（严格检查）：
   - `30_研究/` - 研究笔记应该链接到相关主题
   - `40_知识库/` - 永久知识必须有入链或出链

   **孤儿定义**:
   - 无入链（不被其他笔记引用）且
   - 无出链（不引用其他笔记）

   **处理方式**:
   - 仅对 `30_研究/` 和 `40_知识库/` 报告孤儿问题
   - 建议：链接到相关 MOC

2. **死链检测**
   - 提取所有 `[[笔记链接]]`
   - 检查目标笔记是否存在
   - 列出缺失的链接和来源

3. **标签一致性检查**
   - 检测相似标签（#Python vs #python）
   - 检测语义重复（#coding vs #编程）
   - 给出合并建议

4. **生成报告**
   - 健康评分（0-100）
   - 问题列表和修复建议

**输出示例**:
```
🏥 知识库健康检查报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 总笔记数: 127
🔗 总链接数: 342
🏷️ 总标签数: 56

⚠️ 发现的问题:
孤儿笔记: 3 个
   - [[随机想法]] → 建议链接到 [[moc-个人成长]]

死链: 2 个
   - [[已删除项目]] 被 [[某笔记]] 引用

标签问题: 1 组
   - #Python (15) 和 #python (3) → 建议合并

✅ 健康评分: 87/100

💡 是否自动修复？
用户: 确认
✅ 已修复死链
✅ 已合并重复标签
```

---

### 4.9 `/mocs [操作]` MOC 管理

**触发条件**:
- 用户直接调用: `/mocs [list|open|stats]`

**子命令**:

#### `/mocs list` - 列出所有 MOC
```
🗺️ MOC 列表
━━━━━━━━━━━━━━━━━━━━

40_知识库/moc/
├── moc-编程.md          12 个链接  更新: 2天前
├── moc-工作.md           8 个链接  更新: 5天前
├── moc-个人成长.md       5 个链接  更新: 1周前
└── 健康生活 MOC.md       3 个链接  更新: 2周前

💡 提示: 使用 `/mocs open 编程学习` 快速打开
```

#### `/mocs open <名称>` - 打开 MOC
- 模糊匹配名称
- 打开匹配的 MOC 笔记

#### `/mocs stats` - MOC 统计
```
📊 MOC 统计
━━━━━━━━━━━━━━━━━━━━

编程学习 MOC:
   笔记数: 12
   健康度: 92%
   ⚠️  1 个死链
   💡  3 个未链接的潜在相关笔记
```

---

### 4.10 `/import [内容]` 外部内容导入

**触发条件**:
- Agent 收到外部 skill 返回的结构化内容
- 用户请求保存外部资源到知识库
- 用户说：收藏这篇文章、保存到知识库、导入内容

**参数**：
| 参数 | 必需 | 说明 |
|------|------|------|
| `content` | 是 | 外部内容（JSON 格式或纯文本） |
| `type_hint` | 否 | 内容类型提示：article/tutorial/snippet/knowledge |
| `area` | 否 | 所属领域，不指定则由 Agent 推断 |

**工作流程**：

1. **解析输入**
   - 如果是 JSON → 提取各字段
   - 如果是纯文本 → 提取标题和内容，其他字段留空

2. **分析内容类型（Agent 决策）**

   | 特征 | 建议存放位置 | 原因 |
   |------|------------|------|
   | 短文（<500字）、片段、灵感 | `00_收件箱/` | 需后续整理 |
   | 教程、长文、需要深入学习 | `30_研究/<area>/` | 需要消化 |
   | 知识点摘要、已整理的内容 | `40_知识库/<area>/` | 直接入库 |
   | 项目相关资源 | `10_项目/<area>/<project>/` | 项目资料 |

3. **询问用户确认**
   ```
   📥 收到内容: "Python Async Best Practices"
   来源: twitter

   存放位置建议:
   - A. 收件箱 (稍后处理)
   - B. 研究笔记: 30_研究/编程/ (深入学习)
   - C. 知识库: 40_知识库/编程/ (直接入库) ← 推荐

   所属领域: [编程] ← 从内容推断
   是否调整？
   ```

4. **创建笔记**
   - 生成 Note ID
   - 根据存放位置选择 frontmatter type
   - 写入内容，追加来源链接

5. **后续处理**
   - 执行 `obsidian reload`
   - 询问是否链接到 MOC

**输出示例**：
```
📥 导入内容
━━━━━━━━━━━━━━━━━━━━

标题: Python Async Best Practices
来源: twitter (@python_dev)
推断领域: 编程

✅ 已保存到: 40_知识库/编程/Python_Async_Best_Practices_2025-03-31.md

💡 建议链接到 [[moc-编程]]
确认？ (y/n)
```

**Frontmatter 示例**：
```yaml
---
id: kb-20250331-143052-a1b2
type: knowledge
title: Python Async Best Practices
date: 2025-03-31
created: 2025-03-31 14:30
tags: [Python, 异步, asyncio]
source: twitter
source_url: https://twitter.com/python_dev/status/123456
area: 编程
mocs: []
---
```

---

### 4.11 `/moc-review` MOC 维护

**触发条件**:
- 用户直接调用: `/moc-review`
- 想批量处理未链接笔记时使用

**工作流程**:

1. **扫描未链接笔记**
   - 找出最近 7 天内创建的笔记
   - 排除：Daily、已归档、模板
   - 检查是否已存在于 MOC 中

2. **按主题分组建议**
   - AI 分析每篇笔记内容
   - 建议归属的 MOC
   - 如果无匹配 MOC → 建议创建新 MOC

3. **批量确认**
   - 按 MOC 分组显示建议
   - 用户一次性确认多个链接

**输出示例**:
```
🗺️ MOC 维护建议
━━━━━━━━━━━━━━━━━━━━

最近 7 天未链接笔记: 5 篇

建议链接到 [[编程学习 MOC]]:
   ✅ [[Python 装饰器详解]]
   ✅ [[异步编程笔记]]

建议新建 MOC [[机器学习]]:
   ⚠️ [[机器学习入门]] 无法匹配现有 MOC

确认执行？ (全部确认/逐项确认/取消)
```

---

### 4.12 通用 CLI 钩子

对于超出上述工作流的操作，Agent 可以直接调用 Obsidian CLI：

```
obsidian --help  # 查看所有可用命令
obsidian search query="Python" path="10_项目"
obsidian tags counts format=json
obsidian tasks todo
```

**设计理念**：提供灵活的钩子让 Agent 处理工作流之外的任务，而不是硬编码所有可能的情况。

---

## 5. 模板设计

### 5.1 项目启动模板

```markdown
---
id: {{NOTE_ID}}
type: project
title: {{PROJECT_NAME}}
date: {{DATE}}
created: {{DATETIME}}
status: 进行中
tags: [项目, {{AREA}}]
mocs:
  - "moc-{{AREA}}"
---

# {{PROJECT_NAME}}

> 创建于 {{DATE}} | 来自: {{SOURCE_NOTE}}

---

## 项目目标

{{PROJECT_GOAL}}

## 成功指标

- [ ] 指标 1: ...
- [ ] 指标 2: ...

## 阶段与里程碑

### 阶段 1: 调研（第 1 周）
- [ ] 任务 1
- [ ] 任务 2

### 阶段 2: 开发（第 2-3 周）
- [ ] 任务 1
- [ ] 任务 2

### 阶段 3: 测试与发布（第 4 周）
- [ ] 任务 1
- [ ] 任务 2

## 时间线

- **开始日期**: {{DATE}}
- **目标完成**: {{TARGET_DATE}}
- **实际完成**:

## 相关资源

- [资源链接]
- [[相关笔记]]

## 进展记录

### {{DATE}} - 启动
项目启动，初始规划完成。

## 复盘总结

（项目完成后填写）
```

### 5.2 研究笔记模板

```markdown
---
id: {{NOTE_ID}}
type: research
title: {{RESEARCH_TOPIC}}
date: {{DATE}}
created: {{DATETIME}}
area: {{AREA}}
status: 进行中
tags: [研究, {{AREA}}]
mocs:
  - "moc-{{AREA}}"
---

# {{RESEARCH_TOPIC}} 研究笔记

> 研究领域: {{AREA}} | 开始日期: {{DATE}}

---

## 研究概述

{{OVERVIEW}}

## 核心概念

### 概念 1: ...
详细说明...

### 概念 2: ...
详细说明...

## 学习资源

### 文章/教程
- [标题](URL) - 简要说明

### 视频
- [标题](URL) - 简要说明

### 书籍
- 《书名》- 作者

## 实践笔记

（实践过程中的记录）

## 核心知识提取

已提取到知识库:
- [[知识点 1]]
- [[知识点 2]]

## 下一步行动

- [ ] 行动项 1
- [ ] 行动项 2

## 研究总结

（研究完成后填写）
```

### 5.3 头脑风暴模板

```markdown
---
id: {{NOTE_ID}}
type: brainstorm
title: {{TOPIC}} 头脑风暴
date: {{DATE}}
created: {{DATETIME}}
related_project: "[[{{PROJECT}}]]"
tags: [头脑风暴, {{AREA}}]
---

# {{TOPIC}} 头脑风暴

> 关联项目: [[{{PROJECT}}]] | 日期: {{DATE}}

---

## 原始想法

{{INITIAL_IDEA}}

## 头脑风暴过程

### 问题 1: ...
**思考**: ...

### 问题 2: ...
**思考**: ...

## 发散想法

- 想法 1: ...
- 想法 2: ...
- 想法 3: ...

## 精华提取

### 核心结论
...

### 可行方案
1. 方案 A: ...
2. 方案 B: ...

### 下一步行动
- [ ] 行动项 1
- [ ] 行动项 2

## 关联思考

- [[相关笔记 1]]
- [[相关笔记 2]]
```

### 5.4 每日规划模板

```markdown
---
id: {{NOTE_ID}}
type: daily-note
date: {{DATE}}
created: {{DATETIME}}
inbox_count: 0
active_projects: 0
todo_count: 0
tags: [每日规划]
---

# {{DATE}} 每日规划

---

## 今日重点

（手动填写或 AI 建议）

## 收件箱待处理

{{INBOX_ITEMS}}

## 进行中项目

{{ACTIVE_PROJECTS}}

## 今日待办

{{TODOS}}

---

## 今日记录

（手动填写今日进展）

## 明日计划

（手动填写）
```

### 5.5 MOC 模板

```markdown
---
id: {{NOTE_ID}}
type: moc
title: {{AREA}} MOC
date: {{DATE}}
created: {{DATETIME}}
updated: {{DATETIME}}
tags: [MOC, {{AREA}}]
---

# {{AREA}} MOC

> 汇集所有 {{AREA}} 相关的笔记、项目和资源
> 最后更新: {{DATETIME}}

---

## 进行中的项目

{{PROJECTS_IN_PROGRESS}}

## 研究主题

{{RESEARCH_TOPICS}}

## 知识库

{{KNOWLEDGE_BASE}}

## 待归档

{{ARCHIVE_CANDIDATES}}

## 相关资源

- [外部资源](URL)

---

**统计:**
- 项目: {{PROJECT_COUNT}}
- 研究: {{RESEARCH_COUNT}}
- 知识: {{KNOWLEDGE_COUNT}}
- 总计: {{TOTAL_COUNT}}
```

### 5.6 模板扩展与自定义

用户可以扩展和自定义模板以满足特定需求。

**添加新模板**：

1. 在 `99_模板/` 目录下创建新的 `.md` 文件
2. 使用 Jinja2 变量语法（`{{ VARIABLE }}`）
3. 在配置中注册新模板

**示例：添加"读书笔记"模板**：

```markdown
# 文件: 99_模板/读书笔记模板.md
---
id: {{ NOTE_ID }}
type: reading-note
title: {{ BOOK_TITLE }}
date: {{ DATE }}
created: {{ DATETIME }}
tags: [读书, {{ AREA }}]
author: {{ BOOK_AUTHOR }}
rating: 
status: 进行中
area: {{ AREA }}
---

# {{ BOOK_TITLE }}

> 作者: {{ BOOK_AUTHOR }} | 开始阅读: {{ DATE }}

---

## 书籍信息

- **书名**: {{ BOOK_TITLE }}
- **作者**: {{ BOOK_AUTHOR }}
- **出版年**: 
- **阅读进度**: 

## 核心观点

### 观点 1: ...
详细说明...

### 观点 2: ...
详细说明...

## 精彩摘录

> "摘录内容..."

## 我的思考

（阅读过程中的思考）

## 行动清单

- [ ] 行动项 1
- [ ] 行动项 2

## 推荐指数

⭐⭐⭐⭐⭐ (5/5)
```

**注册新模板**：

```json
// ~/.config/obsidian-kb/config.json
{
  "templates": {
    "project": "99_模板/项目启动模板.md",
    "research": "99_模板/研究笔记模板.md",
    "reading": "99_模板/读书笔记模板.md"  // 新增
  }
}
```

**修改现有模板**：

用户可以直接编辑 `99_模板/` 目录下的模板文件。Agent 使用模板时会读取最新内容。

**模板变量说明**：

| 变量 | 说明 | 自动生成 |
|------|------|---------|
| `{{ NOTE_ID }}` | 唯一标识符 | 是 |
| `{{ DATE }}` | 当前日期 YYYY-MM-DD | 是 |
| `{{ DATETIME }}` | 当前时间 YYYY-MM-DD HH:MM | 是 |
| `{{ AREA }}` | 所属领域 | 用户输入或推断 |
| `{{ TITLE }}` | 笔记标题 | 用户输入 |
| 其他变量 | 根据模板类型 | 用户输入 |

**自定义模板的 CLI Hook 调用**：

```
用户: 用读书笔记模板记录《原子习惯》

Agent 执行:
1. 读取配置中的 templates.reading
2. 加载 99_模板/读书笔记模板.md
3. 收集参数: BOOK_TITLE=原子习惯, BOOK_AUTHOR=James Clear
4. 渲染模板，创建笔记
```

---

## 6. 错误处理策略

### 6.1 Obsidian CLI 不可用

**场景**: obsidian 命令不存在或无法连接

**处理**:
1. 检查 obsidian 命令是否可用
2. 如果不可用 → 提示用户打开 Obsidian 应用
3. 提供手动操作指南

### 6.2 Vault 路径错误

**场景**: `/Volumes/SSD/ObsidianVault` 不存在

**处理**:
1. 检查路径是否存在
2. 如果不存在 → 询问正确的 Vault 路径
3. 保存配置供后续使用

### 6.3 笔记不存在

**场景**: 用户指定的笔记找不到

**处理**:
1. 尝试模糊搜索
2. 列出相似结果让用户选择
3. 如果无匹配 → 询问是否新建

### 6.4 权限错误

**场景**: 无法创建文件或目录

**处理**:
1. 检查文件系统权限
2. 提示用户检查权限
3. 提供替代方案（保存到其他位置）

### 6.5 备份与恢复机制

**自动备份**：

所有修改操作前，自动创建备份：

| 操作类型 | 备份策略 | 备份位置 |
|---------|---------|---------|
| 单文件修改 | 复制原文件到备份目录 | `metadata/backups/YYYY-MM-DD/<原路径>/<文件名>.bak` |
| 批量操作 | 打包所有受影响文件 | `metadata/backups/YYYY-MM-DD/<操作ID>.zip` |
| 归档操作 | 复制原文件 + 记录反向链接 | `metadata/backups/YYYY-MM-DD/archive/<文件名>.bak` |

**备份目录结构**：
```
metadata/backups/
├── 2025-03-30/
│   ├── 10_项目/
│   │   └── 编程/
│   │       └── Python项目笔记.md.bak
│   ├── archive/
│   │   └── 旧项目.md.bak
│   └── batch_op_143052.zip  # 批量操作备份
└── backup-log.json          # 备份日志
```

**备份日志格式**：
```json
{
  "backups": [
    {
      "id": "bk-20250330-143052",
      "timestamp": "2025-03-30T14:30:52",
      "operation": "archive",
      "files": ["10_项目/编程/Python项目笔记.md"],
      "backup_path": "metadata/backups/2025-03-30/archive/Python项目笔记.md.bak",
      "status": "success"
    }
  ]
}
```

**恢复操作**：

用户可以撤销最近的操作：

```
用户: 撤销刚才的归档操作
用户: 恢复被误删的笔记
用户: 回滚到昨天的状态

Agent 执行:
1. 检查备份日志，找到最近的备份
2. 展示可恢复的操作列表:
   📋 可恢复的操作
   ━━━━━━━━━━━━━━━━━━━━
   1. [14:30] 归档 "Python项目笔记" ← 刚才
   2. [11:20] 批量添加标签 (3个文件)
   3. [09:15] 重命名 "旧项目" → "已完成项目"

   选择要恢复的操作？

3. 用户选择后:
   - 从备份恢复文件
   - 回滚相关链接更新
   - 更新 frontmatter
   - obsidian reload
```

**备份保留策略**：

| 备份类型 | 保留时间 | 说明 |
|---------|---------|------|
| 当天备份 | 永久 | 当天的操作可随时恢复 |
| 本周备份 | 7 天 | 一周内的操作可恢复 |
| 更早备份 | 30 天 | 一个月内的备份自动清理 |

**手动备份命令**：

```
用户: 备份整个 Vault

Agent: 执行全量备份...
✅ 备份完成: metadata/backups/manual/2025-03-30_full.zip
📦 包含: 150 个笔记, 5 个 MOC
💾 大小: 2.3 MB
```

**重要提示**：
- 备份仅包含元数据和修改记录，不包含完整笔记内容
- 建议用户使用 Git 或 Obsidian Sync 进行完整备份
- 备份目录可添加到 `.gitignore`

---

## 7. 使用场景示例

### 场景 1: 新的一天开始
```
用户: /start-my-day
Agent: 扫描收件箱 → 列出进行中的项目 → 生成今日建议
用户: 处理建议 → 继续工作或执行其他命令
```

### 场景 2: 产生新想法
```
用户: /kickoff "开发一个习惯追踪 App"
Agent: 询问领域 → 询问时间线 → 创建项目文档 → 建议链接 MOC
用户: 确认 → 开始项目工作
```

### 场景 3: 研究学习
```
用户: /research "微服务架构"
Agent: 询问领域 → 深度调研 → 创建研究笔记 → 提取核心知识 → 建议 MOC
用户: 确认 → 开始学习
```

### 场景 4: 头脑风暴
```
用户: /brainstorm "App 的盈利模式"
Agent: 关联项目 → 引导式提问 → 记录想法 → 提取精华 → 更新项目
用户: 多轮对话 → 获得可行方案
```

### 场景 5: 项目完成
```
用户: /archive "习惯追踪 App"
Agent: 检查完成度 → 确认归档 → 移动文件 → 更新链接 → 更新 MOC
用户: 确认 → 项目归档完成
```

### 场景 6: 定期回顾
```
用户: /review all
Agent: 扫描收件箱 → 扫描项目 → 生成回顾报告
用户: 按建议处理积压 → 清理僵尸项目 → 归档旧笔记
```

### 场景 7: 灵活使用 CLI 钩子
```
用户: 我想看看所有关于 Python 的笔记
Agent: 执行 obsidian search query="Python" → 列出结果
用户: 帮我把这些笔记都加上 #Python 标签
Agent: 执行 obsidian tags 相关命令完成任务
```

---

## 8. 配置与扩展

### 8.1 用户配置

技能应支持用户自定义配置：

```json
{
  "vault_path": "/Volumes/SSD/ObsidianVault",
  "default_area": "编程",
  "quiet_mode": false,
  "auto_confirm_threshold": 0.8,    // 置信度阈值，超过则自动执行
  "auto_confirm_actions": [         // 哪些操作可以自动执行
    "moc_link",
    "tag_extraction"
  ],
  "templates": {
    "project": "99_模板/项目启动模板.md",
    "research": "99_模板/研究笔记模板.md"
  }
}
```

**置信度自动执行机制**:

| 置信度 | 处理方式 | 示例 |
|--------|---------|------|
| **> 0.8** (高) | 自动执行，最后汇总告知 | 明显的技术文章提取到对应 MOC |
| **0.5 - 0.8** (中) | 快速确认（是/否） | 领域判断较明确 |
| **< 0.5** (低) | 详细询问（多选） | 模棱两可的情况 |

**示例流程**:
```
AI 分析内容 → 置信度 0.9
→ 自动保存到 30_研究/编程/
→ 自动添加标签 #Python
→ 自动链接到 [[moc-编程]]

最后汇总告知:
"已完成以下操作（高置信度自动执行）:
- 保存笔记到 30_研究/编程/
- 添加标签: #Python
- 链接到 [[moc-编程]]"
```

**用户可配置**:
- 设置阈值（0.0 - 1.0）
- 选择哪些操作可以自动
- 完全手动模式（阈值设为 1.1）

### 8.2 扩展点

- 自定义模板
- 自定义工作流
- 插件集成（如 Obsidian 插件 API）
- 外部 API 集成（如 Claude API 用于深度分析）

---

## 9. 实现注意事项

本节记录从设计到实现阶段需要特别关注的技术细节和优化建议。

### 9.1 性能与上下文窗口管理

**问题**: 全局扫描的隐患

当知识库膨胀到几千篇笔记时，`/review all` 或 `/start-my-day` 涉及的全量扫描（如扫描整个 `00_收件箱` 或 `10_项目`）如果试图读取大量文件的详细内容，极易耗尽 Token 或导致响应极慢。

**优化方案**:

1. **信息截断机制**（在 `utils.sh` 中实现）:
   - 列表扫描时只提取文件的 Frontmatter 和前 200 个字符的摘要
   - 使用 `obsidian files` 命令获取列表，而非读取每个文件的完整内容
   - 仅在用户明确需要深入探讨某个具体项目时，才读取全量内容

2. **分层扫描策略**:
   ```bash
   # 第一层：只获取元数据（文件名、修改时间、frontmatter）
   obsidian files folder="10_项目" format=json

   # 第二层：用户选择具体项目后，才读取完整内容
   obsidian read path="10_项目/具体项目.md"
   ```

3. **缓存机制**:
   - 缓存文件列表和 frontmatter 信息（有效期 5 分钟）
   - 避免重复扫描未变更的文件

### 9.2 配置管理

**问题**: 硬编码路径风险

文档中多处出现 `/Volumes/SSD/ObsidianVault/` 绝对路径，存在以下风险：
- 不同用户 Vault 路径不同
- 路径变更后需要修改多处代码

**解决方案**:

1. **强制配置文件注入**:
   - 所有脚本必须通过配置文件获取 `VAULT_PATH`
   - 首次运行时强制要求用户提供 Vault 路径
   - 配置文件位置：`~/.config/obsidian-kb/config.json`

2. **配置加载机制**:
   ```bash
   # 每个脚本开头必须加载配置
   source "$(dirname "$0")/../config/config.sh"
   # 或使用环境变量
   VAULT_PATH=$(get_config "vault_path")
   ```

3. **路径不存在处理**:
   - 启动时检查 `VAULT_PATH` 是否存在
   - 不存在时抛出错误并引导用户配置

### 9.3 依赖管理

**问题**: 强依赖外部工具

该技能强依赖：
- `obsidian` CLI 工具（Obsidian 应用需运行并启用 CLI 插件）

**解决方案**:

1. **环境检查**（Python 实现）:
   ```python
   import shutil
   import subprocess

   def check_obsidian_cli() -> dict:
       """检查 Obsidian CLI 是否可用。"""
       try:
           result = subprocess.run(
               ["obsidian", "--version"],
               capture_output=True, text=True, timeout=5
           )
           if result.returncode == 0:
               return {"available": True, "version": result.stdout.strip()}
           return {"available": False, "error": result.stderr}
       except FileNotFoundError:
           return {"available": False, "error": "Obsidian CLI not found"}
       except subprocess.TimeoutExpired:
           return {"available": False, "error": "Obsidian CLI timed out"}
   ```

2. **首次运行检查**:
   - 任何命令执行前检查 CLI 可用性
   - 检查 Vault 路径配置
   - 不可用时提示用户打开 Obsidian 应用

### 9.4 危险操作的容错设计

**问题**: 脆弱的链接替换

`/archive` 工作流提到要更新反向链接。纯 Bash/正则在处理复杂的 Markdown 链接时非常容易误伤数据：
- `[[笔记名称|别名]]` - 带别名的链接
- `[[笔记名称^block-id]]` - 块引用
- `[[笔记名称#标题]]` - 标题引用

**解决方案**:

1. **Dry-run (试运行) 机制**:
   - 所有涉及文件移动和链接修改的破坏性操作，必须先试运行
   - 打印即将修改的 Diff 列表：
     ```
     即将执行以下修改：
     - 移动: 10_项目/旧项目.md → 50_归档/2025-03/旧项目.md
     - 修改: 20_领域/某笔记.md 中的 2 处链接
       - [[旧项目]] → [[50_归档/2025-03/旧项目|旧项目]]

     确认执行？ (是/否)
     ```

2. **链接解析的健壮性**:
   - 使用专门的链接解析函数，而非简单正则
   - 处理各种 Obsidian 链接语法
   - 示例实现：
     ```bash
     parse_links() {
       local content="$1"
       # 使用更精确的模式匹配
       grep -oE '\[\[[^\]]+\]\]' <<< "$content" | sed 's/^\[\[//;s/\]\]$//'
     }
     ```

3. **备份机制**:
   - 修改前自动备份受影响文件到 `metadata/backups/`
   - 提供 `/restore` 命令恢复

4. **事务性操作**:
   - 将多个文件修改视为一个事务
   - 任何一步失败则全部回滚

### 9.5 Markdown 解析策略

**问题**: 字符串替换的隐患

如果用 `text.replace("#tag", "")` 这种方式处理 Markdown：
- 会破坏代码块中的 `#tag`
- 会破坏链接中的 `[[笔记#标题]]`
- 会破坏 frontmatter

**方案对比**:

| 场景 | 推荐方案 | 原因 |
|------|---------|------|
| **信息提取** | ✅ AST 解析 | 单向解析，无需写回，完美适用 |
| **内容修改** (`/archive` 链接更新) | ⚠️ 精确字符串替换 | AST Round-trip 是难题 |

**方案 A：信息提取（AST 解析）**

用于只读解析场景：

```python
# 使用 markdown-it-py（单向解析，无需写回）
from markdown_it import MarkdownIt

md = MarkdownIt()
tokens = md.parse(text)

# 提取链接、标题、标签
for token in tokens:
    if token.type == "inline":
        # 安全地提取信息，不修改原文
        pass
```

**方案 B：内容修改（精确字符串替换）**

用于 `/archive` 等需要修改文件的场景：

```python
# 基于行号和游标的精确替换
# 不使用 AST，而是记录修改位置后精确替换

class PreciseReplacer:
    def __init__(self, content: str):
        self.content = content
        self.replacements = []

    def add_replacement(self, start: int, end: int, new_text: str):
        """基于字符游标的替换"""
        self.replacements.append((start, end, new_text))

    def apply(self) -> str:
        """从后往前应用替换，避免游标偏移"""
        result = self.content
        for start, end, new_text in sorted(self.replacements, reverse=True):
            result = result[:start] + new_text + result[end:]
        return result
```

**关键规则**:
- **提取信息**: 使用 AST（markdown-it-py）
- **修改内容**: 使用行号/游标精确替换，禁止全局正则
- **操作前**: 必须 Dry-run，显示将要修改的 Diff
- **备选方案**: 如果修改复杂，可使用 Node.js 生态的 `remark` + `mdast-util-to-markdown`（通过子进程调用）

---

## 10. 总结

本技能提供完整的 Obsidian 知识库管理能力，基于 PARA 方法论，支持：

1. **日常流程**: 每日规划、项目启动、研究学习
2. **头脑风暴**: 引导式思维发散，精华提取
3. **知识维护**: 归档、回顾、健康检查、MOC 管理
4. **灵活钩子**: 直接调用 Obsidian CLI 处理工作流之外的任务

所有命令均为用户主动触发，无自动定时任务，确保用户完全控制知识库管理流程。

---

**设计完成日期**: 2025-03-30
**版本**: 1.1.0
