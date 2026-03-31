"""头脑风暴工作流.

创建头脑风暴笔记，支持多轮对话追加内容。
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any

from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult
from obsidian_kb.utils.frontmatter import parse_frontmatter, create_frontmatter
from obsidian_kb.parser import MarkdownParser


@dataclass
class BrainstormInsights:
    """头脑风暴精华提取。"""
    core_conclusions: List[str] = field(default_factory=list)
    viable_solutions: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)


class BrainstormWorkflow(BaseWorkflow):
    """头脑风暴工作流。

    创建头脑风暴笔记，支持多轮对话。

    工作流程：
    1. 查找关联项目（如果提供）
    2. 创建头脑风暴笔记
    3. 返回笔记路径，Agent 可继续对话追加内容
    """

    def execute(
        self,
        topic: str,
        project: str = None,
        area: str = None,
        initial_idea: str = None
    ) -> WorkflowResult:
        """创建头脑风暴笔记。

        Args:
            topic: 头脑风暴主题
            project: 关联的项目名称
            area: 所属领域
            initial_idea: 初始想法描述

        Returns:
            WorkflowResult 包含创建的笔记路径
        """
        # 确定领域
        if not area and project:
            # 尝试从项目推断领域
            area = self._infer_area_from_project(project)
        area = self._ensure_area(area)

        # 1. 查找关联项目
        project_path = None
        if project:
            project_path = self._find_project(project, area)

        # 2. 创建头脑风暴笔记
        note_path = self._create_brainstorm_note(
            topic=topic,
            area=area,
            project=project,
            project_path=project_path,
            initial_idea=initial_idea
        )

        if not note_path:
            return WorkflowResult(
                success=False,
                message=f"创建头脑风暴笔记失败: {topic}",
                suggestions=["检查目录权限"]
            )

        # 3. 构建结果
        suggestions = []
        if project:
            suggestions.append(f"已关联项目: {project}")
        suggestions.append("继续对话追加内容到笔记")
        suggestions.append("对话结束后提取精华")

        return WorkflowResult(
            success=True,
            message=f"✅ 头脑风暴笔记已创建: {topic}",
            created_files=[note_path],
            suggestions=suggestions,
            data={
                "topic": topic,
                "area": area,
                "project": project,
                "note_path": note_path
            }
        )

    def _infer_area_from_project(self, project: str) -> Optional[str]:
        """从项目推断领域。

        Args:
            project: 项目名称

        Returns:
            推断的领域
        """
        projects_path = self.vault.path / "10_项目"

        if not projects_path.exists():
            return None

        for area_dir in projects_path.iterdir():
            if not area_dir.is_dir():
                continue

            for md_file in area_dir.glob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    fm_obj = parse_frontmatter(content)
                    title = fm_obj.title if fm_obj else md_file.stem

                    if project.lower() in title.lower():
                        return area_dir.name
                except Exception:
                    continue

        return None

    def _find_project(self, project: str, area: str) -> Optional[str]:
        """查找项目路径。

        Args:
            project: 项目名称
            area: 领域

        Returns:
            项目笔记路径
        """
        projects_path = self.vault.path / "10_项目" / area

        if not projects_path.exists():
            return None

        project_lower = project.lower()

        for md_file in projects_path.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                fm_obj = parse_frontmatter(content)
                title = fm_obj.title if fm_obj else md_file.stem

                if project_lower in title.lower():
                    return str(md_file.relative_to(self.vault.path))
            except Exception:
                continue

        return None

    def _create_brainstorm_note(
        self,
        topic: str,
        area: str,
        project: Optional[str],
        project_path: Optional[str],
        initial_idea: Optional[str]
    ) -> Optional[str]:
        """创建头脑风暴笔记。

        Args:
            topic: 主题
            area: 领域
            project: 项目名称
            project_path: 项目路径
            initial_idea: 初始想法

        Returns:
            创建的笔记路径
        """
        # 确定存储位置
        if project and project_path:
            # 存储在项目目录
            storage_path = Path(project_path).parent
        else:
            # 存储在研究目录
            storage_path = self.vault.path / "30_研究" / area

        storage_path.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        today = date.today().strftime("%Y-%m-%d")
        safe_topic = self._sanitize_filename(topic)
        filename = f"{safe_topic}_头脑风暴_{today}.md"

        note_file = self.vault.path / storage_path / filename

        # 如果文件已存在，添加计数器
        counter = 1
        while note_file.exists():
            filename = f"{safe_topic}_头脑风暴_{today}_{counter}.md"
            note_file = self.vault.path / storage_path / filename
            counter += 1

        # 生成 frontmatter
        fm_obj = create_frontmatter(
            note_type="brainstorm",
            title=f"{topic} 头脑风暴",
            area=area,
            date=today
        )

        # 构建项目关联部分
        project_section = ""
        if project:
            project_link = f"[[{project}]]" if project_path else project
            project_section = f"> 关联项目: {project_link} | 日期: {today}"

        # 初始想法部分
        initial_section = initial_idea if initial_idea else "（待添加）"

        content = f"""{fm_obj}
