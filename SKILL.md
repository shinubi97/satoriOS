---
name: obsidian-knowledge-base
description: |
  Manage Obsidian knowledge base with PARA methodology. Use this skill when the user mentions:
  - Obsidian, knowledge base, vault, notes, MOC
  - PARA method, projects, areas, resources, archives
  - Daily planning, inbox processing, project kickoff
  - Research notes, brainstorming, knowledge organization
  - Link management, orphan detection, health check

  Trigger keywords: /start-my-day, /kickoff, /research, /brainstorm, /archive, /ask, /review, /health-check, /mocs, /moc-review, /import
---

# Obsidian Knowledge Base Management Skill

提供基于 PARA 方法论的完整 Obsidian 知识管理工作流。

## Prerequisites

Before using this skill, ensure:

1. **Obsidian CLI available** - Obsidian app running with CLI plugin enabled
2. **Vault configured** - Run `obsidian-kb config init` to set vault path
3. **PARA structure** - Vault should have standard PARA directories:
   - `00_收件箱/` - Inbox
   - `10_项目/` - Projects
   - `20_领域/` - Areas
   - `30_研究/` - Research
   - `40_知识库/` - Knowledge Base (including `moc/` subfolder)
   - `50_归档/` - Archives
   - `99_模板/` - Templates
   - `Daily/` - Daily notes

## Commands Overview

| Command | Description | Parameters |
|---------|-------------|------------|
| `/start-my-day` | Daily planning | None |
| `/kickoff <name>` | Start new project | idea_name, --area, --timeline |
| `/research <topic>` | Create research note | topic, --area, --depth |
| `/brainstorm <topic>` | Brainstorming session | topic, --project, --area |
| `/archive <target>` | Archive notes | target, --folder, --confirm |
| `/ask <question>` | Quick query | question |
| `/review [note_path]` | Review notes | note_path, --focus |
| `/health-check [type]` | Health check | orphans/deadlinks/tags/all |
| `/mocs <subcmd>` | MOC management | list/open/stats/create |
| `/moc-review` | Link unlinked notes | --area, --path, --all |
| `/import <content>` | Import external content | content, --type, --area |
| `/backup [target]` | Backup notes | target, --full |
| `/restore [backup-id]` | Restore from backup | backup-id, --list |

## CLI Hook (超出工作流的操作)

当用户的请求超出上述预定义工作流时，使用 CLI Hook 灵活处理：

**流程**：
1. 执行 `obsidian --help` 查看可用命令
2. 判断是否能组合命令完成用户任务
3. **如能完成** → 告知用户执行链路，确认后执行
4. **如无法完成** → 告知用户限制，建议替代方案

**示例**：
```
用户: 帮我把所有包含"Python"的笔记都加上 #Python 标签

Agent: 我来检查可用的 CLI 命令...
执行 obsidian --help 后发现可以组合以下命令：
1. obsidian search query=Python format=json  # 搜索包含 Python 的笔记
2. obsidian property:set name=tags value=#Python file=<note>  # 为每个笔记添加标签

预计影响 15 个笔记。确认执行？

用户: 确认
Agent: [执行操作...]
```

**标签追加逻辑说明**：

使用 `property:set` 设置标签时，CLI 会**覆盖**原有值而非追加。如需追加标签：

```python
# 1. 先读取现有标签
obsidian property:read name=tags file=my-note format=json

# 2. 解析返回值，合并新旧标签
existing_tags = result["tags"]  # 如 ["Python", "异步"]
new_tags = existing_tags + ["#装饰器"]  # 合并

# 3. 设置合并后的值
obsidian property:set name=tags value=["Python", "异步", "#装饰器"] file=my-note
```

Agent 在 CLI Hook 场景中需自行处理追加逻辑，告知用户完整执行链路。

**重命名笔记的链接更新流程**：

当用户请求重命名笔记时，需要同步更新所有反向链接：

