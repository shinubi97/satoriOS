"""归档工作流测试."""
import pytest
from pathlib import Path

from obsidian_kb.workflows.archive import ArchiveWorkflow, ArchiveDetails
from obsidian_kb.config import Config
from obsidian_kb.vault import Vault


class TestArchiveWorkflow:
    """ArchiveWorkflow 测试."""

    @pytest.fixture
    def setup_vault(self, temp_vault_for_workflow):
        """设置测试 Vault。"""
        vault_path = temp_vault_for_workflow

        # 创建要归档的笔记
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

这是一个测试项目。
""")

        yield vault_path

    def test_execute_success(self, setup_vault):
        """测试成功归档。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = ArchiveWorkflow(vault, config)

        result = workflow.execute("10_项目/编程/测试项目.md")

        assert result.success is True
        assert "已归档" in result.message
        assert len(result.created_files) >= 1

    def test_archive_moves_file(self, setup_vault):
        """测试归档移动文件。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = ArchiveWorkflow(vault, config)

        original_path = setup_vault / "10_项目" / "编程" / "测试项目.md"
        assert original_path.exists()

        result = workflow.execute("10_项目/编程/测试项目.md")

        assert result.success is True
        # 原文件应该被移动
        assert not original_path.exists()
        # 归档文件应该存在
        assert "50_归档" in result.created_files[0]

    def test_execute_not_found(self, setup_vault):
        """测试笔记不存在。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = ArchiveWorkflow(vault, config)

        result = workflow.execute("不存在的笔记.md")

        assert result.success is False
        assert "不存在" in result.message

    def test_archive_with_reason(self, setup_vault):
        """测试带原因归档。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = ArchiveWorkflow(vault, config)

        result = workflow.execute(
            "10_项目/编程/测试项目.md",
            reason="项目已完成"
        )

        assert result.success is True
        assert result.data["archive"].reason == "项目已完成"


class TestArchiveDetails:
    """ArchiveDetails 数据类测试。"""

    def test_details_creation(self):
        """测试创建归档详情。"""
        details = ArchiveDetails(
            original_path="10_项目/测试.md",
            archived_path="50_归档/2026-03/测试.md",
            archive_date="2026-03-31",
            reason="完成"
        )

        assert details.original_path == "10_项目/测试.md"
        assert details.archived_path == "50_归档/2026-03/测试.md"
        assert details.reason == "完成"