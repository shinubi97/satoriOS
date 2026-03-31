"""Frontmatter 解析器模块测试."""
import pytest
from datetime import datetime
from obsidian_kb.utils.frontmatter import (
    parse_frontmatter,
    extract_frontmatter,
    update_frontmatter,
    create_frontmatter,
    Frontmatter
)


class TestFrontmatter:
    """Frontmatter 解析器测试."""

    def test_parse_frontmatter_valid(self, sample_note_content):
        """测试解析有效的 frontmatter."""
        fm = parse_frontmatter(sample_note_content)

        assert fm is not None
        assert fm.id == "kb-20250330-143052-a3f9"
        assert fm.title == "Python 装饰器详解"
        assert fm.type == "knowledge"
        assert fm.date == "2025-03-30"
        assert "Python" in fm.tags
        assert fm.status == "进行中"

    def test_parse_frontmatter_missing(self):
        """测试缺少 frontmatter 的内容."""
        content = "# 没有 frontmatter 的笔记\n\n正文内容..."

        fm = parse_frontmatter(content)
        assert fm is None

    def test_parse_frontmatter_invalid_yaml(self):
        """测试无效的 YAML frontmatter."""
        content = """---
invalid: yaml: syntax
---

# 笔记内容
"""

        with pytest.raises(ValueError, match="Invalid YAML"):
            parse_frontmatter(content)

    def test_extract_frontmatter_with_content(self, sample_note_content):
        """测试提取 frontmatter 和正文."""
        fm, body = extract_frontmatter(sample_note_content)

        assert fm is not None
        assert fm.title == "Python 装饰器详解"
        assert "# Python 装饰器详解" in body
        assert "什么是装饰器" in body

    def test_extract_frontmatter_without(self):
        """测试没有 frontmatter 时的提取."""
        content = "# 纯正文笔记"

        fm, body = extract_frontmatter(content)

        assert fm is None
        assert body == content

    def test_create_frontmatter_project(self):
        """测试创建项目类型 frontmatter."""
        fm = create_frontmatter(
            note_type="project",
            title="新项目",
            area="编程",
            date="2025-03-30"
        )

        assert fm.type == "project"
        assert fm.title == "新项目"
        assert fm.tags == ["项目", "编程"]
        assert fm.status == "进行中"
        assert fm.id.startswith("kb-")

    def test_create_frontmatter_research(self):
        """测试创建研究类型 frontmatter."""
        fm = create_frontmatter(
            note_type="research",
            title="研究主题",
            area="编程",
            date="2025-03-30"
        )

        assert fm.type == "research"
        assert fm.status == "进行中"
        assert "研究" in fm.tags

    def test_update_frontmatter_field(self, sample_note_content):
        """测试更新 frontmatter 字段."""
        # 更新状态
        updated_content = update_frontmatter(
            sample_note_content,
            {"status": "已完成", "updated": "2025-03-31 10:00"}
        )

        new_fm = parse_frontmatter(updated_content)
        assert new_fm.status == "已完成"
        assert new_fm.updated == "2025-03-31 10:00"
        assert "# Python 装饰器详解" in updated_content  # 正文保留

    def test_update_frontmatter_add_new_field(self, sample_note_content):
        """测试添加新字段到 frontmatter."""
        updated_content = update_frontmatter(
            sample_note_content,
            {"new_field": "new value"}
        )

        fm = parse_frontmatter(updated_content)
        assert fm.new_field == "new value"

    def test_frontmatter_class_methods(self):
        """测试 Frontmatter 类方法."""
        fm = Frontmatter(
            id="kb-20250330-143052-a3f9",
            title="测试",
            type="knowledge",
            date="2025-03-30",
            created="2025-03-30 14:30",
            updated="2025-03-30 14:30",
            tags=["测试"],
            status="进行中"
        )

        # 转换为 YAML
        yaml_str = fm.to_yaml()
        assert "id: kb-20250330-143052-a3f9" in yaml_str
        assert "title: 测试" in yaml_str

        # 转换为字符串（完整 frontmatter）
        full_fm = str(fm)
        assert full_fm.startswith("---\n")
        assert full_fm.endswith("---\n")

    def test_frontmatter_to_dict(self):
        """测试 Frontmatter 转换为字典."""
        fm = Frontmatter(
            id="kb-20250330-143052-a3f9",
            title="测试",
            type="knowledge",
            date="2025-03-30",
            tags=["测试"]
        )

        data = fm.to_dict()
        assert isinstance(data, dict)
        assert data["id"] == "kb-20250330-143052-a3f9"
        assert data["title"] == "测试"