```python
# 执行链路示例
用户: 把"Python项目笔记"重命名为"Python爬虫项目"

Agent 执行流程:
1. obsidian search query="[[Python项目笔记]]" format=json  # 查找引用
2. 解析结果，列出所有需要更新的文件
3. 展示预览:
   📝 重命名预览
   ━━━━━━━━━━━━━━━━━━━━
   源文件: 10_项目/编程/Python项目笔记.md
   新名称: Python爬虫项目

   需更新链接的文件 (3个):
   - 40_知识库/moc/moc-编程.md
   - Daily/2025-03-30.md
   - 30_研究/编程/Python学习笔记.md

   确认执行？

4. 用户确认后:
   - 重命名文件
   - 更新所有反向链接 [[Python项目笔记]] → [[Python爬虫项目]]
   - obsidian reload
```

**注意**：重命名后的链接格式取决于文件位置：
- 同目录内：`[[新名称]]`
- 不同目录：`[[相对路径/新名称]]`

**批量操作安全机制**：

批量操作（影响多个文件）必须遵循以下流程：

1. **展示影响范围**
   ```
   🔍 执行预览
   ━━━━━━━━━━━━━━━━━━━━
   操作: 为所有研究笔记添加 #待复习 标签

   影响范围:
   - 30_研究/编程/Python异步.md
   - 30_研究/编程/装饰器详解.md
   - 30_研究/工作/时间管理.md
   ... 共 15 个文件

   预计耗时: ~30秒
   ```

2. **用户确认**
   - 显示影响文件数量
   - 高风险操作（删除、批量修改）必须确认
   - 低风险操作（添加标签、链接）可配置自动确认

3. **执行与回滚**
   - 执行前备份到 `metadata/backups/`
   - 如执行失败 → 告知用户，建议回滚
   - 执行成功 → `obsidian reload`

**自动确认阈值配置**：
```json
{
  "auto_confirm_threshold": 0.8,
  "auto_confirm_actions": ["moc_link", "tag_add", "content_append"]
}
```

**笔记合并流程**：

```python
用户: 把"Python基础"和"Python进阶"两篇笔记合并成一篇

Agent 执行:
1. obsidian read file=Python基础 format=json
2. obsidian read file=Python进阶 format=json
3. 分析两篇笔记的内容结构
4. 生成合并预览:
   📝 合并预览
   ━━━━━━━━━━━━━━━━━━━━
   合并结果: Python学习笔记（综合）

   结构建议:
   ## Python 基础知识
   [来自 Python基础 的内容]

   ## Python 进阶技巧
   [来自 Python进阶 的内容]

   原笔记处理:
   - Python基础.md → 归档
   - Python进阶.md → 归档

   确认执行？

5. 用户确认后:
   - 创建合并笔记
   - 更新反向链接指向新笔记
   - 归档原笔记
   - obsidian reload
```

**笔记拆分流程**：

```python
用户: 把这篇长笔记拆分成三个知识点

Agent 执行:
1. 读取原笔记内容
2. 分析内容结构，识别可拆分章节
3. 生成分拆建议:
   📄 拆分预览
   ━━━━━━━━━━━━━━━━━━━━
   原笔记: Python全栈学习

   拆分结果:
   1. Python基础语法.md → 基础部分
   2. Python进阶特性.md → 进阶部分
   3. Python项目实战.md → 实战部分

   原笔记处理:
   - 保留（作为汇总索引）或 归档

   确认执行？

4. 用户确认后执行
```

## Workflow Details

### `/start-my-day` Daily Planning

**无需用户输入参数**，直接执行即可。

1. Check if `Daily/YYYY-MM-DD.md` exists
2. Scan inbox (max 5 items to avoid token overflow)
3. List active projects with `#进行中` tag
4. Extract pending todos from daily notes
5. Generate prioritized suggestions
6. Output structured report

**Agent 可选**：询问用户是否要执行建议的下一步操作。

