"""Markdown AST 解析器测试."""
import pytest
from obsidian_kb.parser import MarkdownParser, Heading, Link, CodeBlock


class TestMarkdownParser:
    """Markdown 解析器测试."""

    def test_parse_headings(self):
        """测试解析标题."""
        content = """# H1 Title
## H2 Section
### H3 Subsection
"""
        parser = MarkdownParser()
        headings = parser.extract_headings(content)

        assert len(headings) == 3
        assert headings[0].level == 1
        assert headings[0].text == "H1 Title"
        assert headings[1].level == 2

    def test_parse_wiki_links(self):
        """测试解析 [[wiki links]]。"""
        content = """See [[Note A]] and [[Note B|alias]] for details.
Also check [[folder/nested note]].
"""
        parser = MarkdownParser()
        links = parser.extract_wiki_links(content)

        assert len(links) == 3
        assert links[0].target == "Note A"
        assert links[0].alias is None
        assert links[1].target == "Note B"
        assert links[1].alias == "alias"
        assert links[2].target == "folder/nested note"

    def test_parse_code_blocks(self):
        """测试解析代码块。"""
        content = """Some text.

```python
def hello():
    print("Hello")
```

More text.
"""
        parser = MarkdownParser()
        code_blocks = parser.extract_code_blocks(content)

        assert len(code_blocks) == 1
        assert code_blocks[0].language == "python"
        assert "def hello" in code_blocks[0].code

    def test_extract_text_content(self):
        """测试提取纯文本（排除代码块）。"""
        content = """# Title

Some text here.

```python
code = "should not appear"
```

More text.
"""
        parser = MarkdownParser()
        text = parser.extract_text_content(content)

        assert "Some text here" in text
        assert "More text" in text
        assert "should not appear" not in text

    def test_parse_checkboxes(self):
        """测试解析待办项。"""
        content = """- [ ] Todo 1
- [x] Done
- [ ] Todo 2
"""
        parser = MarkdownParser()
        todos = parser.extract_checkboxes(content)

        assert len(todos) == 3
        assert todos[0].checked is False
        assert todos[0].text == "Todo 1"
        assert todos[1].checked is True

    def test_find_section(self):
        """测试查找特定章节。"""
        content = """# Main

## Section A
Content A

## Section B
Content B

## Section C
Content C
"""
        parser = MarkdownParser()
        section = parser.find_section(content, "Section B")

        assert section is not None
        assert "Content B" in section

    def test_parse_tags(self):
        """测试解析标签。"""
        content = """# Note with #tag1 and #tag2

Some text with #another_tag here.
"""
        parser = MarkdownParser()
        tags = parser.extract_tags(content)

        assert "tag1" in tags
        assert "tag2" in tags
        assert "another_tag" in tags