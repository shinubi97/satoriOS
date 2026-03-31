"""Vault 操作模块测试."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from obsidian_kb.vault import Vault, NoteInfo, NoteContent


class TestVault:
    """Vault 操作测试."""

    def test_vault_init(self, temp_vault):
        """测试 Vault 初始化."""
        vault = Vault(temp_vault)
        assert vault.path == temp_vault
        assert vault.inbox_path == temp_vault / "00_收件箱"
        assert vault.projects_path == temp_vault / "10_项目"

    def test_vault_list_inbox(self, temp_vault):
        """测试列出收件箱文件."""
        # 创建测试文件
        (temp_vault / "00_收件箱" / "idea1.md").write_text("# Idea 1")
        (temp_vault / "00_收件箱" / "idea2.md").write_text("# Idea 2")

        vault = Vault(temp_vault)
        notes = vault.list_inbox()

        assert len(notes) == 2
        assert any("idea1" in n.path for n in notes)

    def test_vault_read_note(self, temp_vault):
        """测试读取笔记内容."""
        note_path = temp_vault / "00_收件箱" / "test.md"
        note_path.write_text("""---
id: kb-20250330-143052-a3f9
title: Test Note
type: knowledge
date: 2025-03-30
---

# Test Note
Content here.
""")

        vault = Vault(temp_vault)
        content = vault.read_note("00_收件箱/test.md")

        assert "Test Note" in content
        assert "Content here" in content

    def test_vault_create_note(self, temp_vault):
        """测试创建笔记."""
        vault = Vault(temp_vault)

        content = """---
id: kb-20250331-100000-abc1
title: New Note
type: project
date: 2025-03-31
---

# New Note
"""

        # 确保目标目录存在
        (temp_vault / "10_项目" / "编程").mkdir(parents=True, exist_ok=True)

        result = vault.create_note("10_项目/编程/NewProject.md", content)

        assert result.exists()
        assert "New Note" in result.read_text()

    def test_vault_search(self, temp_vault):
        """测试搜索笔记."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='[{"path": "test.md", "title": "Test"}]'
            )

            vault = Vault(temp_vault)
            results = vault.search("Python")

            assert len(results) == 1
            assert results[0]["title"] == "Test"

    def test_vault_get_backlinks(self, temp_vault):
        """测试获取反向链接."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='[{"source": "note1.md", "link": "[[test]]"}]'
            )

            vault = Vault(temp_vault)
            backlinks = vault.get_backlinks("test.md")

            assert len(backlinks) == 1
            assert backlinks[0]["source"] == "note1.md"

    def test_vault_move_note(self, temp_vault):
        """测试移动笔记."""
        # 创建源文件
        src = temp_vault / "00_收件箱" / "move_me.md"
        src.write_text("# Move Me")

        # 确保目标目录存在
        (temp_vault / "50_归档" / "2025-03").mkdir(parents=True, exist_ok=True)

        vault = Vault(temp_vault)
        result = vault.move_note(
            "00_收件箱/move_me.md",
            "50_归档/2025-03/move_me.md"
        )

        assert result.exists()
        assert not src.exists()

    def test_vault_ensure_directory(self, temp_vault):
        """测试确保目录存在."""
        vault = Vault(temp_vault)

        # 目录不存在时应创建
        vault.ensure_directory("10_项目/新领域")

        assert (temp_vault / "10_项目" / "新领域").exists()


class TestNoteInfo:
    """NoteInfo 数据类测试."""

    def test_note_info_creation(self):
        """测试 NoteInfo 创建."""
        info = NoteInfo(
            path="test/note.md",
            title="Test Note",
            modified_time="2025-03-30"
        )

        assert info.path == "test/note.md"
        assert info.title == "Test Note"
        assert info.modified_time == "2025-03-30"


class TestNoteContent:
    """NoteContent 数据类测试."""

    def test_note_content_creation(self):
        """测试 NoteContent 创建."""
        content = NoteContent(
            path="test/note.md",
            frontmatter={"id": "kb-001", "title": "Test"},
            body="# Test\nContent"
        )

        assert content.path == "test/note.md"
        assert content.frontmatter["id"] == "kb-001"
        assert "Test" in content.body