# Obsidian Knowledge Base 技能实施计划 - Part 6: 模板系统

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现模板管理模块和六个标准模板文件，支持变量替换和自定义模板。

**Architecture:** 模板使用 Jinja2 语法，支持变量替换和条件渲染。

**Tech Stack:** Python 3.8+, jinja2 (模板引擎)

---

## 项目文件结构（本 Part 新增）

```
# 模板文件存放在 Vault 内，方便用户自定义
<Vault>/
└── 99_模板/
    ├── 项目启动模板.md
    ├── 研究笔记模板.md
    ├── 头脑风暴模板.md
    ├── 每日规划模板.md
    └── MOC模板.md

src/obsidian_kb/utils/
└── templates.py          # 模板管理模块
tests/
└── test_utils/
    └── test_templates.py
```

---

## Task 6.1: 模板管理模块

**Files:**
- Create: `src/obsidian_kb/utils/templates.py`
- Create: `tests/test_utils/test_templates.py`

### 核心接口

```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Dict, Any

class TemplateManager:
    """模板管理器。"""

    def __init__(self, template_dir: Path):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False
        )

    def render(self, template_name: str, variables: Dict[str, Any]) -> str:
        """渲染模板。"""
        pass

    def get_template(self, template_name: str) -> Template:
        """获取模板对象。"""
        pass

    def list_templates(self) -> List[str]:
        """列出所有可用模板。"""
        pass

# 标准变量
STANDARD_VARIABLES = {
    "NOTE_ID": "kb-YYYYMMDD-HHMMSS-XXXX",  # 自动生成
    "DATE": "YYYY-MM-DD",
    "DATETIME": "YYYY-MM-DD HH:MM",
    "PROJECT_NAME": "",
    "AREA": "",
    "TITLE": "",
    "SOURCE_NOTE": "",
}
```

---

## Task 6.2: 项目启动模板

**Files:**
- Create: `templates/project.md`

### 模板内容

```markdown
---
id: {{ NOTE_ID }}
type: project
title: {{ PROJECT_NAME }}
date: {{ DATE }}
created: {{ DATETIME }}
updated: {{ DATETIME }}
tags: [项目, {{ AREA }}]
status: 进行中
area: {{ AREA }}
mocs:
  - "moc-{{ AREA }}"
---

# {{ PROJECT_NAME }}

> 创建于 {{ DATE }} | 来自: {{ SOURCE_NOTE }}

---

## 项目目标

{{ PROJECT_GOAL }}

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

- **开始日期**: {{ DATE }}
- **目标完成**: {{ TARGET_DATE }}
- **实际完成**:

## 相关资源

- [资源链接]
- [[相关笔记]]

## 进展记录

### {{ DATE }} - 启动
项目启动，初始规划完成。

## 复盘总结

（项目完成后填写）
```

---

## Task 6.3: 研究笔记模板

**Files:**
- Create: `templates/research.md`

### 模板内容

```markdown
---
id: {{ NOTE_ID }}
type: research
title: {{ RESEARCH_TOPIC }}
date: {{ DATE }}
created: {{ DATETIME }}
updated: {{ DATETIME }}
tags: [研究, {{ AREA }}]
status: 进行中
area: {{ AREA }}
mocs:
  - "moc-{{ AREA }}"
---

# {{ RESEARCH_TOPIC }} 研究笔记

> 研究领域: {{ AREA }} | 开始日期: {{ DATE }}

---

## 研究概述

{{ OVERVIEW }}

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

---

## Task 6.4: 头脑风暴模板

**Files:**
- Create: `templates/brainstorm.md`

### 模板内容

```markdown
---
id: {{ NOTE_ID }}
type: brainstorm
title: {{ TOPIC }} 头脑风暴
date: {{ DATE }}
created: {{ DATETIME }}
updated: {{ DATETIME }}
tags: [头脑风暴, {{ AREA }}]
area: {{ AREA }}
related_project: "[[{{ PROJECT }}]]"
---

# {{ TOPIC }} 头脑风暴

> 关联项目: [[{{ PROJECT }}]] | 日期: {{ DATE }}

---

## 原始想法

{{ INITIAL_IDEA }}

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

---

## Task 6.5: 每日规划模板

**Files:**
- Create: `templates/daily.md`

### 模板内容

```markdown
---
id: {{ NOTE_ID }}
type: daily-note
title: {{ DATE }} 每日规划
date: {{ DATE }}
created: {{ DATETIME }}
tags: [每日规划]
inbox_count: 0
active_projects: 0
todo_count: 0
---

# {{ DATE }} 每日规划

---

## 今日重点

（手动填写或 AI 建议）

## 收件箱待处理

{{ INBOX_ITEMS }}

## 进行中项目

{{ ACTIVE_PROJECTS }}

## 今日待办

{{ TODOS }}

---

## 今日记录

（手动填写今日进展）

## 明日计划

（手动填写）
```

---

## Task 6.6: MOC 模板

**Files:**
- Create: `templates/moc.md`

### 模板内容

```markdown
---
id: {{ NOTE_ID }}
type: moc
title: {{ AREA }} MOC
date: {{ DATE }}
created: {{ DATETIME }}
updated: {{ DATETIME }}
tags: [MOC, {{ AREA }}]
area: {{ AREA }}
---

# {{ AREA }} MOC

> 汇集所有 {{ AREA }} 相关的笔记、项目和资源
> 最后更新: {{ DATETIME }}

---

## 进行中的项目

{{ PROJECTS_IN_PROGRESS }}

## 研究主题

{{ RESEARCH_TOPICS }}

## 知识库

{{ KNOWLEDGE_BASE }}

## 待归档

{{ ARCHIVE_CANDIDATES }}

## 相关资源

- [外部资源](URL)

---

**统计:**
- 项目: {{ PROJECT_COUNT }}
- 研究: {{ RESEARCH_COUNT }}
- 知识: {{ KNOWLEDGE_COUNT }}
- 总计: {{ TOTAL_COUNT }}
```

---

## Part 6 完成检查清单

- [ ] 模板管理模块完成 (templates.py)
- [ ] 项目启动模板完成 (project.md)
- [ ] 研究笔记模板完成 (research.md)
- [ ] 头脑风暴模板完成 (brainstorm.md)
- [ ] 每日规划模板完成 (daily.md)
- [ ] MOC 模板完成 (moc.md)
- [ ] 所有测试通过

**下一步:** Part 7 将编写 SKILL.md 技能定义文件。