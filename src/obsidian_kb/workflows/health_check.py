"""健康检查工作流.

检查知识库健康状态。
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any

from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult
from obsidian_kb.utils.frontmatter import parse_frontmatter
from obsidian_kb.link_resolver import LinkResolver


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

        # 2. 检查失效链接
        link_resolver = LinkResolver(self.vault.path)
        broken_links = self._check_broken_links(all_notes, link_resolver)
        issues.extend(broken_links)

        # 3. 检查孤立笔记
        orphans = self._check_orphans(all_notes, link_resolver)
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
        link_resolver: LinkResolver
    ) -> List[HealthIssue]:
        """检查失效链接。

        Args:
            notes: 笔记列表
            link_resolver: 链接解析器

        Returns:
            问题列表
        """
        issues = []

        for note in notes:
            try:
                broken = link_resolver.find_broken_links()
                for link in broken:
                    issues.append(HealthIssue(
                        severity="error",
                        type="broken_link",
                        path=link.source,
                        description=f"失效链接: [[{link.target}]]",
                        suggestion=f"修复或删除链接 [[{link.target}]]"
                    ))
            except Exception:
                continue

        return issues[:20]  # 最多报告 20 个

    def _check_orphans(
        self,
        notes: List[Path],
        link_resolver: LinkResolver
    ) -> List[HealthIssue]:
        """检查孤立笔记。

        Args:
            notes: 笔记列表
            link_resolver: 链接解析器

        Returns:
            问题列表
        """
        issues = []

        try:
            orphans = link_resolver.find_orphans()
            for path in orphans:
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
        except Exception:
            pass

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