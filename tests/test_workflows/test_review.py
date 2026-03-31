"""回顾工作流测试."""
import pytest
from pathlib import Path

from obsidian_kb.workflows.review import ReviewWorkflow, ReviewDetails
from obsidian_kb.config import Config
from obsidian_kb.vault import Vault


class TestReviewWorkflow:
    """ReviewWorkflow 测试."""

    @pytest.fixture
    def setup_vault(self, temp_vault_for_workflow):
        """设置测试 Vault。"""
        vault_path = temp_vault_for_workflow

        # 创建项目笔记
        projects_path = vault_path / "10_项目" / "编程"
        projects_path.mkdir(parents=True, exist_ok=True)
        (projects_path / "测试项目.md").write_text("""---
id: kb-20260301-100000-0001
title: 测试项目
type: project
area: 编程
date: 2026-03-01
status: 进行中
---

# 测试项目

## 项目目标

- 目标 1
- 目标 2

## 下一步行动

- [ ] 完成任务 A
- [ ] 开始任务 B

## 相关资源

- [[相关笔记 1]]
- [[相关笔记 2]]
""")

        # 创建研究笔记
        research_path = vault_path / "30_研究" / "编程"
        research_path.mkdir(parents=True, exist_ok=True)
        (research_path / "测试研究.md").write_text("""---
id: kb-20260301-100000-0002
title: 测试研究
type: research
area: 编程
date: 2026-03-01
---

# 测试研究

## 核心结论

- 结论 1: 这是第一个核心结论
- 结论 2: 这是第二个核心结论

## 总结

这是研究的总结内容。
""")

        yield vault_path

    def test_execute_success(self, setup_vault):
        """测试成功回顾。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = ReviewWorkflow(vault, config)

        result = workflow.execute("10_项目/编程/测试项目.md")

        assert result.success is True
        assert result.data["review"] is not None

    def test_extract_action_items(self, setup_vault):
        """测试提取行动项。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = ReviewWorkflow(vault, config)

        result = workflow.execute("10_项目/编程/测试项目.md")

        assert result.success is True
        actions = result.data["review"].action_items
        assert len(actions) >= 2
        assert any("任务 A" in a for a in actions)

    def test_extract_related_notes(self, setup_vault):
        """测试提取相关笔记。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = ReviewWorkflow(vault, config)

        result = workflow.execute("10_项目/编程/测试项目.md")

        assert result.success is True
        related = result.data["review"].related_notes
        assert len(related) >= 2

    def test_extract_key_findings(self, setup_vault):
        """测试提取关键发现。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = ReviewWorkflow(vault, config)

        result = workflow.execute("30_研究/编程/测试研究.md")

        assert result.success is True
        findings = result.data["review"].key_findings
        assert len(findings) >= 1

    def test_execute_not_found(self, setup_vault):
        """测试笔记不存在。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = ReviewWorkflow(vault, config)

        result = workflow.execute("不存在的笔记.md")

        assert result.success is False
        assert "不存在" in result.message

    def test_review_project(self, setup_vault):
        """测试项目回顾。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = ReviewWorkflow(vault, config)

        result = workflow.review_project("10_项目/编程/测试项目.md")

        assert result.success is True
        assert result.data["review"].note_type == "project"

    def test_review_research(self, setup_vault):
        """测试研究回顾。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = ReviewWorkflow(vault, config)

        result = workflow.review_research("30_研究/编程/测试研究.md")

        assert result.success is True
        assert result.data["review"].note_type == "research"


class TestReviewDetails:
    """ReviewDetails 数据类测试。"""

    def test_details_creation(self):
        """测试创建回顾详情。"""
        details = ReviewDetails(
            note_path="10_项目/test.md",
            note_type="project",
            review_date="2026-03-31",
            key_findings=["发现 1", "发现 2"],
            action_items=["行动 1", "行动 2"]
        )

        assert details.note_type == "project"
        assert len(details.key_findings) == 2
        assert len(details.action_items) == 2