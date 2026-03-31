"""项目启动工作流.

从收件箱想法启动新项目。
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any

from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult
from obsidian_kb.utils.frontmatter import parse_frontmatter, create_frontmatter


@dataclass
class ProjectDetails:
    """项目详情。"""
    name: str
    area: str
    timeline: str
    goals: List[str] = field(default_factory=list)
    source_idea: Optional[str] = None
    source_path: Optional[str] = None


class KickoffWorkflow(BaseWorkflow):
    """项目启动工作流。

    从收件箱的想法创建新项目。

    工作流程：
    1. 查找原想法（在收件箱中搜索匹配）
    2. 创建项目文档（使用模板）
    3. 归档原想法
    4. 返回结果，包含 MOC 链接建议
    """

    def execute(
        self,
        idea_name: str,
        area: str = None,
        timeline: str = "1个月",
        goals: List[str] = None,
        link_to_moc: str = None
    ) -> WorkflowResult:
        """启动新项目。

        Args:
            idea_name: 想法名称（用于搜索匹配）
            area: 所属领域
            timeline: 期望完成时间
            goals: 项目目标列表
            link_to_moc: 要链接的 MOC 名称（可选）

        Returns:
            WorkflowResult 包含创建的项目信息
        """
        # 确定领域
        area = self._ensure_area(area)

        # 1. 查找原想法
        source_idea = self._find_idea(idea_name)

        if not source_idea:
            return WorkflowResult(
                success=False,
                message=f"未找到匹配的想法: {idea_name}",
                suggestions=["检查想法名称是否正确", "手动创建项目文档"]
            )

        # 2. 创建项目文档
        project_name = source_idea.get("title", idea_name)
        project_path = self._create_project_document(
            name=project_name,
            area=area,
            timeline=timeline,
            goals=goals or [],
            source_path=source_idea.get("path")
        )

        if not project_path:
            return WorkflowResult(
                success=False,
                message=f"创建项目文档失败: {project_name}",
                suggestions=["检查目录权限", "手动创建项目文档"]
            )

        # 3. 归档原想法
        archived_path = self._archive_idea(source_idea.get("path"))

        # 4. 构建结果
        suggestions = []
        if link_to_moc:
            suggestions.append(f"已链接到 MOC: {link_to_moc}")
        else:
            suggestions.append(f"考虑链接到 MOC: moc-{area}")

        project_details = ProjectDetails(
            name=project_name,
            area=area,
            timeline=timeline,
            goals=goals or [],
            source_idea=source_idea.get("title"),
            source_path=source_idea.get("path")
        )

        created_files = [project_path]
        if archived_path:
            created_files.append(archived_path)

        return WorkflowResult(
            success=True,
            message=f"✅ 项目已启动: {project_name}",
            created_files=created_files,
            suggestions=suggestions,
            data={
                "project": project_details,
                "project_path": project_path,
                "archived_idea": archived_path
            }
        )

    def _find_idea(self, idea_name: str) -> Optional[Dict[str, Any]]:
        """在收件箱中查找想法。

        Args:
            idea_name: 想法名称

        Returns:
            找到的想法信息，如果未找到返回 None
        """
        inbox_path = self.vault.path / "00_收件箱"

        if not inbox_path.exists():
            return None

        # 搜索匹配的笔记
        matches = []

        for md_file in inbox_path.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                fm_obj = parse_frontmatter(content)
                if fm_obj:
                    title = fm_obj.title
                else:
                    # 如果没有 frontmatter，使用文件名
                    title = md_file.stem

                # 检查是否匹配
                if self._matches_idea(title, idea_name):
                    matches.append({
                        "path": str(md_file.relative_to(self.vault.path)),
                        "title": title,
                        "file": md_file
                    })
            except Exception:
                continue

        # 如果找到多个匹配，返回第一个（按修改时间排序）
        if matches:
            # 按文件修改时间排序，最新的优先
            matches.sort(key=lambda x: x["file"].stat().st_mtime, reverse=True)
            return matches[0]

        return None

    def _matches_idea(self, title: str, idea_name: str) -> bool:
        """检查标题是否匹配想法名称。

        Args:
            title: 笔记标题
            idea_name: 想法名称

        Returns:
            是否匹配
        """
        title_lower = title.lower()
        idea_lower = idea_name.lower()

        # 精确匹配
        if title_lower == idea_lower:
            return True

        # 包含匹配
        if idea_lower in title_lower or title_lower in idea_lower:
            return True

        return False

    def _create_project_document(
        self,
        name: str,
        area: str,
        timeline: str,
        goals: List[str],
        source_path: Optional[str]
    ) -> Optional[str]:
        """创建项目文档。

        Args:
            name: 项目名称
            area: 所属领域
            timeline: 时间线
            goals: 目标列表
            source_path: 来源想法路径

        Returns:
            创建的文档路径
        """
        # 确保项目目录存在
        projects_path = self.vault.path / "10_项目" / area
        projects_path.mkdir(parents=True, exist_ok=True)

        # 生成文件名（处理特殊字符）
        safe_name = self._sanitize_filename(name)
        project_file = projects_path / f"{safe_name}.md"

        # 如果文件已存在，添加后缀
        counter = 1
        while project_file.exists():
            project_file = projects_path / f"{safe_name}_{counter}.md"
            counter += 1

        # 生成笔记 ID
        note_id = self._generate_note_id()

        # 生成 frontmatter
        today = date.today().isoformat()

        fm_obj = create_frontmatter(
            note_type="project",
            title=name,
            area=area,
            date=today,
            status="进行中"
        )

        # 转换为 YAML 字符串
        fm = str(fm_obj)

        # 构建内容
        source_note = f"\n> 来自: {source_path}" if source_path else ""
        goals_section = "\n".join(f"- {g}" for g in goals) if goals else "- [ ] 定义项目目标"

        content = f"""{fm}
