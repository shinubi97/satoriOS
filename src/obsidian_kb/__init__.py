"""Obsidian Knowledge Base Management Skill.

提供 PARA 方法论的完整知识管理工作流实现。
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from obsidian_kb.config import Config, get_config
from obsidian_kb.utils.id_generator import generate_note_id
from obsidian_kb.utils.frontmatter import parse_frontmatter, extract_frontmatter