"""头脑风暴工作流测试."""
import pytest
from datetime import datetime, date
from pathlib import Path

from obsidian_kb.workflows.brainstorm import BrainstormWorkflow, BrainstormInsights
from obsidian_kb.config import Config
from obsidian_kb.vault import Vault


class TestBrainstormWorkflow:
    """BrainstormWorkflow 测试."""

    @pytest.fixture
    def setup_vault(self, temp_vault_for_workflow):
        """设置测试 Vault。"""
        vault_path = temp_vault_for_workflow

        # 创建项目笔记（用于测试关联）
        projects_path = vault_path / "10_项目" / "编程"
        projects_path.mkdir(parents=True, exist_ok=True)
        (projects_path / "学习Python.md").write_text("""---
id: kb-20250301-100000-0001
title: 学习Python
type: project
area: 编程
date: 2025-03-01
status: 进行中
---

# 学习Python

项目内容。
""")

        yield vault_path

    def test_execute_success(self, setup_vault):
        """测试成功创建头脑风暴笔记。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = BrainstormWorkflow(vault, config)

        result = workflow.execute(
            topic="如何高效学习编程",
            area="编程",
            initial_idea="想要找到更高效的学习方法"
        )

        assert result.success is True
        assert "头脑风暴" in result.message or "高效学习" in result.message
        assert len(result.created_files) >= 1

    def test_execute_with_project(self, setup_vault):
        """测试关联项目的头脑风暴。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = BrainstormWorkflow(vault, config)

        result = workflow.execute(
            topic="Python学习方法",
            project="学习Python",
            initial_idea="讨论Python学习策略"
        )

        assert result.success is True
        assert result.data.get("project") == "学习Python"

    def test_execute_with_default_area(self, setup_vault):
        """测试使用默认领域。"""
        config = Config(
            vault_path=setup_vault,
            default_area="编程"
        )
        vault = Vault(setup_vault)
        workflow = BrainstormWorkflow(vault, config)

        result = workflow.execute(topic="测试头脑风暴")

        assert result.success is True
        assert result.data["area"] == "编程"

    def test_infer_area_from_project(self, setup_vault):
        """测试从项目推断领域。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = BrainstormWorkflow(vault, config)

        area = workflow._infer_area_from_project("学习Python")
        assert area == "编程"

    def test_infer_area_from_project_not_found(self, setup_vault):
        """测试项目不存在时推断领域。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = BrainstormWorkflow(vault, config)

        area = workflow._infer_area_from_project("不存在的项目")
        assert area is None

    def test_find_project(self, setup_vault):
        """测试查找项目。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = BrainstormWorkflow(vault, config)

        project_path = workflow._find_project("学习Python", "编程")
        assert project_path is not None
        assert "学习Python" in project_path

    def test_find_project_not_found(self, setup_vault):
        """测试项目不存在。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = BrainstormWorkflow(vault, config)

        project_path = workflow._find_project("不存在的项目", "编程")
        assert project_path is None

    def test_create_brainstorm_note(self, setup_vault):
        """测试创建头脑风暴笔记。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = BrainstormWorkflow(vault, config)

        note_path = workflow._create_brainstorm_note(
            topic="测试主题",
            area="编程",
            project=None,
            project_path=None,
            initial_idea="初始想法内容"
        )

        assert note_path is not None
        assert "测试主题" in note_path

        # 验证文件内容
        full_path = setup_vault / note_path
        content = full_path.read_text(encoding="utf-8")
        assert "头脑风暴" in content
        assert "初始想法内容" in content

    def test_create_brainstorm_note_with_project(self, setup_vault):
        """测试创建关联项目的头脑风暴笔记。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = BrainstormWorkflow(vault, config)

        project_path = workflow._find_project("学习Python", "编程")
        note_path = workflow._create_brainstorm_note(
            topic="项目相关头脑风暴",
            area="编程",
            project="学习Python",
            project_path=project_path,
            initial_idea="项目想法"
        )

        assert note_path is not None

        # 验证文件包含项目链接
        full_path = setup_vault / note_path
        content = full_path.read_text(encoding="utf-8")
        assert "学习Python" in content

    def test_append_to_note(self, setup_vault):
        """测试追加内容到笔记。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = BrainstormWorkflow(vault, config)

        # 先创建笔记
        note_path = workflow._create_brainstorm_note(
            topic="追加测试",
            area="编程",
            project=None,
            project_path=None,
            initial_idea="初始内容"
        )

        # 追加内容
        success = workflow.append_to_note(note_path, "追加的新内容")
        assert success is True

        # 验证追加成功
        full_path = setup_vault / note_path
        content = full_path.read_text(encoding="utf-8")
        assert "追加的新内容" in content

    def test_append_to_note_not_found(self, setup_vault):
        """测试追加到不存在的笔记。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = BrainstormWorkflow(vault, config)

        success = workflow.append_to_note("不存在的路径.md", "内容")
        assert success is False

    def test_extract_insights(self, setup_vault):
        """测试提取精华。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = BrainstormWorkflow(vault, config)

        # 直接创建包含精华内容的笔记（模拟完成的头脑风暴）
        research_path = setup_vault / "30_研究" / "编程"
        research_path.mkdir(parents=True, exist_ok=True)

        note_content = """---
