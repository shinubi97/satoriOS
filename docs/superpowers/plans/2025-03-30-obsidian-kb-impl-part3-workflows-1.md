# Obsidian Knowledge Base 技能实施计划 - Part 3: 核心工作流 (上)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现四个核心工作流：每日规划、项目启动、研究笔记、头脑风暴。

**Architecture:** 每个工作流作为独立模块，遵循"询问 → 执行 → 反馈"模式，支持高置信度自动执行。

**Tech Stack:** Python 3.8+, click (CLI), pydantic (数据验证)

---

## 项目文件结构（本 Part 新增）

```
src/obsidian_kb/workflows/
├── __init__.py
├── base.py              # 工作流基类
├── start_my_day.py      # 每日规划
├── kickoff.py           # 项目启动
├── research.py          # 研究笔记
└── brainstorm.py        # 头脑风暴
tests/test_workflows/
├── test_start_my_day.py
├── test_kickoff.py
├── test_research.py
└── test_brainstorm.py
```

---

## Task 3.1: 工作流基类

**Files:**
- Create: `src/obsidian_kb/workflows/base.py`

### 设计理念

**重要**：这个 skill 是给 AI Agent 用的，不是传统软件。

- **传统软件**：代码内处理用户交互（弹窗、表单、按钮）
- **Agent Skill**：SKILL.md 写清楚交互步骤，Agent 自己决定如何与用户沟通

因此：
- 工作流代码**不处理交互**，只负责执行操作
- 所有需要的参数由 Agent 收集后传入
- 返回值清晰描述执行结果

### 核心接口

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class WorkflowResult:
    """工作流执行结果。"""
    success: bool
    message: str
    created_files: List[str]
    modified_files: List[str]
    suggestions: List[str]
    data: Dict[str, Any] = None

class BaseWorkflow(ABC):
    """工作流基类。
    
    注意：不包含交互逻辑。所有参数由 Agent 收集后传入。
    交互步骤在 SKILL.md 中描述，Agent 负责与用户沟通。
    """

    def __init__(self, vault: Vault, config: Config):
        self.vault = vault
        self.config = config

    @abstractmethod
    def execute(self, **kwargs) -> WorkflowResult:
        """执行工作流。
        
        Args 由 Agent 根据用户输入和 SKILL.md 说明收集。
        """
        pass
```

---

## Task 3.2: `/start-my-day` 每日规划工作流

**Files:**
- Create: `src/obsidian_kb/workflows/start_my_day.py`
- Create: `tests/test_workflows/test_start_my_day.py`

### SKILL.md 交互说明

```
此命令无需用户输入参数，直接执行即可。
Agent 可选：询问用户是否要执行建议的下一步操作。
```

### 工作流程

```
1. 检查 Daily/YYYY-MM-DD.md 是否存在
   ├─ 存在 → 读取现有内容，智能合并模式
   └─ 不存在 → 创建新笔记

2. 扫描收件箱 (限制 5 个笔记)
   └─ 提取 frontmatter + 前 200 字符摘要

3. 列出进行中项目
   └─ obsidian search query="#进行中" path="10_项目"

4. 提取今日待办
   └─ obsidian tasks todo path="Daily"

5. 生成建议
   └─ AI 分析 + 优先级排序

6. 输出结构化报告
```

### 核心接口

```python
class StartMyDayWorkflow(BaseWorkflow):
    """每日规划工作流。无需参数，直接执行。"""
    
    def execute(self) -> WorkflowResult:
        """执行每日规划，返回今日报告和建议。"""
        pass

@dataclass
class DailyPlanResult:
    date: str
    inbox_count: int
    inbox_items: List[InboxItem]  # 最多 5 个
    active_projects: List[ProjectSummary]
    todos: List[TaskItem]
    suggestions: List[str]

@dataclass
class InboxItem:
    path: str
    title: str
    age_days: int
    suggested_action: str  # "kickoff" | "archive"
```

---

## Task 3.3: `/kickoff` 项目启动工作流

**Files:**
- Create: `src/obsidian_kb/workflows/kickoff.py`
- Create: `tests/test_workflows/test_kickoff.py`

### SKILL.md 交互说明

```
此命令需要 Agent 收集以下信息：

1. idea_name (必需): 想法/项目名称
2. 如果在收件箱找到多个匹配 → 让用户选择一个
3. area (可选): 项目所属领域，默认配置中的 default_area
4. timeline (可选): 期望完成时间，默认 "1个月"
5. goals (可选): 项目目标列表
6. 执行完成后 → 询问用户是否要链接到相关 MOC
```

### 工作流程

```
1. 查找原想法
   └─ 在 00_收件箱/ 搜索匹配的笔记

2. 创建项目文档
   └─ 使用模板: 99_模板/项目启动模板.md

