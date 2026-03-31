"""研究笔记工作流测试."""
import pytest
from datetime import datetime
from pathlib import Path

from obsidian_kb.workflows.research import ResearchWorkflow, ResearchDetails
from obsidian_kb.config import Config
from obsidian_kb.vault import Vault


class TestResearchWorkflow:
    """ResearchWorkflow 测试."""

    @pytest.fixture
    def setup_vault(self, temp_vault_for_workflow):
        """设置测试 Vault。"""
        vault_path = temp_vault_for_workflow

        # 创建已存在的研究笔记（用于测试检查重复）
        research_path = vault_path / "30_研究" / "编程"
        research_path.mkdir(parents=True, exist_ok=True)
        (research_path / "Python基础_2025-03-01.md").write_text("""---
id: kb-20250301-100000-0001
title: Python基础 研究笔记
type: research
area: 编程
date: 2025-03-01
---

# Python基础 研究笔记

已有研究笔记内容。
""")

        yield vault_path

    def test_execute_success(self, setup_vault):
        """测试成功创建研究笔记。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = ResearchWorkflow(vault, config)

        result = workflow.execute(
            topic="机器学习入门",
            area="编程",
            depth="深入学习"
        )

        assert result.success is True
        assert "机器学习" in result.message or "研究笔记" in result.message
        assert len(result.created_files) >= 1

    def test_execute_with_default_area(self, setup_vault):
        """测试使用默认领域。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = ResearchWorkflow(vault, config)

        result = workflow.execute(topic="数据结构")

        assert result.success is True
        assert result.data is not None
        assert result.data["research"].area == "编程"

    def test_execute_existing_research(self, setup_vault):
        """测试已存在相关研究。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = ResearchWorkflow(vault, config)

        result = workflow.execute(topic="Python基础")

        assert result.success is True
        assert "已存在" in result.message
        assert result.data.get("existing_research") is not None

    def test_normalize_depth_quick(self, setup_vault):
        """测试标准化深度 - 快速了解。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = ResearchWorkflow(vault, config)

        # 测试各种表达方式
        assert workflow._normalize_depth("快速") == "快速了解"
        assert workflow._normalize_depth("概览") == "快速了解"
        assert workflow._normalize_depth("quick") == "快速了解"
        assert workflow._normalize_depth("overview") == "快速了解"

    def test_normalize_depth_deep(self, setup_vault):
        """测试标准化深度 - 深入学习。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = ResearchWorkflow(vault, config)

        assert workflow._normalize_depth("深入") == "深入学习"
        assert workflow._normalize_depth("系统") == "深入学习"
        assert workflow._normalize_depth("deep") == "深入学习"

    def test_normalize_depth_master(self, setup_vault):
        """测试标准化深度 - 精通掌握。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = ResearchWorkflow(vault, config)

        assert workflow._normalize_depth("精通") == "精通掌握"
        assert workflow._normalize_depth("掌握") == "精通掌握"
        assert workflow._normalize_depth("master") == "精通掌握"
        assert workflow._normalize_depth("expert") == "精通掌握"

    def test_check_existing_research(self, setup_vault):
        """测试检查已存在研究。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = ResearchWorkflow(vault, config)

        existing = workflow._check_existing_research("Python基础", "编程")
        assert existing is not None
        assert "Python基础" in existing

    def test_check_existing_research_not_found(self, setup_vault):
        """测试不存在的研究。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = ResearchWorkflow(vault, config)

        existing = workflow._check_existing_research("不存在的研究", "编程")
        assert existing is None

    def test_create_research_note_quick(self, setup_vault):
        """测试创建快速了解研究笔记。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = ResearchWorkflow(vault, config)

        note_path = workflow._create_research_note(
            topic="快速测试",
            area="编程",
            depth="快速了解"
        )

        assert note_path is not None
        assert "快速测试" in note_path

        # 验证文件内容
        full_path = setup_vault / note_path
        content = full_path.read_text(encoding="utf-8")
        assert "快速概览" in content

    def test_create_research_note_master(self, setup_vault):
        """测试创建精通掌握研究笔记。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = ResearchWorkflow(vault, config)

        note_path = workflow._create_research_note(
            topic="精通测试",
            area="编程",
            depth="精通掌握"
        )

        assert note_path is not None

        # 验证文件内容
        full_path = setup_vault / note_path
        content = full_path.read_text(encoding="utf-8")
        assert "全面精通" in content
        assert "进阶主题" in content


class TestResearchDetails:
    """ResearchDetails 数据类测试。"""

    def test_research_details_creation(self):
        """测试创建研究详情。"""
        details = ResearchDetails(
            topic="测试主题",
            area="编程",
            depth="深入学习"
        )

        assert details.topic == "测试主题"
        assert details.area == "编程"
        assert details.depth == "深入学习"

    def test_research_details_defaults(self):
        """测试默认值。"""
        details = ResearchDetails(
            topic="主题",
            area="通用",
            depth="深入学习"
        )

        assert details.existing_research is None