**Output format:**
```
📅 YYYY-MM-DD 每日规划
━━━━━━━━━━━━━━━━━━━━
📥 收件箱待处理: X 项
🚀 进行中项目: Y 个
✅ 今日建议重点:
   1. ...
```

### `/kickoff` Project Startup

**需要 Agent 收集的参数**：

| 参数 | 必需 | 说明 | 决策指南 |
|------|------|------|----------|
| `idea_name` | 是 | 想法/项目名称 | 从用户输入获取 |
| `area` | 否 | 所属领域 | 优先询问用户；若用户未指定，使用配置的 `default_area` |
| `timeline` | 否 | 期望完成时间 | 默认 "1个月" |
| `goals` | 否 | 项目目标列表 | 可选询问 |

**执行步骤**：

1. Search for matching idea in `00_收件箱/`
2. **如找到多个匹配** → 让用户选择一个
3. Create project document in `10_项目/<area>/`
   - **如 `<area>` 子目录不存在** → 自动创建（如 `10_项目/编程/`）
4. Archive original idea to `50_归档/YYYY-MM/`
5. Return result with MOC suggestions

**执行完成后**：询问用户是否要链接到相关 MOC。

### `/research` Research Notes

**需要 Agent 收集的参数**：

| 参数 | 必需 | 说明 | 决策指南 |
|------|------|------|----------|
| `topic` | 是 | 研究主题 | 从用户输入获取 |
| `area` | 否 | 所属领域 | 根据主题内容推断（如"Python 异步"→"编程"），或询问用户 |
| `depth` | 否 | 研究深度 | 默认 "深入学习"；用户提到"快速了解"或"精通"时调整 |
| `link_to_moc` | 否 | 要链接的 MOC | 执行完成后询问 |

**执行步骤**：

1. Check if research on this topic already exists
2. **如已存在** → 询问用户是否要继续/打开现有笔记
3. Create research note in `30_研究/<area>/<topic>_YYYY-MM-DD.md`
4. Extract core concepts to `40_知识库/`

**执行完成后**：询问用户是否要链接到相关 MOC。

### `/brainstorm` Brainstorming

**需要 Agent 收集的参数**：

| 参数 | 必需 | 说明 | 决策指南 |
|------|------|------|----------|
| `topic` | 是 | 头脑风暴主题 | 从用户输入获取 |
| `project` | 否 | 关联的项目名称 | 尝试从主题匹配现有项目，或询问用户 |
| `area` | 否 | 所属领域 | 若有项目则继承项目领域；否则询问或推断 |
| `initial_idea` | 否 | 初始想法描述 | 可选，若用户提供则记录 |

**执行步骤**：

1. Find related project (if `project` provided)
2. Create brainstorm note in `10_项目/<area>/<project>_头脑风暴_YYYY-MM-DD.md`
3. Return note path for Agent to continue conversation

**多轮对话**：
- Agent 继续与用户对话，追加内容到笔记
- **对话结束后**：询问用户是否将精华追加到项目文档

### `/archive` Archival

**需要 Agent 收集的参数**：

| 参数 | 必需 | 说明 | 决策指南 |
|------|------|------|----------|
| `target` | 是 | 要归档的笔记名称或路径 | 从用户输入获取；支持模糊匹配 |
| `folder` | 否 | 批量归档文件夹 | 用户明确提到"整个文件夹"时设置 |
| `confirm` | 否 | 是否确认执行 | 默认 True，展示预览让用户确认 |

**执行步骤**：

1. Find target note
2. Check backlinks (who links to this note)
3. **展示预览**（Dry-run）：列出所有将受影响的文件
4. **用户确认后**执行：
   - Move to `50_归档/YYYY-MM/`
   - Update backlinks in source files
   - Update frontmatter status

**安全机制**：
- Dry-run preview before execution
- Automatic backup to `metadata/backups/`
- User confirmation required for destructive operations

**归档后反向链接更新格式**：