3. 归档原想法
   └─ 移动到 50_归档/YYYY-MM/

4. 返回结果，包含 MOC 链接建议
```

### 核心接口

```python
class KickoffWorkflow(BaseWorkflow):
    """项目启动工作流。"""
    
    def execute(
        self,
        idea_name: str,
        area: str = None,
        timeline: str = "1个月",
        goals: List[str] = None,
        link_to_moc: str = None
    ) -> WorkflowResult:
        """启动新项目。
        
        Args:
            idea_name: 想法名称（用于搜索匹配）
            area: 所属领域
            timeline: 期望完成时间
            goals: 项目目标列表
            link_to_moc: 要链接的 MOC 名称（可选）
        """
        pass

@dataclass
class ProjectDetails:
    name: str
    area: str
    timeline: str
    goals: List[str]
    source_idea: Optional[str]
```

---

## Task 3.4: `/research` 研究笔记工作流

**Files:**
- Create: `src/obsidian_kb/workflows/research.py`
- Create: `tests/test_workflows/test_research.py`

### SKILL.md 交互说明

```
此命令需要 Agent 收集以下信息：

1. topic (必需): 研究主题
2. area (可选): 所属领域，用于确定存储路径
3. depth (可选): 研究深度，"快速了解" | "深入学习" | "精通掌握"，默认 "深入学习"
4. 执行完成后 → 询问用户是否要链接到相关 MOC
```

### 工作流程

```
1. 检查是否已存在相同主题研究
   └─ 如存在，提示用户

2. 深度调研
   └─ AI 搜索/分析，提取核心概念

3. 创建研究笔记
   └─ 30_研究/<领域>/<主题>_YYYY-MM-DD.md

4. 提取核心知识
   └─ 将核心概念提取到 40_知识库/

5. 返回结果，包含 MOC 链接建议
```

### 核心接口

```python
class ResearchWorkflow(BaseWorkflow):
    """研究笔记工作流。"""
    
    def execute(
        self,
        topic: str,
        area: str = None,
        depth: str = "深入学习",
        link_to_moc: str = None
    ) -> WorkflowResult:
        """创建研究笔记。
        
        Args:
            topic: 研究主题
            area: 所属领域
            depth: 研究深度
            link_to_moc: 要链接的 MOC 名称
        """
        pass
```

---

## Task 3.5: `/brainstorm` 头脑风暴工作流

**Files:**
- Create: `src/obsidian_kb/workflows/brainstorm.py`
- Create: `tests/test_workflows/test_brainstorm.py`

### SKILL.md 交互说明

```
此命令需要 Agent 收集以下信息：

1. topic (必需): 头脑风暴主题
2. project (可选): 关联的项目名称
3. area (可选): 所属领域
4. initial_idea (可选): 初始想法描述

执行后：
- 头脑风暴笔记已创建
- Agent 可继续与用户对话，追加内容到笔记
- 对话结束后 → 询问用户是否将精华追加到项目文档
```

### 工作流程

```
1. 查找关联项目（如果提供了 project 参数）

2. 创建头脑风暴笔记
   └─ 10_项目/<领域>/<项目名>_头脑风暴_YYYY-MM-DD.md

3. 返回笔记路径，Agent 可继续对话追加内容
```

### 核心接口

```python
class BrainstormWorkflow(BaseWorkflow):
    """头脑风暴工作流。"""
    
    def execute(
        self,
        topic: str,
        project: str = None,
        area: str = None,
        initial_idea: str = None
    ) -> WorkflowResult:
        """创建头脑风暴笔记。
        
        Args:
            topic: 头脑风暴主题
            project: 关联的项目名称
            area: 所属领域
            initial_idea: 初始想法描述
        
        Returns:
            包含创建的笔记路径，Agent 可继续对话追加内容
        """
        pass

    def append_to_note(self, note_path: str, content: str) -> None:
        """追加内容到头脑风暴笔记（用于多轮对话）。"""
        pass

    def extract_insights(self, note_path: str) -> BrainstormInsights:
        """从头脑风暴笔记中提取精华。"""
        pass

    def update_project(self, project_name: str, insights: BrainstormInsights) -> None:
        """将精华追加到项目文档。"""
        pass

@dataclass
class BrainstormInsights:
    core_conclusions: List[str]
    viable_solutions: List[str]
    next_actions: List[str]
```

---

## Part 3 完成检查清单

- [ ] 工作流基类完成 (base.py)
- [ ] `/start-my-day` 工作流完成
- [ ] `/kickoff` 工作流完成
- [ ] `/research` 工作流完成
- [ ] `/brainstorm` 工作流完成
- [ ] 所有测试通过

**下一步:** Part 4 将实现归档、查询、回顾、健康检查等工作流。