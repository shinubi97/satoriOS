"""MOC (Map of Content) 管理工作流.

创建和维护知识地图。
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any

from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult
from obsidian_kb.utils.frontmatter import parse_frontmatter, create_frontmatter
from obsidian_kb.link_resolver import LinkResolver
from obsidian_kb.parser import MarkdownParser


@dataclass
class MOCEntry:
    """MOC 条目。"""
    path: str
    title: str
    note_type: str
    relevance: float = 1.0


@dataclass
class MOCContent:
    """MOC 内容。"""
    area: str
    description: str = ""
    core_notes: List[MOCEntry] = field(default_factory=list)
    projects: List[MOCEntry] = field(default_factory=list)
    researches: List[MOCEntry] = field(default_factory=list)
    brainstorms: List[MOCEntry] = field(default_factory=list)
    knowledge: List[MOCEntry] = field(default_factory=list)


class MocsWorkflow(BaseWorkflow):
    """MOC 管理工作流。

    列出、查看和更新 MOC。

    工作流程：
    1. 扫描领域
    2. 收集相关笔记
    3. 生成或更新 MOC
    """

    def execute(self, **kwargs) -> WorkflowResult:
        """列出所有 MOC。

        Returns:
            WorkflowResult 包含 MOC 列表
        """
        mocs_path = self.vault.path / "40_知识库" / "moc"

        if not mocs_path.exists():
            return WorkflowResult(
                success=True,
                message="暂无 MOC",
                suggestions=["创建第一个 MOC: /moc-create 领域名"]
            )

        mocs = []
        for md_file in mocs_path.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                fm_obj = parse_frontmatter(content)
                title = fm_obj.title if fm_obj else md_file.stem

                mocs.append({
                    "path": str(md_file.relative_to(self.vault.path)),
                    "title": title,
                    "area": fm_obj.area if fm_obj else ""
                })
            except Exception:
                continue

        return WorkflowResult(
            success=True,
            message=f"找到 {len(mocs)} 个 MOC",
            suggestions=[f"查看 [[{m['title']}]]" for m in mocs[:5]],
            data={"mocs": mocs}
        )

    def get_moc(self, area: str) -> WorkflowResult:
        """获取特定领域的 MOC。

        Args:
            area: 领域名称

        Returns:
            WorkflowResult 包含 MOC 内容
        """
        moc_path = self.vault.path / "40_知识库" / "moc" / f"moc-{area}.md"

        if not moc_path.exists():
            return WorkflowResult(
                success=False,
                message=f"MOC 不存在: {area}",
                suggestions=[f"创建 MOC: /moc-create {area}"]
            )

        try:
            content = moc_path.read_text(encoding="utf-8")
            fm_obj = parse_frontmatter(content)

            return WorkflowResult(
                success=True,
                message=f"MOC: {area}",
                data={
                    "moc": {
                        "path": str(moc_path.relative_to(self.vault.path)),
                        "title": fm_obj.title if fm_obj else f"{area} MOC",
                        "area": area,
                        "content": content
                    }
                }
            )
        except Exception as e:
            return WorkflowResult(
                success=False,
                message=f"读取 MOC 失败: {e}",
                suggestions=["检查文件权限"]
            )

    def create_moc(self, area: str, description: str = "") -> WorkflowResult:
        """创建新的 MOC。

        Args:
            area: 领域名称
            description: MOC 描述

        Returns:
            WorkflowResult 包含创建的 MOC
        """
        mocs_path = self.vault.path / "40_知识库" / "moc"
        mocs_path.mkdir(parents=True, exist_ok=True)

        moc_file = mocs_path / f"moc-{area}.md"

        if moc_file.exists():
            return WorkflowResult(
                success=False,
                message=f"MOC 已存在: {area}",
                suggestions=[f"查看 MOC: /moc {area}", "更新 MOC: /moc-update {area}"]
            )

        # 收集该领域的笔记
        moc_content = self._collect_area_notes(area)
        moc_content.description = description or f"{area} 领域的知识地图"

        # 生成 MOC 内容
        content = self._generate_moc_content(area, moc_content)

        try:
            moc_file.write_text(content, encoding="utf-8")
        except Exception as e:
            return WorkflowResult(
                success=False,
                message=f"创建 MOC 失败: {e}",
                suggestions=["检查目录权限"]
            )

        return WorkflowResult(
            success=True,
            message=f"✅ MOC 已创建: {area}",
            created_files=[str(moc_file.relative_to(self.vault.path))],
            suggestions=["添加更多笔记到 MOC", "定期更新 MOC"]
        )

    def update_moc(self, area: str) -> WorkflowResult:
        """更新现有 MOC。

        Args:
            area: 领域名称

        Returns:
            WorkflowResult 包含更新结果
        """
        moc_path = self.vault.path / "40_知识库" / "moc" / f"moc-{area}.md"

        if not moc_path.exists():
            # 如果不存在，创建新的
            return self.create_moc(area)

        # 收集该领域的笔记
        moc_content = self._collect_area_notes(area)

        # 读取原有描述
        try:
            old_content = moc_path.read_text(encoding="utf-8")
            fm_obj = parse_frontmatter(old_content)
            # 保留原有描述（如果有）
            parser = MarkdownParser()
            old_desc = parser.find_section(old_content, "概述")
            if old_desc:
                moc_content.description = old_desc
        except Exception:
            pass

        # 生成新内容
        content = self._generate_moc_content(area, moc_content)

        try:
            moc_path.write_text(content, encoding="utf-8")
        except Exception as e:
            return WorkflowResult(
                success=False,
                message=f"更新 MOC 失败: {e}",
                suggestions=["检查文件权限"]
            )

        return WorkflowResult(
            success=True,
            message=f"✅ MOC 已更新: {area}",
            modified_files=[str(moc_path.relative_to(self.vault.path))],
            data={
                "stats": {
                    "projects": len(moc_content.projects),
                    "researches": len(moc_content.researches),
                    "brainstorms": len(moc_content.brainstorms)
                }
            }
        )

    def _collect_area_notes(self, area: str) -> MOCContent:
        """收集领域笔记。

        Args:
            area: 领域名称

        Returns:
            MOC 内容
        """
        moc_content = MOCContent(area=area)

        # 收集项目
        projects_path = self.vault.path / "10_项目" / area
        if projects_path.exists():
            for md_file in projects_path.glob("*.md"):
                entry = self._create_entry(md_file)
                if entry:
                    entry.note_type = "project"
                    moc_content.projects.append(entry)

        # 收集研究笔记
        research_path = self.vault.path / "30_研究" / area
        if research_path.exists():
            for md_file in research_path.glob("*.md"):
                entry = self._create_entry(md_file)
                if entry:
                    entry.note_type = "research"
                    moc_content.researches.append(entry)

        # 收集头脑风暴
        # 可能在研究目录或项目目录
        for path in [research_path, projects_path]:
            if path and path.exists():
                for md_file in path.glob("*头脑风暴*.md"):
                    entry = self._create_entry(md_file)
                    if entry and entry not in moc_content.brainstorms:
                        entry.note_type = "brainstorm"
                        moc_content.brainstorms.append(entry)

        # 收集知识库笔记
        knowledge_path = self.vault.path / "40_知识库" / area
        if knowledge_path.exists():
            for md_file in knowledge_path.glob("*.md"):
                entry = self._create_entry(md_file)
                if entry:
                    entry.note_type = "knowledge"
                    moc_content.knowledge.append(entry)

        return moc_content

    def _create_entry(self, md_file: Path) -> Optional[MOCEntry]:
        """创建 MOC 条目。

        Args:
            md_file: 笔记文件

        Returns:
            MOC 条目
        """
        try:
            content = md_file.read_text(encoding="utf-8")
            fm_obj = parse_frontmatter(content)
            title = fm_obj.title if fm_obj else md_file.stem

            return MOCEntry(
                path=str(md_file.relative_to(self.vault.path)),
                title=title,
                note_type=fm_obj.type if fm_obj else "note"
            )
        except Exception:
            return None

    def _generate_moc_content(self, area: str, moc: MOCContent) -> str:
        """生成 MOC 内容。

        Args:
            area: 领域名称
            moc: MOC 内容

        Returns:
            MOC 文件内容
        """
        today = date.today().isoformat()

        # 生成 frontmatter
        fm_obj = create_frontmatter(
            note_type="moc",
            title=f"{area} MOC",
            area=area,
            date=today
        )

        # 构建内容
        lines = [
            str(fm_obj),
            f"# {area} MOC",
            "",
            f"> 领域: {area} | 更新日期: {today}",
            "",
            "---",
            "",
            "## 概述",
            "",
            moc.description or f"{area} 领域的知识地图。",
            ""
        ]

        # 核心笔记
        if moc.core_notes:
            lines.append("## 核心笔记")
            lines.append("")
            for entry in moc.core_notes:
                lines.append(f"- [[{entry.title}]]")
            lines.append("")

        # 项目
        if moc.projects:
            lines.append("## 相关项目")
            lines.append("")
            for entry in moc.projects:
                lines.append(f"- [[{entry.title}]]")
            lines.append("")

        # 研究
        if moc.researches:
            lines.append("## 研究笔记")
            lines.append("")
            for entry in moc.researches:
                lines.append(f"- [[{entry.title}]]")
            lines.append("")

        # 头脑风暴
        if moc.brainstorms:
            lines.append("## 头脑风暴")
            lines.append("")
            for entry in moc.brainstorms:
                lines.append(f"- [[{entry.title}]]")
            lines.append("")

        # 知识库
        if moc.knowledge:
            lines.append("## 知识库")
            lines.append("")
            for entry in moc.knowledge:
                lines.append(f"- [[{entry.title}]]")
            lines.append("")

        # 待探索
        lines.extend([
            "## 待探索",
            "",
            "- [ ] 探索主题 1",
            "- [ ] 探索主题 2",
            "",
            "## 关联 MOC",
            "",
            "- [[相关 MOC]]",
            "",
            "---",
            "",
            f"> 注: 此 MOC 由 Obsidian KB 自动维护，最后更新: {today}"
        ])

        return "\n".join(lines)