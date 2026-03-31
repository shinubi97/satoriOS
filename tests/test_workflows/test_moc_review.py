"""MOC 回顾工作流测试."""
import pytest
from pathlib import Path

from obsidian_kb.workflows.moc_review import MocReviewWorkflow, MOCReviewResult
from obsidian_kb.config import Config
from obsidian_kb.vault import Vault


class TestMocReviewWorkflow:
    """MocReviewWorkflow 测试."""

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

        # 创建 MOC
        mocs_path = vault_path / "40_资源" / "mocs"
        mocs_path.mkdir(parents=True, exist_ok=True)
        (mocs_path / "moc-编程.md").write_text("""---
id: kb-20260301-100000-0003
title: 编程 MOC
type: moc
area: 编程
date: 2026-03-01
---

# 编程 MOC

## 相关项目

- [[项目A]]

## 研究笔记

- [[研究笔记]]

## 待探索

- [ ] 探索主题 1
""")

        yield vault_path

    def test_execute_success(self, setup_vault):
        """测试成功回顾 MOC。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = MocReviewWorkflow(vault, config)

        result = workflow.execute(area="编程")

        assert result.success is True
        assert result.data["review"] is not None

    def test_execute_with_path(self, setup_vault):
        """测试使用路径回顾 MOC。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = MocReviewWorkflow(vault, config)

        result = workflow.execute(moc_path="40_资源/mocs/moc-编程.md")

        assert result.success is True

    def test_execute_not_found(self, setup_vault):
        """测试 MOC 不存在。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = MocReviewWorkflow(vault, config)

        result = workflow.execute(area="不存在的领域")

        assert result.success is False
        assert "不存在" in result.message

    def test_check_broken_links(self, setup_vault):
        """测试检查失效链接。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = MocReviewWorkflow(vault, config)

        # 添加一个失效链接到 MOC
        moc_path = setup_vault / "40_资源" / "mocs" / "moc-编程.md"
        content = moc_path.read_text(encoding="utf-8")
        moc_path.write_text(content + "\n- [[不存在的笔记]]", encoding="utf-8")

        result = workflow.execute(area="编程")

        assert result.success is True
        assert result.data["review"].broken_links >= 1

    def test_check_missing_notes(self, setup_vault):
        """测试检查遗漏笔记。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = MocReviewWorkflow(vault, config)

        # 创建一个不在 MOC 中的新项目
        projects_path = setup_vault / "10_项目" / "编程"
        (projects_path / "新项目.md").write_text("""---
id: kb-20260301-100000-0004
title: 新项目
type: project
area: 编程
date: 2026-03-01
---

# 新项目
内容
""")

        result = workflow.execute(area="编程")

        assert result.success is True
        assert len(result.data["review"].missing_notes) >= 1

    def test_review_all_mocs(self, setup_vault):
        """测试回顾所有 MOC。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = MocReviewWorkflow(vault, config)

        result = workflow.review_all_mocs()

        assert result.success is True
        assert len(result.data["reviews"]) >= 1


class TestMOCReviewResult:
    """MOCReviewResult 数据类测试。"""

    def test_result_creation(self):
        """测试创建回顾结果。"""
        result = MOCReviewResult(
            moc_path="40_资源/mocs/moc-编程.md",
            area="编程",
            total_links=10,
            broken_links=2
        )

        assert result.moc_path == "40_资源/mocs/moc-编程.md"
        assert result.area == "编程"
        assert result.total_links == 10
        assert result.broken_links == 2