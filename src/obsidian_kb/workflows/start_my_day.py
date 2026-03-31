"""每日规划工作流.

扫描收件箱、列出进行中项目、提取待办，生成每日规划报告。
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any

from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult
from obsidian_kb.utils.frontmatter import parse_frontmatter


@dataclass
class InboxItem:
    """收件箱项目。"""
    path: str
    title: str
    age_days: int
    summary: str
    suggested_action: str  # "kickoff" | "archive" | "research" | "import"


@dataclass
class ProjectSummary:
    """项目摘要。"""
    path: str
    name: str
    area: str
    status: str
    progress: str  # 从 frontmatter 或内容中提取
    goals: List[str] = field(default_factory=list)  # 项目目标
    timeline: Optional[str] = None  # 时间线/截止日期
    pending_todos: int = 0  # 未完成待办数量
    last_update: Optional[str] = None  # 最后更新时间


@dataclass
class TaskItem:
    """待办事项。"""
    text: str
    source: str  # 来源笔记路径
    priority: str = "normal"  # "high" | "normal" | "low"


@dataclass
class DailyPlanData:
    """每日规划数据。"""
    date: str
    inbox_count: int
    inbox_items: List[InboxItem]
    active_projects: List[ProjectSummary]
    todos: List[TaskItem]
    suggestions: List[str]


class StartMyDayWorkflow(BaseWorkflow):
    """每日规划工作流。

    无需参数，直接执行。返回今日报告和建议。

    工作流程：
    1. 检查 Daily/YYYY-MM-DD.md 是否存在
    2. 扫描收件箱（限制 5 个笔记）
    3. 列出进行中项目
    4. 提取今日待办
    5. 生成建议
    6. 输出结构化报告
    """

    MAX_INBOX_ITEMS = 5  # 限制收件箱扫描数量，避免 token 溢出
    SUMMARY_LENGTH = 200  # 摘要最大字符数

    def execute(self, **kwargs) -> WorkflowResult:
        """执行每日规划。

        Returns:
            WorkflowResult 包含 DailyPlanData
        """
        today = date.today().isoformat()

        # 1. 检查今日笔记
        daily_note_path = self._check_daily_note(today)

        # 2. 扫描收件箱
        inbox_items = self._scan_inbox()

        # 3. 列出进行中项目
        active_projects = self._list_active_projects()

        # 4. 提取今日待办
        todos = self._extract_todos()

        # 5. 生成建议
        suggestions = self._generate_suggestions(inbox_items, active_projects, todos)

        # 6. 构建结果数据
        plan_data = DailyPlanData(
            date=today,
            inbox_count=len(inbox_items),
            inbox_items=inbox_items[:self.MAX_INBOX_ITEMS],
            active_projects=active_projects,
            todos=todos,
            suggestions=suggestions
        )

        return WorkflowResult(
            success=True,
            message=f"📅 {today} 每日规划已生成",
            created_files=[daily_note_path] if daily_note_path else [],
            suggestions=suggestions,
            data={
                "plan": plan_data,
                "daily_note_exists": daily_note_path is not None
            }
        )

    def _check_daily_note(self, today: str) -> Optional[str]:
        """检查今日笔记是否存在。

        Args:
            today: 日期字符串 (YYYY-MM-DD)

        Returns:
            笔记路径（如果存在），否则 None
        """
        daily_path = self.vault.path / "Daily" / f"{today}.md"
        if daily_path.exists():
            return f"Daily/{today}.md"
        return None

    def _scan_inbox(self) -> List[InboxItem]:
        """扫描收件箱。

        Returns:
            收件箱项目列表（最多 5 个）
        """
        inbox_items = []
        inbox_path = self.vault.path / "00_收件箱"

        if not inbox_path.exists():
            return inbox_items

        today = datetime.now()

        # 获取所有 .md 文件
        md_files = sorted(
            inbox_path.glob("*.md"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:self.MAX_INBOX_ITEMS]

        for md_file in md_files:
            try:
                content = md_file.read_text(encoding="utf-8")
                fm, body = self._parse_note(content)

                # 计算笔记年龄
                created_date = fm.get("date") or fm.get("created")
                age_days = 0
                if created_date:
                    try:
                        if isinstance(created_date, str):
                            created = datetime.fromisoformat(created_date[:10])
                        else:
                            created = datetime.fromisoformat(str(created_date)[:10])
                        age_days = (today - created).days
                    except (ValueError, TypeError):
                        pass

                # 提取摘要
                summary = self._extract_summary(body)

                # 推断建议操作
                suggested_action = self._infer_action(fm, body)

                inbox_items.append(InboxItem(
                    path=str(md_file.relative_to(self.vault.path)),
                    title=fm.get("title", md_file.stem),
                    age_days=age_days,
                    summary=summary,
                    suggested_action=suggested_action
                ))
            except Exception:
                # 跳过解析失败的文件
                continue

        return inbox_items

    def _list_active_projects(self) -> List[ProjectSummary]:
        """列出进行中项目。

        Returns:
            项目摘要列表
        """
        projects = []
        projects_path = self.vault.path / "10_项目"

        if not projects_path.exists():
            return projects

        # 搜索所有项目目录中的笔记
        for area_dir in projects_path.iterdir():
            if not area_dir.is_dir():
                continue

            for md_file in area_dir.glob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    fm, _ = self._parse_note(content)

                    # 只收集进行中的项目
                    status = fm.get("status", "")
                    tags = fm.get("tags", [])

                    # 判断是否进行中：status 字段或 #进行中 标签
                    is_active = (
                        "进行中" in status or
                        "进行中" in tags or
                        status == "in_progress" or
                        "#进行中" in content
                    )

                    if is_active:
                        projects.append(ProjectSummary(
                            path=str(md_file.relative_to(self.vault.path)),
                            name=fm.get("title", md_file.stem),
                            area=area_dir.name,
                            status=status or "进行中",
                            progress=self._extract_progress(content),
                            goals=self._extract_goals(content, fm),
                            timeline=fm.get("timeline") or fm.get("截止日期"),
                            pending_todos=self._count_pending_todos(content),
                            last_update=fm.get("updated")
                        ))
                except Exception:
                    continue

        return projects

    def _extract_todos(self) -> List[TaskItem]:
        """提取今日待办。

        从 Daily 目录的笔记中提取未完成的待办项。

        Returns:
            待办事项列表
        """
        todos = []
        daily_path = self.vault.path / "Daily"

        if not daily_path.exists():
            return todos

        # 只检查最近的笔记（最近 7 天）
        today = datetime.now()

        for md_file in sorted(daily_path.glob("*.md"), reverse=True)[:7]:
            try:
                content = md_file.read_text(encoding="utf-8")

                # 提取未完成的待办项
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("- [ ]"):
                        todo_text = line[5:].strip()
                        if todo_text:
                            todos.append(TaskItem(
                                text=todo_text,
                                source=str(md_file.relative_to(self.vault.path))
                            ))
            except Exception:
                continue

        return todos

    def _generate_suggestions(
        self,
        inbox_items: List[InboxItem],
        projects: List[ProjectSummary],
        todos: List[TaskItem]
    ) -> List[str]:
        """生成今日建议。

        Args:
            inbox_items: 收件箱项目
            projects: 进行中项目
            todos: 待办事项

        Returns:
            建议列表
        """
        suggestions = []

        # 收件箱处理建议
        if inbox_items:
            actions = {}
            for item in inbox_items:
                actions[item.suggested_action] = actions.get(item.suggested_action, 0) + 1

            if "kickoff" in actions:
                suggestions.append(f"处理 {actions['kickoff']} 个项目想法 (使用 /kickoff)")
            if "research" in actions:
                suggestions.append(f"开始 {actions['research']} 个研究主题 (使用 /research)")
            if "archive" in actions:
                suggestions.append(f"归档 {actions['archive']} 个过期想法 (使用 /archive)")

        # 项目跟进建议
        if projects:
            suggestions.append(f"跟进 {len(projects)} 个进行中项目")

        # 待办提醒
        if todos:
            high_priority = [t for t in todos if t.priority == "high"]
            if high_priority:
                suggestions.append(f"优先处理 {len(high_priority)} 个高优先级待办")

        return suggestions

    def _parse_note(self, content: str) -> tuple:
        """解析笔记内容。

        Args:
            content: 笔记内容

        Returns:
            (frontmatter dict, body string)
        """
        try:
            fm_obj = parse_frontmatter(content)
            if fm_obj:
                # Convert Frontmatter dataclass to dict
                fm = fm_obj.to_dict()
            else:
                fm = {}

            # 去除 frontmatter 部分
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    body = parts[2].strip()
                else:
                    body = content
            else:
                body = content
            return fm, body
        except Exception:
            # If parsing fails, return empty dict and original content
            return {}, content

    def _extract_summary(self, body: str) -> str:
        """提取摘要。

        Args:
            body: 笔记正文

        Returns:
            摘要文本（最多 SUMMARY_LENGTH 字符）
        """
        # 去除标题和空行
        lines = []
        for line in body.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line)

        summary = " ".join(lines)
        return summary[:self.SUMMARY_LENGTH] if len(summary) > self.SUMMARY_LENGTH else summary

    def _infer_action(self, fm: dict, body: str) -> str:
        """推断建议操作。

        Args:
            fm: frontmatter
            body: 正文

        Returns:
            建议操作 ("kickoff" | "archive" | "research" | "import")
        """
        tags = fm.get("tags", [])
        note_type = fm.get("type", "")
        title = fm.get("title", "").lower()

        # 根据标签推断
        if "项目" in tags or "project" in tags:
            return "kickoff"
        if "研究" in tags or "research" in tags:
            return "research"
        if "归档" in tags or "archive" in tags:
            return "archive"

        # 根据标题关键词推断
        if any(kw in title for kw in ["项目", "想法", "idea"]):
            return "kickoff"
        if any(kw in title for kw in ["研究", "学习", "调研"]):
            return "research"

        # 默认建议归档
        return "archive"

    def _extract_progress(self, content: str) -> str:
        """提取项目进度描述。

        Args:
            content: 笔记内容

        Returns:
            进度描述
        """
        # 查找进展记录章节
        lines = content.split("\n")
        in_progress_section = False

        for line in lines:
            if "进展记录" in line or "进度" in line:
                in_progress_section = True
                continue

            if in_progress_section and line.startswith("##"):
                break

            if in_progress_section and line.strip() and not line.startswith("#"):
                return line.strip()[:100]

        return "进行中"

    def _extract_goals(self, content: str, fm: dict) -> List[str]:
        """提取项目目标。

        Args:
            content: 笔记内容
            fm: frontmatter 字典

        Returns:
            目标列表
        """
        goals = []

        # 从 frontmatter 获取
        if "goals" in fm:
            g = fm["goals"]
            goals = g if isinstance(g, list) else [g]
            return goals

        # 从内容中提取
        lines = content.split('\n')
        in_goals = False
        for line in lines:
            if "目标" in line and line.startswith('#'):
                in_goals = True
                continue
            if in_goals and line.startswith('#'):
                break
            if in_goals and line.strip().startswith('- [ ]'):
                goal_text = line.strip()[5:].strip()
                if goal_text:
                    goals.append(goal_text)

        return goals[:5]

    def _count_pending_todos(self, content: str) -> int:
        """统计未完成待办数量。

        Args:
            content: 笔记内容

        Returns:
            未完成待办数量
        """
        count = 0
        for line in content.split('\n'):
            if line.strip().startswith('- [ ]'):
                count += 1
        return count