# {topic} 头脑风暴

{project_section}

---

## 原始想法

{initial_section}

## 头脑风暴过程

### 问题 1: ...
**思考**: ...

## 发散想法

- 想法 1: ...
- 想法 2: ...

## 精华提取

### 核心结论
- ...

### 可行方案
1. 方案 A: ...
2. 方案 B: ...

### 下一步行动
- [ ] 行动项 1
- [ ] 行动项 2

## 关联思考

- [[相关笔记 1]]
"""

        try:
            note_file.write_text(content, encoding="utf-8")
            return str(note_file.relative_to(self.vault.path))
        except Exception:
            return None

    def append_to_note(self, note_path: str, content: str) -> bool:
        """追加内容到头脑风暴笔记。

        Args:
            note_path: 笔记路径
            content: 要追加的内容

        Returns:
            是否成功
        """
        full_path = self.vault.path / note_path

        if not full_path.exists():
            return False

        try:
            with open(full_path, "a", encoding="utf-8") as f:
                f.write("\n\n" + content)
            return True
        except Exception:
            return False

    def extract_insights(self, note_path: str) -> BrainstormInsights:
        """从头脑风暴笔记中提取精华。

        Args:
            note_path: 笔记路径

        Returns:
            提取的精华
        """
        full_path = self.vault.path / note_path

        if not full_path.exists():
            return BrainstormInsights()

        try:
            content = full_path.read_text(encoding="utf-8")
            parser = MarkdownParser()

            insights = BrainstormInsights()

            # 查找核心结论章节
            conclusions_section = parser.find_section(content, "核心结论")
            if conclusions_section:
                # 提取列表项
                for line in conclusions_section.split("\n"):
                    line = line.strip()
                    if line.startswith("- "):
                        insights.core_conclusions.append(line[2:])

            # 查找可行方案章节
            solutions_section = parser.find_section(content, "可行方案")
            if solutions_section:
                for line in solutions_section.split("\n"):
                    line = line.strip()
                    if line.startswith(("1. ", "2. ", "3. ", "4. ", "5. ")):
                        insights.viable_solutions.append(line[3:])

            # 查找下一步行动章节
            actions_section = parser.find_section(content, "下一步行动")
            if actions_section:
                checkboxes = parser.extract_checkboxes(actions_section)
                insights.next_actions = [cb.text for cb in checkboxes]

            return insights
        except Exception:
            return BrainstormInsights()

    def update_project(self, project_name: str, insights: BrainstormInsights) -> bool:
        """将精华追加到项目文档。

        Args:
            project_name: 项目名称
            insights: 提取的精华

        Returns:
            是否成功
        """
        # 查找项目文档
        project_file = None
        projects_path = self.vault.path / "10_项目"

        if not projects_path.exists():
            return False

        for area_dir in projects_path.iterdir():
            if not area_dir.is_dir():
                continue

            for md_file in area_dir.glob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    fm_obj = parse_frontmatter(content)
                    title = fm_obj.title if fm_obj else md_file.stem

                    if project_name.lower() in title.lower():
                        project_file = md_file
                        break
                except Exception:
                    continue

            if project_file:
                break

        if not project_file:
            return False

        try:
            # 追加精华内容
            with open(project_file, "a", encoding="utf-8") as f:
                f.write(f"\n\n## 头脑风暴精华 ({date.today()})\n")

                if insights.core_conclusions:
                    f.write("\n### 核心结论\n")
                    for c in insights.core_conclusions:
                        f.write(f"- {c}\n")

                if insights.viable_solutions:
                    f.write("\n### 可行方案\n")
                    for i, s in enumerate(insights.viable_solutions, 1):
                        f.write(f"{i}. {s}\n")

                if insights.next_actions:
                    f.write("\n### 下一步行动\n")
                    for a in insights.next_actions:
                        f.write(f"- [ ] {a}\n")

            return True
        except Exception:
            return False

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名中的特殊字符。"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()[:100]