归档笔记后，需更新所有引用该笔记的源文件中的链接。更新规则：

| 情况 | 更新格式 |
|------|---------|
| 引用方在归档目录内 | 保持原链接 `[[原名称]]`（同在归档区） |
| 引用方在其他目录 | 更新为 `[[50_归档/YYYY-MM/原名称]]`（完整路径） |

**示例**：
```
归档前: [[Python 项目笔记]]（在 10_项目/中）
归档后:
  - 10_项目/其他项目.md 中 → [[50_归档/2025-03/Python 项目笔记]]
  - 50_归档/2025-02/旧笔记.md 中 → [[Python 项目笔记]]（保持不变）
```

### `/ask` Quick Query

**需要 Agent 收集的参数**：

| 参数 | 必需 | 说明 |
|------|------|------|
| `question` | 是 | 用户问题 |

**执行步骤**：

1. Search knowledge base
2. Generate answer based on search results
3. Return answer with source note references

**可选**：询问用户是否保存此回答到知识库。

### `/import` External Content Import

**触发条件**：
- Agent 收到外部 skill 返回的结构化内容
- 用户请求：收藏这篇文章、保存到知识库、导入内容

**需要 Agent 收集的参数**：

| 参数 | 必需 | 说明 | 决策指南 |
|------|------|------|----------|
| `content` | 是 | 外部内容（JSON 或纯文本） | 从外部 skill 返回或用户输入获取 |
| `type_hint` | 否 | 内容类型 | 分析内容特征推断 |
| `area` | 否 | 所属领域 | 从内容关键词推断，或询问用户 |

**外部内容标准格式**：
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

**执行步骤**：

1. **解析输入**
   - JSON → 提取各字段
   - 纯文本 → 提取标题和内容

2. **分析内容类型（Agent 决策）**

   | 特征 | 建议存放位置 | 原因 |
   |------|------------|------|
   | 短文（<500字）、片段 | `00_收件箱/` | 需后续整理 |
   | 教程、长文 | `30_研究/<area>/` | 需要消化 |
   | 知识点摘要 | `40_知识库/<area>/` | 直接入库 |
   | 项目相关资源 | `10_项目/<area>/<project>/` | 项目资料 |

3. **询问用户确认存放位置**
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
   - 写入 frontmatter（包含 source, source_url）
   - 写入正文，追加来源链接

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

### `/review` Review

**参数**：
- `note_path`: 笔记路径（可选，不指定则回顾收件箱）
- `--focus`: 关注重点

**`/review` 无参数行为**：

当调用 `/review` 不指定笔记路径时，自动扫描收件箱并返回处理建议。

**`/review inbox` 批量处理模式**：

当收件箱有多条内容时，支持批量处理：

```
📥 收件箱回顾
━━━━━━━━━━━━━━━━━━━━

待处理: 5 条

1. "学习Rust的想法"
   → 建议: /research Rust 或 /kickoff

2. "AI写作助手项目想法"
   → 建议: /kickoff AI写作助手 --area=工作

3. "看到一篇好文章链接"
   → 建议: /import 或 手动处理

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
```
处理第 1 条: "学习Rust的想法"

建议操作:
1. 启动研究笔记 /research Rust
2. 启动项目 /kickoff Rust学习
3. 暂不处理

选择？ 用户: 1

✅ 创建研究笔记: 30_研究/编程/Rust学习_2025-03-31.md
✅ 原想法已归档

