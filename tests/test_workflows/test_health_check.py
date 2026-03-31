"""健康检查工作流测试."""
import pytest
from pathlib import Path

from obsidian_kb.workflows.health_check import HealthCheckWorkflow, HealthReport, HealthIssue
from obsidian_kb.config import Config
from obsidian_kb.vault import Vault


class TestHealthCheckWorkflow:
    """HealthCheckWorkflow 测试."""

    @pytest.fixture
    def setup_vault(self, temp_vault_for_workflow):
        """设置测试 Vault。"""
        vault_path = temp_vault_for_workflow

        # 创建各种笔记
        # 项目
        projects_path = vault_path / "10_项目" / "编程"
        projects_path.mkdir(parents=True, exist_ok=True)
        (projects_path / "项目A.md").write_text("""---
id: kb-20260301-100000-0001
title: 项目A
type: project
area: 编程
date: 2026-03-01
status: 进行中
---

# 项目A

内容... [[相关笔记]]

- [ ] 待办项
""")

        # 研究
        research_path = vault_path / "30_研究" / "编程"
        research_path.mkdir(parents=True, exist_ok=True)
        (research_path / "研究笔记.md").write_text("""---
id: kb-20260301-100000-0002
title: 研究笔记
type: research
area: 编程
date: 2026-03-01
---

# 研究笔记

[[项目A]] 相关研究。
""")

        # 收件箱
        inbox_path = vault_path / "00_收件箱"
        inbox_path.mkdir(parents=True, exist_ok=True)
        (inbox_path / "新想法.md").write_text("""---
id: kb-20260301-100000-0003
title: 新想法
type: idea
date: 2026-03-01
---

一个新的想法。
""")

        yield vault_path

    def test_execute_success(self, setup_vault):
        """测试成功执行健康检查。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = HealthCheckWorkflow(vault, config)

        result = workflow.execute()

        assert result.success is True
        assert result.data["health"] is not None

    def test_collects_statistics(self, setup_vault):
        """测试收集统计信息。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = HealthCheckWorkflow(vault, config)

        result = workflow.execute()

        stats = result.data["health"].statistics
        assert "total_notes" in stats
        assert stats["total_notes"] >= 3

    def test_check_inbox(self, setup_vault):
        """测试检查收件箱。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = HealthCheckWorkflow(vault, config)

        issues = workflow._check_inbox()

        # 收件箱有 1 个笔记，不应该触发警告
        info_issues = [i for i in issues if i.severity == "info"]
        assert len(info_issues) <= 1

    def test_check_frontmatter(self, setup_vault):
        """测试检查 frontmatter。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = HealthCheckWorkflow(vault, config)

        notes = list(setup_vault.rglob("*.md"))
        issues = workflow._check_frontmatter(notes)

        # 所有笔记都有完整 frontmatter
        assert len(issues) == 0

    def test_generates_suggestions(self, setup_vault):
        """测试生成建议。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = HealthCheckWorkflow(vault, config)

        result = workflow.execute()

        assert isinstance(result.suggestions, list)


class TestHealthIssue:
    """HealthIssue 数据类测试。"""

    def test_issue_creation(self):
        """测试创建健康问题。"""
        issue = HealthIssue(
            severity="error",
            type="broken_link",
            path="test.md",
            description="失效链接",
            suggestion="修复链接"
        )

        assert issue.severity == "error"
        assert issue.type == "broken_link"
        assert issue.description == "失效链接"


class TestHealthReport:
    """HealthReport 数据类测试。"""

    def test_report_creation(self):
        """测试创建健康报告。"""
        report = HealthReport(
            check_date="2026-03-31",
            total_notes=10,
            issues=[],
            statistics={}
        )

        assert report.check_date == "2026-03-31"
        assert report.total_notes == 10
        assert report.issues == []