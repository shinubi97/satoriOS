"""Obsidian Knowledge Base Management Skill.

提供 PARA 方法论的完整知识管理工作流实现。
"""

__version__ = "1.0.0"
__author__ = "Your Name"

# 只导入已实现的模块
from obsidian_kb.config import Config, get_config, DEFAULT_CONFIG_PATH
from obsidian_kb.parser import MarkdownParser, Heading, Link, CodeBlock, Checkbox
from obsidian_kb.link_resolver import LinkResolver, LinkInfo
from obsidian_kb.vault import Vault, NoteInfo, NoteContent

# 以下模块将在后续任务中实现
# from obsidian_kb.utils.id_generator import generate_note_id
# from obsidian_kb.utils.frontmatter import parse_frontmatter, extract_frontmatter