id: kb-20260331-100000-0001
title: 提取测试 头脑风暴
type: brainstorm
date: 2026-03-31
area: 编程
---

# 提取测试 头脑风暴

## 精华提取

### 核心结论
- 结论1：这是核心结论
- 结论2：另一个核心结论

### 可行方案
1. 方案 A：第一个方案
2. 方案 B：第二个方案

### 下一步行动
- [ ] 行动项1
- [ ] 行动项2
"""
        note_file = research_path / "提取测试_头脑风暴_2026-03-31.md"
        note_file.write_text(note_content, encoding="utf-8")
        note_path = "30_研究/编程/提取测试_头脑风暴_2026-03-31.md"

        # 提取精华
        insights = workflow.extract_insights(note_path)

        assert len(insights.core_conclusions) >= 2
        assert len(insights.viable_solutions) >= 2
        assert len(insights.next_actions) >= 2

    def test_extract_insights_from_template(self, setup_vault):
        """测试从模板笔记提取空精华（只有占位符）。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = BrainstormWorkflow(vault, config)

        # 创建模板笔记（没有填充精华内容）
        note_path = workflow._create_brainstorm_note(
            topic="空精华测试",
            area="编程",
            project=None,
            project_path=None,
            initial_idea="只是想法"
        )

        insights = workflow.extract_insights(note_path)

        # 模板有占位符内容，所以会提取到占位符
        # 这测试的是模板结构存在的情况
        assert isinstance(insights.core_conclusions, list)
        assert isinstance(insights.viable_solutions, list)
        assert isinstance(insights.next_actions, list)

    def test_extract_insights_file_not_found(self, setup_vault):
        """测试文件不存在时提取精华。"""
        config = Config(vault_path=setup_vault, default_area="编程")
        vault = Vault(setup_vault)
        workflow = BrainstormWorkflow(vault, config)

        insights = workflow.extract_insights("不存在.md")
        assert insights.core_conclusions == []


class TestBrainstormInsights:
    """BrainstormInsights 数据类测试。"""

    def test_insights_creation(self):
        """测试创建精华。"""
        insights = BrainstormInsights(
            core_conclusions=["结论1", "结论2"],
            viable_solutions=["方案A", "方案B"],
            next_actions=["行动1", "行动2"]
        )

        assert len(insights.core_conclusions) == 2
        assert len(insights.viable_solutions) == 2
        assert len(insights.next_actions) == 2

    def test_insights_defaults(self):
        """测试默认值。"""
        insights = BrainstormInsights()

        assert insights.core_conclusions == []
        assert insights.viable_solutions == []
        assert insights.next_actions == []