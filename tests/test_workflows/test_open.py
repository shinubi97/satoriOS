"""Test open workflow."""
import pytest
from pathlib import Path

from obsidian_kb.workflows.open import OpenWorkflow, NoteDetail
from obsidian_kb.vault import Vault


class MockVault:
    """Mock vault for testing."""
    def __init__(self, path):
        self.path = Path(path)


class TestOpenWorkflow:
    """Test open workflow."""

    def test_open_by_fuzzy_match(self, temp_vault):
        """Test opening note by fuzzy name match."""
        # Create test note
        note_path = temp_vault / "40_知识库" / "OpenClaw教程.md"
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text("""---
title: OpenClaw 教程
type: knowledge
area: 编程
---

# OpenClaw 教程

这是一个关于 OpenClaw 的教程。

## 核心概念

OpenClaw 是一个编排工具。
""")

        vault = MockVault(temp_vault)
        workflow = OpenWorkflow(vault, None)
        result = workflow.execute(note_name="openclaw")

        assert result.success
        assert "OpenClaw" in result.data["note"].title

    def test_open_not_found(self, temp_vault):
        """Test opening non-existent note."""
        vault = MockVault(temp_vault)
        workflow = OpenWorkflow(vault, None)
        result = workflow.execute(note_name="不存在的笔记")

        assert not result.success
        # Error message can be "不存在" or "无法读取" depending on CLI availability
        assert "不存在" in result.message or "无法读取" in result.message

    def test_open_by_path(self, temp_vault):
        """Test opening note by exact path."""
        # Create test note with complete frontmatter
        note_path = temp_vault / "10_项目" / "工作" / "测试项目.md"
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text("""---
id: kb-20260331-100000-0001
title: 测试项目
type: project
status: 进行中
date: 2026-03-31
---

# 测试项目

项目内容。

## 目标

- [ ] 完成开发
- [ ] 测试验证
""")

        vault = MockVault(temp_vault)
        workflow = OpenWorkflow(vault, None)
        result = workflow.execute(note_name="10_项目/工作/测试项目.md")

        assert result.success
        assert result.data["note"].title == "测试项目"
        assert result.data["note"].note_type == "project"

    def test_open_extracts_headings(self, temp_vault):
        """Test that headings are extracted."""
        note_path = temp_vault / "测试笔记.md"
        note_path.write_text("""---
title: 测试笔记
---

# 主标题

## 二级标题

### 三级标题
""")

        vault = MockVault(temp_vault)
        workflow = OpenWorkflow(vault, None)
        result = workflow.execute(note_name="测试笔记")

        assert result.success
        assert len(result.data["note"].headings) > 0
        assert "主标题" in result.data["note"].headings

    def test_open_extracts_links(self, temp_vault):
        """Test that outgoing links are extracted."""
        note_path = temp_vault / "测试笔记.md"
        note_path.write_text("""---
title: 测试笔记
---

# 内容

引用 [[其他笔记]] 和 [[另一个笔记|别名]]。
""")

        vault = MockVault(temp_vault)
        workflow = OpenWorkflow(vault, None)
        result = workflow.execute(note_name="测试笔记")

        assert result.success
        assert len(result.data["note"].outgoing_links) >= 2

    def test_note_detail_dataclass(self):
        """Test NoteDetail dataclass."""
        detail = NoteDetail(
            path="test/note.md",
            title="Test Note",
            note_type="knowledge",
            area="编程",
            status="",
            content_preview="Preview content",
            headings=["Heading 1"],
            outgoing_links=["link1"],
            backlinks=["link2"]
        )

        assert detail.path == "test/note.md"
        assert detail.title == "Test Note"
        assert len(detail.headings) == 1