继续处理下一条？ (y/n)
```

### `/health-check` Health Check

**参数**：
- `type`: "orphans" | "deadlinks" | "tags" | "all" (default: "all")

**无需额外用户输入**，直接执行并返回报告。

**PARA-aware orphan detection**:
- Strict: `30_研究/`, `40_知识库/` - must have links
- Relaxed: `00_收件箱/`, `10_项目/`, `Daily/` - temporary/in-progress

### `/mocs` MOC Management

**子命令**：

| 命令 | 参数 | 说明 |
|------|------|------|
| `list` | 无 | 列出所有 MOC 及其链接数、更新时间 |
| `open <name>` | name (必需) | 打开指定 MOC，支持模糊匹配名称 |
| `stats [name]` | name (可选) | 显示 MOC 统计；不指定则显示所有概览 |
| `create <name>` | name (必需), --area | 创建新 MOC |

**`/mocs stats` 无参数行为**：

当调用 `/mocs stats` 不指定 MOC 名称时，显示所有 MOC 的概览统计（而非某个 MOC 的详细统计）。输出格式与 `/mocs list` 类似，但额外包含健康度百分比。

**`/mocs list` 输出**：
```
🗺️ MOC 列表
━━━━━━━━━━━━━━━━━━━━

40_知识库/moc/
├── moc-编程.md          12 个链接  更新: 2天前
├── moc-工作.md           8 个链接  更新: 5天前
└── moc-个人成长.md       5 个链接  更新: 1周前

💡 提示: 使用 `/mocs open 编程` 快速打开
```

**`/mocs stats <name>` 输出**：
```
📊 MOC 统计: 编程
━━━━━━━━━━━━━━━━━━━━

笔记数: 12
健康度: 92%
⚠️  1 个死链
💡  3 个未链接的潜在相关笔记
```

### `/moc-review` MOC Maintenance

**参数**：
- `--area`: 指定领域
- `--path`: 指定 MOC 路径
- `--all`: 回顾所有 MOC

**执行步骤**：
1. 扫描指定 MOC 或领域的笔记
2. 排除：Daily、已归档、模板
3. AI 分析每篇笔记内容，建议归属的 MOC
4. 按 MOC 分组显示建议

**MOC 链接插入位置选择规则**：

当 Agent 向 MOC 添加新链接时，根据笔记类型选择合适的章节：

| 笔记类型 | 插入章节 | 原因 |
|---------|---------|------|
| project (进行中) | `## 进行中的项目` | 项目活动状态 |
| project (已完成) | `## 已完成项目` 或归档 | 项目完成状态 |
| research | `## 研究主题` | 研究主题归类 |
| knowledge | `## 知识库` | 知识点归类 |
| brainstorm | `## 相关思考` | 思考记录 |
| 其他 | `## 待归档` | 临时存放，等待进一步分类 |

**章节不存在时的处理**：
- 如 MOC 模板中定义了该章节 → 在章节末尾追加
- 如 MOC 中不存在该章节 → 在末尾新建章节并追加链接
- Agent 需判断章节是否存在，动态选择插入位置

**输出示例**：
```
🗺️ MOC 维护建议
━━━━━━━━━━━━━━━━━━━━

最近 7 天未链接笔记: 5 篇

建议链接到 [[moc-编程]]:
   ✅ [[Python 装饰器详解]]
   ✅ [[异步编程笔记]]

建议链接到 [[moc-工作]]:
   ✅ [[会议记录-项目启动]]

建议新建 MOC [[moc-机器学习]]:
   ⚠️ [[机器学习入门]] 无法匹配现有 MOC

确认执行？ (全部确认/逐项确认/取消)
```

## Agent Decision Guide

当参数未明确提供时，Agent 应按以下优先级决策：

| 参数类型 | 决策优先级 |
|---------|-----------|
| **area** | 1. 用户明确指定 → 使用指定值<br>2. 从上下文推断（如主题关键词）<br>3. 使用配置的 `default_area`<br>4. 询问用户 |
| **timeline** | 默认 "1个月"，用户提到时间相关词汇时调整 |
| **depth** | 默认 "深入学习"，用户提到"快速/概览"或"精通/深入"时调整 |
| **project** | 尝试从主题匹配现有项目名称，无匹配则询问 |

## Configuration

Config file: `~/.config/obsidian-kb/config.json`