# {name}
{source_note}

---

## 项目目标

{goals_section}

## 时间线

- **开始日期**: {today}
- **目标完成**: {timeline}

## 进展记录

### {today} - 启动

项目启动，初始规划完成。

## 相关资源

- [[相关笔记]]

## 复盘总结

（项目完成后填写）
"""

        try:
            project_file.write_text(content, encoding="utf-8")
            return str(project_file.relative_to(self.vault.path))
        except Exception:
            return None

    def _archive_idea(self, idea_path: Optional[str]) -> Optional[str]:
        """归档原想法。

        Args:
            idea_path: 想法笔记路径

        Returns:
            归档后的路径
        """
        if not idea_path:
            return None

        source_file = self.vault.path / idea_path
        if not source_file.exists():
            return None

        # 创建归档目录
        today = date.today()
        archive_dir = self.vault.path / "50_归档" / today.strftime("%Y-%m")
        archive_dir.mkdir(parents=True, exist_ok=True)

        # 移动文件
        dest_file = archive_dir / source_file.name

        try:
            source_file.rename(dest_file)
            return str(dest_file.relative_to(self.vault.path))
        except Exception:
            return None

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名中的特殊字符。

        Args:
            name: 原始名称

        Returns:
            安全的文件名
        """
        # 替换特殊字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')

        # 去除首尾空格
        name = name.strip()

        # 限制长度
        if len(name) > 100:
            name = name[:100]

        return name

    def find_matching_ideas(self, idea_name: str) -> List[Dict[str, Any]]:
        """查找所有匹配的想法（供 Agent 展示给用户选择）。

        Args:
            idea_name: 想法名称

        Returns:
            匹配的想法列表
        """
        inbox_path = self.vault.path / "00_收件箱"

        if not inbox_path.exists():
            return []

        matches = []

        for md_file in inbox_path.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                fm_obj = parse_frontmatter(content)
                title = fm_obj.title if fm_obj else md_file.stem

                if self._matches_idea(title, idea_name):
                    # 提取摘要
                    summary = self._extract_summary(content)

                    matches.append({
                        "path": str(md_file.relative_to(self.vault.path)),
                        "title": title,
                        "summary": summary[:100]
                    })
            except Exception:
                continue

        return matches

    def _extract_summary(self, content: str) -> str:
        """提取内容摘要。"""
        # 去除 frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2]

        # 提取非标题文本
        lines = []
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line)

        return " ".join(lines)[:200]