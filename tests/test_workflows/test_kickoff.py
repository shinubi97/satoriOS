"""项目启动工作流测试."""
import pytest
from datetime import datetime
from pathlib import Path

from obsidian_kb.workflows.kickoff import KickoffWorkflow, ProjectDetails
from obsidian_kb.config import Config
from obsidian_kb.vault import Vault


class TestKickoffWorkflow:
    """KickoffWorkflow 测试."""

    @pytest.fixture
    def setup_vault(self, temp_vault_for_workflow):
        """设置测试 Vault。"""
        vault_path = temp_vault_for_workflow

        # 创建收件箱想法
        inbox_path = vault_path / "00_收件箱"
        (inbox_path / "学习Python的想法.md").write_text("""---
id: kb-20250328-100000-0001
title: 学习Python的想法
type: idea
date: 2025-03-28
---

想要系统学习 Python 编程，包括基础语法和高级特性。
""")

        # 创建已存在的项目（用于测试冲突）
        projects_path = vault_path / "10_项目" / "编程"
        (projects_path / "已有项目.md").write_text("""---
id: kb-20250301-100000-0002
title: 已有项目
type: project
date: 2025-03-01
status: 进行中
---

这是一个已存在的项目。
""")

        yield vault_path

    def test_execute_success(self, setup_vault):
        """测试成功启动项目。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = KickoffWorkflow(vault, config)

        result = workflow.execute(
            idea_name="学习Python的想法",
            area="编程",
            timeline="2个月",
            goals=["掌握基础语法", "理解面向对象"]
        )

        assert result.success is True
        assert "学习Python" in result.message or "Python" in result.message
        assert len(result.created_files) >= 1

    def test_execute_with_default_area(self, setup_vault):
        """测试使用默认领域。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = KickoffWorkflow(vault, config)

        result = workflow.execute(idea_name="学习Python的想法")

        assert result.success is True
        assert result.data is not None
        assert result.data["project"].area == "编程"

    def test_execute_idea_not_found(self, setup_vault):
        """测试想法不存在。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = KickoffWorkflow(vault, config)

        result = workflow.execute(idea_name="不存在的想法")

        assert result.success is False
        assert "未找到" in result.message

    def test_find_idea(self, setup_vault):
        """测试查找想法。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = KickoffWorkflow(vault, config)

        idea = workflow._find_idea("学习Python的想法")

        assert idea is not None
        assert "学习Python" in idea["title"]

    def test_find_matching_ideas(self, setup_vault):
        """测试查找多个匹配。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = KickoffWorkflow(vault, config)

        matches = workflow.find_matching_ideas("Python")

        assert len(matches) >= 1

    def test_archive_idea(self, setup_vault):
        """测试归档想法。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = KickoffWorkflow(vault, config)

        archived_path = workflow._archive_idea("00_收件箱/学习Python的想法.md")

        assert archived_path is not None
        assert "50_归档" in archived_path


class TestProjectDetails:
    """ProjectDetails 数据类测试。"""

    def test_project_details_creation(self):
        """测试创建项目详情。"""
        details = ProjectDetails(
            name="测试项目",
            area="编程",
            timeline="1个月",
            goals=["目标1", "目标2"],
            source_idea="原始想法"
        )

        assert details.name == "测试项目"
        assert details.area == "编程"
        assert details.timeline == "1个月"
        assert len(details.goals) == 2
        assert details.source_idea == "原始想法"

    def test_project_details_defaults(self):
        """测试默认值。"""
        details = ProjectDetails(
            name="项目",
            area="通用",
            timeline="1个月"
        )

        assert details.goals == []
        assert details.source_idea is None
        assert details.source_path is None