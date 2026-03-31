"""Markdown AST 解析器模块.

使用 markdown-it-py 进行 Markdown AST 解析，支持提取：
- 标题 (headings)
- Wiki 链接 ([[...]] 和 ![[...]])
- 代码块
- 待办项 (checkboxes)
- 标签 (#tag)
"""
from dataclasses import dataclass
from typing import List, Optional
import re

from markdown_it import MarkdownIt
from markdown_it.token import Token


@dataclass
class Heading:
    """标题数据类."""
    level: int
    text: str
    line_number: int


@dataclass
class Link:
    """链接数据类."""
    target: str
    alias: Optional[str]
    is_embed: bool  # True for ![[...]], False for [[...]]


@dataclass
class CodeBlock:
    """代码块数据类."""
    language: str
    code: str


@dataclass
class Checkbox:
    """待办项数据类."""
    checked: bool
    text: str


class MarkdownParser:
    """Markdown 解析器类.

    使用 markdown-it-py 解析 Markdown 内容，提供各种提取方法。
    """

    # Wiki 链接正则: [[target]] 或 [[target|alias]]
    WIKI_LINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
    # 嵌入链接正则: ![[target]] 或 ![[target|alias]]
    EMBED_LINK_PATTERN = re.compile(r'!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
    # 标签正则: #tag (不以 # 开头的标题)
    TAG_PATTERN = re.compile(r'(?<!^)#(\w[\w/-]+)', re.MULTILINE)
    # 待办项正则: - [ ] 或 - [x]
    CHECKBOX_PATTERN = re.compile(r'^[ \t]*[-*+][ \t]+\[([ xX])\][ \t]+(.+)$', re.MULTILINE)

    def __init__(self):
        """初始化解析器."""
        self._md = MarkdownIt("commonmark", {"html": False})

    def parse(self, content: str) -> List[Token]:
        """解析 Markdown 内容为 token 列表."""
        return self._md.parse(content)

    def extract_headings(self, content: str) -> List[Heading]:
        """提取所有标题.

        Args:
            content: Markdown 内容

        Returns:
            标题列表，按出现顺序排列
        """
        tokens = self.parse(content)
        headings = []

        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.type == "heading_open":
                # 从 tag 中获取级别 (h1 -> 1, h2 -> 2, ...)
                level = int(token.tag[1])

                # 下一个 token 是 heading_inline，包含文本
                if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                    text = tokens[i + 1].content
                else:
                    text = ""

                line_number = token.map[0] if token.map else i

                headings.append(Heading(
                    level=level,
                    text=text,
                    line_number=line_number
                ))
            i += 1

        return headings

    def extract_wiki_links(self, content: str) -> List[Link]:
        """提取所有 Wiki 链接.

        支持 [[target]] 和 [[target|alias]] 格式。
        也支持嵌入格式 ![[...]]。

        Args:
            content: Markdown 内容

        Returns:
            链接列表，按出现顺序排列
        """
        links = []

        # 先处理嵌入链接 ![[...]]
        for match in self.EMBED_LINK_PATTERN.finditer(content):
            target = match.group(1).strip()
            alias = match.group(2).strip() if match.group(2) else None
            links.append(Link(
                target=target,
                alias=alias,
                is_embed=True
            ))

        # 再处理普通 wiki 链接 [[...]]
        for match in self.WIKI_LINK_PATTERN.finditer(content):
            target = match.group(1).strip()
            alias = match.group(2).strip() if match.group(2) else None

            # 检查是否已经被作为嵌入链接处理
            # 通过检查位置是否在 ![[...]] 的范围内
            start = match.start()
            is_embed = False
            for embed_match in self.EMBED_LINK_PATTERN.finditer(content):
                if embed_match.start() == start - 1:  # ! 在 [[...]] 前面
                    is_embed = True
                    break

            if not is_embed:
                links.append(Link(
                    target=target,
                    alias=alias,
                    is_embed=False
                ))

        return links

    def extract_code_blocks(self, content: str) -> List[CodeBlock]:
        """提取所有代码块.

        Args:
            content: Markdown 内容

        Returns:
            代码块列表，按出现顺序排列
        """
        tokens = self.parse(content)
        code_blocks = []

        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.type == "fence":
                language = token.info.strip() if token.info else ""
                code = token.content
                code_blocks.append(CodeBlock(
                    language=language,
                    code=code
                ))
            i += 1

        return code_blocks

    def extract_text_content(self, content: str) -> str:
        """提取纯文本内容（排除代码块）.

        Args:
            content: Markdown 内容

        Returns:
            去除代码块后的文本
        """
        tokens = self.parse(content)
        text_parts = []

        for token in tokens:
            if token.type == "inline":
                text_parts.append(token.content)

        return " ".join(text_parts)

    def extract_checkboxes(self, content: str) -> List[Checkbox]:
        """提取所有待办项.

        支持格式：- [ ] todo 和 - [x] done

        Args:
            content: Markdown 内容

        Returns:
            待办项列表，按出现顺序排列
        """
        checkboxes = []

        for match in self.CHECKBOX_PATTERN.finditer(content):
            checked = match.group(1).lower() == 'x'
            text = match.group(2).strip()
            checkboxes.append(Checkbox(
                checked=checked,
                text=text
            ))

        return checkboxes

    def find_section(self, content: str, heading: str) -> Optional[str]:
        """查找特定章节的内容.

        Args:
            content: Markdown 内容
            heading: 要查找的标题文本

        Returns:
            章节内容（不包括标题本身），如果未找到则返回 None
        """
        tokens = self.parse(content)

        # 找到目标标题的级别和位置
        target_level = None
        target_index = None

        for i, token in enumerate(tokens):
            if token.type == "heading_open":
                level = int(token.tag[1])
                if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                    text = tokens[i + 1].content
                    if text == heading:
                        target_level = level
                        target_index = i
                        break

        if target_index is None:
            return None

        # 收集该标题下的内容，直到遇到同级或更高级的标题
        section_tokens = []
        i = target_index + 2  # 跳过 heading_open 和 inline
        while i < len(tokens):
            token = tokens[i]
            if token.type == "heading_open":
                level = int(token.tag[1])
                if level <= target_level:
                    break
            section_tokens.append(token)
            i += 1

        # 从 tokens 中提取文本
        text_parts = []
        for token in section_tokens:
            if token.type == "inline":
                text_parts.append(token.content)

        return " ".join(text_parts) if text_parts else ""

    def extract_tags(self, content: str) -> List[str]:
        """提取所有标签.

        支持格式：#tag

        注意：不会匹配 Markdown 标题标记（以 # 开头后跟空格的行首）

        Args:
            content: Markdown 内容

        Returns:
            标签列表（去重后）
        """
        tags = set()

        # 按行处理
        lines = content.split('\n')
        for line in lines:
            # 去除标题标记（行首的 # 后跟空格）
            stripped = line.strip()
            processed_line = stripped

            # 去除标题标记：# ## ### 等（后面必须跟空格）
            heading_match = re.match(r'^#{1,6}\s+', stripped)
            if heading_match:
                # 去除标题标记部分，保留后面的文本
                processed_line = stripped[heading_match.end():]

            # 在处理后的行中查找标签
            # 标签格式：#word（后面不跟空格）
            for match in re.finditer(r'#(\w[\w/-]+)', processed_line):
                tag = match.group(1)
                tags.add(tag)

        return list(tags)