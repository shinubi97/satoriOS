"""回顾工作流.

回顾项目或研究笔记，提取关键信息。
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any

from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult
from obsidian_kb.utils.frontmatter import parse_frontmatter, update_frontmatter
from obsidian_kb.parser import MarkdownParser


@dataclass
class ReviewDetails:
    """回顾详情。"""
    note_path: str
    note_type: str
    review_date: str
    key_findings: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    related_notes: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class ReviewWorkflow(BaseWorkflow):
    """回顾工作流。

    回顾笔记内容，提取关键信息和行动项。

    工作流程：
    1. 读取笔记内容
    2. 解析结构和内容
    3. 提取关键信息
    4. 生成回顾报告
    5. 返回结果
    """

    def execute(
        self,
        note_path: str,
        focus: str = None
    ) -> WorkflowResult:
        """回顾笔记。

        Args:
            note_path: 笔记路径
            focus: 关注重点（可选）

        Returns:
            WorkflowResult 包含回顾结果
        """
        source_file = self.vault.path / note_path

        if not source_file.exists():
            return WorkflowResult(
                success=False,
                message=f"笔记不存在: {note_path}",
                suggestions=["检查路径是否正确"]
            )

        # 1. 读取笔记
        try:
            content = source_file.read_text(encoding="utf-8")
        except Exception as e:
            return WorkflowResult(
                success=False,
                message=f"读取笔记失败: {e}",
                suggestions=["检查文件权限"]
            )

        # 2. 解析 frontmatter
        fm_obj = parse_frontmatter(content)
        note_type = fm_obj.type if fm_obj else "unknown"
        title = fm_obj.title if fm_obj else source_file.stem

        # 3. 解析内容
        parser = MarkdownParser()

        # 提取关键信息
        key_findings = self._extract_key_findings(content, parser)
        action_items = self._extract_action_items(content, parser)
        related_notes = self._extract_related_notes(content, parser)

        # 4. 生成建议
        suggestions = self._generate_suggestions(
            note_type, key_findings, action_items, related_notes
        )

        # 5. 构建回顾详情
        review = ReviewDetails(
            note_path=note_path,
            note_type=note_type,
            review_date=date.today().isoformat(),
            key_findings=key_findings,
            action_items=action_items,
            related_notes=related_notes,
            suggestions=suggestions
        )

        return WorkflowResult(
            success=True,
            message=f"✅ 回顾完成: {title}",
            suggestions=suggestions,
            data={
                "review": review
            }
        )

    def _extract_key_findings(
        self,
        content: str,
        parser: MarkdownParser
    ) -> List[str]:
        """提取关键发现。

        Args:
            content: 笔记内容
            parser: 解析器

        Returns:
            关键发现列表
        """
        findings = []

        # 查找"核心结论"、"关键发现"、"总结"等章节
        sections = ["核心结论", "关键发现", "总结", "核心收获", "精华"]

        for section in sections:
            section_content = parser.find_section(content, section)
            if section_content:
                # 提取列表项
                for line in section_content.split("\n"):
                    line = line.strip()
                    if line.startswith("- ") and len(line) > 2:
                        findings.append(line[2:])
                    elif line.startswith("* ") and len(line) > 2:
                        findings.append(line[2:])

        return findings[:5]  # 最多返回 5 个

    def _extract_action_items(
        self,
        content: str,
        parser: MarkdownParser
    ) -> List[str]:
        """提取行动项。

        Args:
            content: 笔记内容
            parser: 解析器

        Returns:
            行动项列表
        """
        action_items = []

        # 查找"下一步行动"、"待办"等章节
        sections = ["下一步行动", "待办", "行动项"]

        for section in sections:
            section_content = parser.find_section(content, section)
            if section_content:
                checkboxes = parser.extract_checkboxes(section_content)
                for cb in checkboxes:
                    if not cb.checked:
                        action_items.append(cb.text)

        return action_items[:5]  # 最多返回 5 个

    def _extract_related_notes(
        self,
        content: str,
        parser: MarkdownParser
    ) -> List[str]:
        """提取相关笔记链接。

        Args:
            content: 笔记内容
            parser: 解析器

        Returns:
            相关笔记列表
        """
        links = parser.extract_wiki_links(content)
        return [link.target for link in links[:10]]  # 最多返回 10 个

    def _generate_suggestions(
        self,
        note_type: str,
        key_findings: List[str],
        action_items: List[str],
        related_notes: List[str]
    ) -> List[str]:
        """生成建议。

        Args:
            note_type: 笔记类型
            key_findings: 关键发现
            action_items: 行动项
            related_notes: 相关笔记

        Returns:
            建议列表
        """
        suggestions = []

        if note_type == "project":
            if not action_items:
                suggestions.append("项目没有明确的下一步行动，建议添加")
            else:
                suggestions.append(f"项目有 {len(action_items)} 个待办事项")

            if not related_notes:
                suggestions.append("项目没有关联笔记，考虑添加相关资源")

        elif note_type == "research":
            if not key_findings:
                suggestions.append("研究笔记没有核心结论，建议总结")

            suggestions.append("考虑将研究成果应用到项目中")

        elif note_type == "brainstorm":
            if key_findings:
                suggestions.append("头脑风暴有结论，考虑创建行动计划")

            if action_items:
                suggestions.append("将行动项添加到相关项目")

        return suggestions

    def review_project(self, project_path: str) -> WorkflowResult:
        """专门回顾项目笔记。

        Args:
            project_path: 项目笔记路径

        Returns:
            回顾结果
        """
        return self.execute(project_path, focus="project")

    def review_research(self, research_path: str) -> WorkflowResult:
        """专门回顾研究笔记。

        Args:
            research_path: 研究笔记路径

        Returns:
            回顾结果
        """
        return self.execute(research_path, focus="research")