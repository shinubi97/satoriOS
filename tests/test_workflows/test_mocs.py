"""MOC 管理工作流测试."""
import pytest
from pathlib import Path

from obsidian_kb.workflows.mocs import MocsWorkflow, MOCEntry, MOCContent
from obsidian_kb.config import Config
from obsidian_kb.vault import Vault


class TestMocsWorkflow:
    """MocsWorkflow 测试."""

    @pytest.fixture
    def setup_vault(self, temp_vault_for_workflow):
        """设置测试 Vault。"""
        vault_path = temp_vault_for_workflow

        # 创建项目
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
内容
""")

        # 创建研究笔记
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
内容
""")

        # 创建 MOC 目录
        mocs_path = vault_path / "40_知识库" / "moc"
        mocs_path.mkdir(parents=True, exist_ok=True)

        yield vault_path

    def test_execute_list_empty(self, temp_vault_for_workflow):
        """测试列出空 MOC。"""
        config = Config(vault_path=temp_vault_for_workflow)
        vault = Vault(temp_vault_for_workflow)
        workflow = MocsWorkflow(vault, config)

        result = workflow.execute()

        assert result.success is True
        assert "暂无 MOC" in result.message or result.data.get("mocs") == []

    def test_create_moc(self, setup_vault):
        """测试创建 MOC。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = MocsWorkflow(vault, config)

        result = workflow.create_moc("编程", "编程领域知识地图")

        assert result.success is True
        assert "已创建" in result.message
        assert len(result.created_files) >= 1

    def test_create_moc_already_exists(self, setup_vault):
        """测试创建已存在的 MOC。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = MocsWorkflow(vault, config)

        # 先创建
        workflow.create_moc("编程")

        # 再创建
        result = workflow.create_moc("编程")

        assert result.success is False
        assert "已存在" in result.message

    def test_get_moc(self, setup_vault):
        """测试获取 MOC。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = MocsWorkflow(vault, config)

        # 先创建
        workflow.create_moc("编程")

        # 获取
        result = workflow.get_moc("编程")

        assert result.success is True
        assert result.data["moc"]["area"] == "编程"

    def test_get_moc_not_found(self, setup_vault):
        """测试获取不存在的 MOC。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = MocsWorkflow(vault, config)

        result = workflow.get_moc("不存在的领域")

        assert result.success is False
        assert "不存在" in result.message

    def test_update_moc(self, setup_vault):
        """测试更新 MOC。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = MocsWorkflow(vault, config)

        # 先创建
        workflow.create_moc("编程")

        # 更新
        result = workflow.update_moc("编程")

        assert result.success is True
        assert "已更新" in result.message

    def test_collect_area_notes(self, setup_vault):
        """测试收集领域笔记。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = MocsWorkflow(vault, config)

        moc_content = workflow._collect_area_notes("编程")

        assert len(moc_content.projects) >= 1
        assert len(moc_content.researches) >= 1


class TestMOCEntry:
    """MOCEntry 数据类测试。"""

    def test_entry_creation(self):
        """测试创建 MOC 条目。"""
        entry = MOCEntry(
            path="10_项目/test.md",
            title="测试项目",
            note_type="project",
            relevance=0.9
        )

        assert entry.path == "10_项目/test.md"
        assert entry.title == "测试项目"
        assert entry.note_type == "project"
        assert entry.relevance == 0.9