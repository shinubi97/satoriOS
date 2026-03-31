"""链接解析器测试."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from obsidian_kb.link_resolver import LinkResolver, LinkInfo


class TestLinkResolver:
    """链接解析器测试."""

    def test_resolve_wiki_link(self, temp_vault):
        """测试解析 wiki link 到文件路径。"""
        # 创建测试文件
        (temp_vault / "40_知识库" / "Test Note.md").write_text("# Test Note")

        resolver = LinkResolver(temp_vault)
        result = resolver.resolve("Test Note")

        assert result is not None
        assert result.exists()
        assert "Test Note" in result.name

    def test_resolve_with_alias(self, temp_vault):
        """测试带别名的链接解析。"""
        (temp_vault / "40_知识库" / "Python.md").write_text("# Python")

        resolver = LinkResolver(temp_vault)
        result = resolver.resolve("Python|Py")

        assert result is not None
        assert "Python" in result.name

    def test_resolve_nested_path(self, temp_vault):
        """测试嵌套路径解析。"""
        (temp_vault / "10_项目" / "编程").mkdir(parents=True, exist_ok=True)
        (temp_vault / "10_项目" / "编程" / "My Project.md").write_text("# My Project")

        resolver = LinkResolver(temp_vault)
        result = resolver.resolve("My Project")

        assert result is not None

    def test_resolve_not_found(self, temp_vault):
        """测试链接目标不存在。"""
        resolver = LinkResolver(temp_vault)
        result = resolver.resolve("Nonexistent Note")

        assert result is None

    def test_get_backlinks(self, temp_vault):
        """测试获取反向链接。"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='[{"file": "note1.md"}, {"file": "note2.md"}]'
            )

            resolver = LinkResolver(temp_vault)
            backlinks = resolver.get_backlinks("target.md")

            assert len(backlinks) == 2

    def test_get_outgoing_links(self, temp_vault):
        """测试获取出链。"""
        content = """# Note
See [[Link A]] and [[Link B]].
"""
        resolver = LinkResolver(temp_vault)
        links = resolver.extract_links(content)

        assert len(links) == 2
        assert links[0] == "Link A"
        assert links[1] == "Link B"

    def test_update_link_in_content(self, temp_vault):
        """测试更新内容中的链接。"""
        content = "See [[Old Name]] for details."
        resolver = LinkResolver(temp_vault)

        updated = resolver.update_link(content, "Old Name", "New Name")

        assert "[[New Name]]" in updated
        assert "[[Old Name]]" not in updated

    def test_find_broken_links(self, temp_vault):
        """测试查找死链。"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='[{"link": "[[Missing]]", "file": "note.md"}]'
            )

            resolver = LinkResolver(temp_vault)
            broken = resolver.find_broken_links()

            assert len(broken) == 1
            assert broken[0]["link"] == "[[Missing]]"

    def test_find_orphans(self, temp_vault):
        """测试查找孤儿笔记。"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='[{"file": "orphan.md"}]'
            )

            resolver = LinkResolver(temp_vault)
            orphans = resolver.find_orphans()

            assert len(orphans) == 1


class TestLinkInfo:
    """LinkInfo 数据类测试."""

    def test_link_info_creation(self):
        """测试 LinkInfo 创建。"""
        info = LinkInfo(
            source="source.md",
            target="target.md",
            link_text="Target Note",
            is_embed=False
        )

        assert info.source == "source.md"
        assert info.target == "target.md"
        assert info.link_text == "Target Note"
        assert info.is_embed == False

    def test_link_info_embed(self):
        """测试嵌入链接。"""
        info = LinkInfo(
            source="source.md",
            target="image.png",
            link_text="![[image.png]]",
            is_embed=True
        )

        assert info.is_embed == True
        assert info.link_text == "![[image.png]]"

    def test_link_info_str(self):
        """测试 LinkInfo 字符串表示。"""
        info = LinkInfo(
            source="source.md",
            target="target.md",
            link_text="Target"
        )

        assert str(info) == "[[Target]] -> target.md (from source.md)"