```json
{
  "vault_path": "/path/to/ObsidianVault",
  "default_area": "编程",
  "quiet_mode": false,
  "auto_confirm_threshold": 0.8,
  "auto_confirm_actions": ["moc_link", "tag_extraction"],
  "templates": {
    "project": "99_模板/项目启动模板.md",
    "research": "99_模板/研究笔记模板.md",
    "brainstorm": "99_模板/头脑风暴模板.md",
    "daily": "99_模板/每日规划模板.md",
    "moc": "99_模板/MOC模板.md"
  },
  "backup": {
    "enabled": true,
    "retention_days": 30,
    "max_backups_per_day": 100
  }
}
```

**模板扩展**：

用户可添加自定义模板：

1. 在 `99_模板/` 创建新的 `.md` 文件
2. 使用 Jinja2 变量语法（`{{ VARIABLE }}`）
3. 在配置中注册

```json
// 添加读书笔记模板
"templates": {
  ...
  "reading": "99_模板/读书笔记模板.md"
}
```

使用：Agent 识别 "读书笔记" 关键词时自动使用该模板。

**模板变量**：

| 变量 | 说明 | 来源 |
|------|------|------|
| `{{ NOTE_ID }}` | 唯一标识符 | 自动生成 |
| `{{ DATE }}` | 当前日期 | 自动生成 |
| `{{ DATETIME }}` | 当前时间 | 自动生成 |
| `{{ AREA }}` | 所属领域 | 用户输入或推断 |
| `{{ TITLE }}` | 笔记标题 | 用户输入 |

## Backup & Recovery

### `/backup` Backup Notes

**参数**：
- `target`: 备份目标（可选，默认当前笔记）
- `--full`: 全量备份整个 Vault

**执行步骤**：

1. 确定备份范围（单笔记 / 全量）
2. 创建备份到 `metadata/backups/YYYY-MM-DD/`
3. 记录备份日志
4. 返回备份路径

**输出示例**：
```
📦 备份完成
━━━━━━━━━━━━━━━━━━━━

备份路径: metadata/backups/2025-03-31/manual/Python项目笔记.md.bak
备份时间: 2025-03-31 14:30
备份 ID: bk-20250331-143052

💡 使用 /restore bk-20250331-143052 恢复
```

### `/restore` Restore from Backup

**参数**：
- `backup-id`: 备份 ID（可选）
- `--list`: 列出可恢复的备份

**执行步骤**：

1. 如无参数 → 列出最近的可恢复操作
2. 展示操作列表让用户选择
3. 从备份恢复文件
4. 回滚相关链接更新
5. `obsidian reload`

**输出示例**：
```
📋 可恢复的操作
━━━━━━━━━━━━━━━━━━━━

1. [14:30] 归档 "Python项目笔记" ← 刚才
2. [11:20] 批量添加标签 (3个文件)
3. [09:15] 重命名 "旧项目" → "已完成项目"

选择要恢复的操作？ (1-3)

用户: 1

✅ 已恢复: 10_项目/编程/Python项目笔记.md
✅ 已回滚反向链接更新
✅ 已执行 obsidian reload
```

**备份保留策略**：

| 备份类型 | 保留时间 |
|---------|---------|
| 当天备份 | 永久 |
| 本周备份 | 7 天 |
| 更早备份 | 30 天 |

## Index Sync

After direct file modifications (link updates, content changes), the skill automatically calls `obsidian reload` to refresh Obsidian's search index. This ensures:

- Backlinks are updated correctly
- Search queries reflect latest changes
- Orphan/deadlink detection is accurate

## Note ID Format

All notes have unique IDs: `kb-YYYYMMDD-HHMMSS-XXXX`

- Stable reference across renames/moves
- Used for knowledge graph and embedding deduplication
- **Not exposed in wiki links** - links use readable titles

## References

For detailed information, read:
- `references/para-method.md` - PARA methodology guide
- `references/obsidian-cli-usage.md` - Obsidian CLI commands