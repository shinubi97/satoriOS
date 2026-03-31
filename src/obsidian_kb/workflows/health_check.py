"""健康检查工作流.

检查知识库健康状态。
完全基于 Obsidian CLI 进行操作，利用 CLI 的索引能力。
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any
import subprocess
import json
import re

from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult
from obsidian_kb.utils.frontmatter import parse_frontmatter


@dataclass
class HealthIssue:
    """健康问题。"""
    severity: str  # "error", "warning", "info"
    type: str
    path: str
    description: str
    suggestion: str


@dataclass
class HealthReport:
    """健康报告。"""
    check_date: str
    total_notes: int
    issues: List[HealthIssue] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)


class HealthCheckWorkflow(BaseWorkflow):
    """健康检查工作流。

    检查知识库健康状态，发现问题和建议。

    工作流程：
    1. 扫描所有笔记
    2. 检查各种健康指标
    3. 收集问题
    4. 生成报告
    5. 返回结果
    """

    # 检查项目
    CHECKS = [
        "broken_links",
        "orphan_notes",
        "missing_frontmatter",
        "stale_notes",
        "inbox_overflow"
    ]

    def execute(self, **kwargs) -> WorkflowResult:
        """执行健康检查。

        Returns:
            WorkflowResult 包含健康报告
        """
        issues = []
        statistics = {}

        # 1. 扫描所有笔记
        all_notes = list(self.vault.path.rglob("*.md"))
        statistics["total_notes"] = len(all_notes)

        # 2. 检查失效链接 (使用 CLI: obsidian unresolved)
        broken_links = self._check_broken_links(all_notes)
        issues.extend(broken_links)

        # 3. 检查孤立笔记 (使用 CLI: obsidian orphans)
        orphans = self._check_orphans(all_notes)
        issues.extend(orphans)

        # 4. 检查缺失 frontmatter
        missing_fm = self._check_frontmatter(all_notes)
        issues.extend(missing_fm)

        # 5. 检查过期笔记
        stale = self._check_stale_notes(all_notes)
        issues.extend(stale)

        # 6. 检查收件箱
        inbox_issues = self._check_inbox()
        issues.extend(inbox_issues)

        # 统计各类笔记
        statistics.update(self._collect_statistics(all_notes))

        # 7. 收集标签统计 (使用 CLI: obsidian tags counts)
        tag_stats = self._collect_tag_statistics()
        if tag_stats:
            statistics["tags"] = tag_stats

        # 生成报告
        report = HealthReport(
            check_date=date.today().isoformat(),
            total_notes=len(all_notes),
            issues=issues,
            statistics=statistics
        )

        # 构建消息
        error_count = len([i for i in issues if i.severity == "error"])
        warning_count = len([i for i in issues if i.severity == "warning"])

        if error_count > 0:
            message = f"⚠️ 发现 {error_count} 个错误, {warning_count} 个警告"
        elif warning_count > 0:
            message = f"✅ 知识库基本健康，有 {warning_count} 个警告"
        else:
            message = "✅ 知识库健康状态良好"

        return WorkflowResult(
            success=True,
            message=message,
            suggestions=self._generate_suggestions(issues),
            data={
                "health": report
            }
        )

    def _check_broken_links(
        self,
        notes: List[Path],
        link_resolver=None
    ) -> List[HealthIssue]:
        """检查失效链接。

        使用 CLI: obsidian unresolved format=json

        Args:
            notes: 笔记列表
            link_resolver: 链接解析器（已弃用，保留兼容）

        Returns:
            问题列表
        """
        issues = []

        # 尝试使用 CLI
        try:
            result = subprocess.run(
                ["obsidian", "unresolved", "format=json"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                for item in data:
                    issues.append(HealthIssue(
                        severity="error",
                        type="broken_link",
                        path=item.get("file", item.get("source", "")),
                        description=f"失效链接: [[{item.get('link', item.get('target', ''))}]]",
                        suggestion=f"修复或删除链接 [[{item.get('link', item.get('target', ''))}]]"
                    ))
                return issues[:20]
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            pass

        # 本地检查作为后备
        return self._local_check_broken_links(notes)

    def _local_check_broken_links(self, notes: List[Path]) -> List[HealthIssue]:
        """本地检查失效链接。

        Args:
            notes: 笔记列表

        Returns:
            问题列表
        """
        issues = []
        link_pattern = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')

        for note in notes:
            try:
                content = note.read_text(encoding="utf-8")
                for match in link_pattern.finditer(content):
                    target = match.group(1)

                    # 跳过 URL 链接
                    if target.startswith("http"):
                        continue

                    # 检查目标文件是否存在
                    target_path = self._resolve_link(target)
                    if not target_path:
                        issues.append(HealthIssue(
                            severity="error",
                            type="broken_link",
                            path=str(note.relative_to(self.vault.path)),
                            description=f"失效链接: [[{target}]]",
                            suggestion=f"修复或删除链接 [[{target}]]"
                        ))
            except Exception:
                continue

        return issues[:20]

    def _resolve_link(self, link: str) -> Optional[Path]:
        """解析链接到文件路径。

        Args:
            link: 链接文本

        Returns:
            文件路径或 None
        """
        # 尝试直接匹配
        for ext in ["", ".md"]:
            target_path = self.vault.path / (link + ext)
            if target_path.exists():
                return target_path

        # 尝试文件名匹配
        link_name = Path(link).name
        for md_file in self.vault.path.rglob("*.md"):
            if md_file.stem == link_name:
                return md_file

        return None

    def _check_orphans(
        self,
        notes: List[Path],
        link_resolver=None
    ) -> List[HealthIssue]:
        """检查孤立笔记。

        使用 CLI: obsidian orphans format=json

        Args:
            notes: 笔记列表
            link_resolver: 链接解析器（已弃用，保留兼容）

        Returns:
            问题列表
        """
        issues = []

        # 尝试使用 CLI
        try:
            result = subprocess.run(
                ["obsidian", "orphans", "format=json"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                for path in data:
                    # 排除 Daily 和收件箱
                    if "Daily" in path or "00_收件箱" in path:
                        continue

                    issues.append(HealthIssue(
                        severity="warning",
                        type="orphan",
                        path=path,
                        description="笔记没有被其他笔记链接",
                        suggestion="添加链接到相关笔记或 MOC"
                    ))
                return issues[:20]
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            pass

        # 本地检查作为后备
        return self._local_check_orphans(notes)

    def _local_check_orphans(self, notes: List[Path]) -> List[HealthIssue]:
        """本地检查孤立笔记。

        Args:
            notes: 笔记列表

        Returns:
            问题列表
        """
        issues = []

        # 收集所有被链接的笔记
        linked_notes = set()
        link_pattern = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')

        for note in notes:
            try:
                content = note.read_text(encoding="utf-8")
                for match in link_pattern.finditer(content):
                    target = match.group(1)
                    if not target.startswith("http"):
                        linked_notes.add(target)
            except Exception:
                continue

        # 找出孤立笔记
        for note in notes:
            rel_path = str(note.relative_to(self.vault.path))

            # 排除 Daily 和收件箱
            if "Daily" in rel_path or "00_收件箱" in rel_path:
                continue

            # 排除归档
            if "50_归档" in rel_path:
                continue

            note_name = note.stem

            # 检查是否被链接
            is_linked = note_name in linked_notes or any(
                note_name in linked for linked in linked_notes
            )

            if not is_linked:
                issues.append(HealthIssue(
                    severity="warning",
                    type="orphan",
                    path=rel_path,
                    description="笔记没有被其他笔记链接",
                    suggestion="添加链接到相关笔记或 MOC"
                ))

        return issues[:20]

    def _check_frontmatter(self, notes: List[Path]) -> List[HealthIssue]:
        """检查 frontmatter。

        Args:
            notes: 笔记列表

        Returns:
            问题列表
        """
        issues = []

        required_fields = ["id", "title", "type", "date"]

        for note in notes:
            # 跳过归档和 Daily
            if "50_归档" in str(note) or "Daily" in str(note):
                continue

            try:
                content = note.read_text(encoding="utf-8")
                fm_obj = parse_frontmatter(content)

                if not fm_obj:
                    issues.append(HealthIssue(
                        severity="warning",
                        type="missing_frontmatter",
                        path=str(note.relative_to(self.vault.path)),
                        description="笔记缺少 frontmatter",
                        suggestion="添加 frontmatter 元数据"
                    ))
                else:
                    # 检查必需字段
                    missing = []
                    for field in required_fields:
                        if not getattr(fm_obj, field, None):
                            missing.append(field)

                    if missing:
                        issues.append(HealthIssue(
                            severity="info",
                            type="incomplete_frontmatter",
                            path=str(note.relative_to(self.vault.path)),
                            description=f"缺少字段: {', '.join(missing)}",
                            suggestion="补充 frontmatter 字段"
                        ))
            except Exception:
                continue

        return issues[:20]

    def _check_stale_notes(self, notes: List[Path]) -> List[HealthIssue]:
        """检查过期笔记。

        Args:
            notes: 笔记列表

        Returns:
            问题列表
        """
        issues = []
        threshold_days = 90  # 90 天未更新

        today = datetime.now()

        for note in notes:
            # 跳过归档
            if "50_归档" in str(note):
                continue

            try:
                # 检查修改时间
                mtime = datetime.fromtimestamp(note.stat().st_mtime)
                age_days = (today - mtime).days

                if age_days > threshold_days:
                    issues.append(HealthIssue(
                        severity="info",
                        type="stale_note",
                        path=str(note.relative_to(self.vault.path)),
                        description=f"{age_days} 天未更新",
                        suggestion="考虑更新或归档"
                    ))
            except Exception:
                continue

        return issues[:20]

    def _check_inbox(self) -> List[HealthIssue]:
        """检查收件箱。

        Returns:
            问题列表
        """
        issues = []
        inbox_path = self.vault.path / "00_收件箱"

        if not inbox_path.exists():
            return issues

        inbox_count = len(list(inbox_path.glob("*.md")))

        if inbox_count > 10:
            issues.append(HealthIssue(
                severity="warning",
                type="inbox_overflow",
                path="00_收件箱",
                description=f"收件箱有 {inbox_count} 个待处理笔记",
                suggestion="处理收件箱，转化或归档笔记"
            ))
        elif inbox_count > 5:
            issues.append(HealthIssue(
                severity="info",
                type="inbox_items",
                path="00_收件箱",
                description=f"收件箱有 {inbox_count} 个笔记待处理",
                suggestion="考虑处理收件箱"
            ))

        return issues

    def _collect_statistics(self, notes: List[Path]) -> Dict[str, Any]:
        """收集统计信息。

        Args:
            notes: 笔记列表

        Returns:
            统计字典
        """
        stats = {
            "by_type": {},
            "by_area": {},
            "projects_active": 0,
            "research_notes": 0
        }

        for note in notes:
            if "50_归档" in str(note):
                continue

            try:
                content = note.read_text(encoding="utf-8")
                fm_obj = parse_frontmatter(content)

                if fm_obj:
                    # 按类型统计
                    note_type = fm_obj.type or "unknown"
                    stats["by_type"][note_type] = stats["by_type"].get(note_type, 0) + 1

                    # 按领域统计
                    area = fm_obj.area or "未分类"
                    stats["by_area"][area] = stats["by_area"].get(area, 0) + 1

                    # 特定类型计数
                    if fm_obj.type == "project" and fm_obj.status == "进行中":
                        stats["projects_active"] += 1
                    elif fm_obj.type == "research":
                        stats["research_notes"] += 1
            except Exception:
                continue

        return stats

    def _collect_tag_statistics(self) -> Dict[str, int]:
        """收集标签统计信息。

        使用 CLI: obsidian tags counts

        Returns:
            标签计数字典
        """
        # 尝试使用 CLI
        try:
            result = subprocess.run(
                ["obsidian", "tags", "counts"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout:
                # 解析输出格式 (可能是 JSON 或文本)
                try:
                    data = json.loads(result.stdout)
                    return data
                except json.JSONDecodeError:
                    # 尝试解析文本格式 (每行: tag count)
                    tag_counts = {}
                    for line in result.stdout.strip().split('\n'):
                        parts = line.split()
                        if len(parts) >= 2:
                            tag = parts[0].lstrip('#')
                            try:
                                count = int(parts[1])
                                tag_counts[tag] = count
                            except ValueError:
                                continue
                    return tag_counts
        except FileNotFoundError:
            pass

        # 本地收集作为后备
        return self._local_collect_tag_statistics()

    def _local_collect_tag_statistics(self) -> Dict[str, int]:
        """本地收集标签统计。

        Returns:
            标签计数字典
        """
        tag_counts = {}
        tag_pattern = re.compile(r'#([^\s#]+)')

        for md_file in self.vault.path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                for match in tag_pattern.finditer(content):
                    tag = match.group(1)
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            except Exception:
                continue

        return tag_counts

    def _generate_suggestions(self, issues: List[HealthIssue]) -> List[str]:
        """生成建议。

        Args:
            issues: 问题列表

        Returns:
            建议列表
        """
        suggestions = []

        # 统计问题类型
        error_count = len([i for i in issues if i.severity == "error"])
        warning_count = len([i for i in issues if i.severity == "warning"])

        if error_count > 0:
            suggestions.append(f"优先修复 {error_count} 个错误")

        if warning_count > 0:
            suggestions.append(f"处理 {warning_count} 个警告")

        # 根据问题类型给出建议
        issue_types = set(i.type for i in issues)

        if "broken_link" in issue_types:
            suggestions.append("使用 /ask 或手动修复失效链接")

        if "orphan" in issue_types:
            suggestions.append("将孤立笔记链接到 MOC 或相关笔记")

        if "inbox_overflow" in issue_types:
            suggestions.append("使用 /kickoff 或 /archive 处理收件箱")

        return suggestions[:5]