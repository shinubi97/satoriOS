"""每日规划工作流测试."""
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from obsidian_kb.workflows.start_my_day import (
    StartMyDayWorkflow, InboxItem, ProjectSummary, TaskItem, DailyPlanData
)
from obsidian_kb.config import Config
from obsidian_kb.vault import Vault


class TestStartMyDayWorkflow:
    """StartMyDayWorkflow 测试."""

    @pytest.fixture
    def setup_vault(self, temp_vault_for_workflow):
        """设置测试 Vault。"""
        vault_path = temp_vault_for_workflow

        # 创建收件箱项目
        inbox_path = vault_path / "00_收件箱"
        (inbox_path / "项目想法A.md").write_text("""---
id: kb-20250328-100000-0001
title: 项目想法A
type: idea
date: 2025-03-28
tags: [项目]
---

这是一个关于学习 Python 的项目想法。
""")
        (inbox_path / "研究主题B.md").write_text("""---
id: kb-20250329-100000-0002
title: 研究主题B
type: research
date: 2025-03-29
---

想要深入研究异步编程。
""")

        # 创建进行中项目
        projects_path = vault_path / "10_项目" / "编程"
        (projects_path / "Python项目.md").write_text("""---
id: kb-20250301-100000-0003
title: Python项目
type: project
date: 2025-03-01
status: 进行中
area: 编程
---

## 进展记录

已完成基础语法学习。
""")

        # 创建今日笔记和待办
        daily_path = vault_path / "Daily"
        today = datetime.now().strftime("%Y-%m-%d")
        (daily_path / f"{today}.md").write_text("""---
id: kb-{today}-100000-0004
title: 每日规划
type: daily-note
date: {today}
---

## 今日待办

- [ ] 完成测试
- [ ] 提交代码
""".replace("{today}", today))

        yield vault_path

    def test_execute_success(self, setup_vault):
        """测试执行成功。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = StartMyDayWorkflow(vault, config)

        result = workflow.execute()

        assert result.success is True
        assert "每日规划已生成" in result.message
        assert result.data is not None
        assert "plan" in result.data

    def test_scan_inbox(self, setup_vault):
        """测试扫描收件箱。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = StartMyDayWorkflow(vault, config)

        inbox_items = workflow._scan_inbox()

        assert len(inbox_items) == 2
        assert any(item.title == "项目想法A" for item in inbox_items)
        assert any(item.title == "研究主题B" for item in inbox_items)

    def test_list_active_projects(self, setup_vault):
        """测试列出进行中项目。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = StartMyDayWorkflow(vault, config)

        projects = workflow._list_active_projects()

        assert len(projects) >= 1
        assert any("Python" in p.name for p in projects)

    def test_extract_todos(self, setup_vault):
        """测试提取待办。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = StartMyDayWorkflow(vault, config)

        todos = workflow._extract_todos()

        assert len(todos) >= 2
        assert any("完成测试" in t.text for t in todos)
        assert any("提交代码" in t.text for t in todos)

    def test_generate_suggestions(self, setup_vault):
        """测试生成建议。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = StartMyDayWorkflow(vault, config)

        inbox_items = [InboxItem(
            path="00_收件箱/test.md",
            title="测试",
            age_days=1,
            summary="测试摘要",
            suggested_action="kickoff"
        )]
        projects = [ProjectSummary(
            path="10_项目/测试.md",
            name="测试项目",
            area="编程",
            status="进行中",
            progress="进行中"
        )]

        suggestions = workflow._generate_suggestions(inbox_items, projects, [])

        assert len(suggestions) > 0
        assert any("kickoff" in s.lower() or "项目想法" in s for s in suggestions)


class TestInboxItem:
    """InboxItem 数据类测试。"""

    def test_inbox_item_creation(self):
        """测试创建收件箱项目。"""
        item = InboxItem(
            path="00_收件箱/test.md",
            title="测试项目",
            age_days=5,
            summary="这是一个测试项目",
            suggested_action="kickoff"
        )

        assert item.path == "00_收件箱/test.md"
        assert item.title == "测试项目"
        assert item.age_days == 5
        assert item.suggested_action == "kickoff"


class TestProjectSummary:
    """ProjectSummary 数据类测试。"""

    def test_project_summary_creation(self):
        """测试创建项目摘要。"""
        project = ProjectSummary(
            path="10_项目/编程/Python.md",
            name="Python项目",
            area="编程",
            status="进行中",
            progress="已完成基础学习"
        )

        assert project.name == "Python项目"
        assert project.area == "编程"
        assert project.status == "进行中"


class TestTaskItem:
    """TaskItem 数据类测试。"""

    def test_task_item_creation(self):
        """测试创建待办事项。"""
        task = TaskItem(
            text="完成测试",
            source="Daily/2025-03-30.md",
            priority="high"
        )

        assert task.text == "完成测试"
        assert task.source == "Daily/2025-03-30.md"
        assert task.priority == "high"

    def test_task_item_default_priority(self):
        """测试默认优先级。"""
        task = TaskItem(
            text="测试",
            source="Daily/test.md"
        )

        assert task.priority == "normal"