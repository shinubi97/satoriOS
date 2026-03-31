"""MOC 回顾工作流.

检查 MOC 的完整性和健康状态。
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any

from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult
from obsidian_kb.utils.frontmatter import parse_frontmatter
from obsidian_kb.link_resolver import LinkResolver
from obsidian_kb.parser import MarkdownParser


@dataclass
class MOCIssue:
    """MOC 问题。"""
    type: str
    description: str
    suggestion: str


@dataclass
class MOCReviewResult:
    """MOC 回顾结果。"""
    moc_path: str
    area: str
    total_links: int
    broken_links: int
    missing_notes: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    issues: List[MOCIssue] = field(default_factory=list)


class MocReviewWorkflow(BaseWorkflow):
    """MOC 回顾工作流。

    检查 MOC 的完整性和健康状态。

    工作流程：
    1. 读取 MOC 内容
    2. 提取所有链接
    3. 检查链接有效性
    4. 检查是否有遗漏笔记
    5. 生成改进建议
    """

    def execute(self, moc_path: str = None, area: str = None) -> WorkflowResult:
        """回顾 MOC。

        Args:
            moc_path: MOC 文件路径
            area: 领域名称（如果未提供 moc_path）

        Returns:
            WorkflowResult 包含回顾结果
        """
        # 确定要回顾的 MOC
        if moc_path:
            target_path = self.vault.path / moc_path
        elif area:
            target_path = self.vault.path / "40_知识库" / "moc" / f"moc-{area}.md"
        else:
            return WorkflowResult(
                success=False,
                message="请指定 MOC 路径或领域名称",
                suggestions=["/moc-review --area=领域名", "/moc-review --path=MOC路径"]
            )

        if not target_path.exists():
            return WorkflowResult(
                success=False,
                message=f"MOC 不存在: {target_path}",
                suggestions=[f"创建 MOC: /moc-create {area or '领域名'}"]
            )

        # 读取 MOC
        try:
            content = target_path.read_text(encoding="utf-8")
        except Exception as e:
            return WorkflowResult(
                success=False,
                message=f"读取 MOC 失败: {e}",
                suggestions=["检查文件权限"]
            )

        # 解析
        fm_obj = parse_frontmatter(content)
        moc_area = fm_obj.area if fm_obj else area or target_path.stem.replace("moc-", "")
        moc_title = fm_obj.title if fm_obj else target_path.stem

        # 提取链接
        parser = MarkdownParser()
        links = parser.extract_wiki_links(content)

        # 检查链接
        link_resolver = LinkResolver(self.vault.path)
        broken_links = []
        missing_notes = []

        for link in links:
            # 跳过特殊链接
            if link.target.startswith("相关") or link.target in ["相关 MOC", "相关笔记"]:
                continue

            if not link_resolver.check_link_exists(link.target):
                broken_links.append(link.target)

        # 检查遗漏笔记
        missing = self._check_missing_notes(moc_area, links)

        # 生成建议
        suggestions = self._generate_suggestions(broken_links, missing)

        # 构建结果
        result = MOCReviewResult(
            moc_path=str(target_path.relative_to(self.vault.path)),
            area=moc_area,
            total_links=len(links),
            broken_links=len(broken_links),
            missing_notes=missing,
            suggestions=suggestions
        )

        # 添加问题
        if broken_links:
            result.issues.append(MOCIssue(
                type="broken_links",
                description=f"发现 {len(broken_links)} 个失效链接",
                suggestion="修复或删除失效链接"
            ))

        if missing:
            result.issues.append(MOCIssue(
                type="missing_notes",
                description=f"有 {len(missing)} 个笔记未包含在 MOC 中",
                suggestion="更新 MOC 添加遗漏的笔记"
            ))

        # 生成消息
        if broken_links or missing:
            message = f"⚠️ MOC 需要更新: {len(broken_links)} 个失效链接, {len(missing)} 个遗漏笔记"
        else:
            message = f"✅ MOC 状态良好"

        return WorkflowResult(
            success=True,
            message=message,
            suggestions=suggestions,
            data={
                "review": result
            }
        )

    def _check_missing_notes(
        self,
        area: str,
        existing_links: List
    ) -> List[str]:
        """检查遗漏的笔记。

        Args:
            area: 领域名称
            existing_links: 现有链接列表

        Returns:
            遗漏笔记列表
        """
        missing = []
        existing_targets = {link.target for link in existing_links}

        # 检查项目目录
        projects_path = self.vault.path / "10_项目" / area
        if projects_path.exists():
            for md_file in projects_path.glob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    fm_obj = parse_frontmatter(content)
                    title = fm_obj.title if fm_obj else md_file.stem

                    if title not in existing_targets and md_file.stem not in existing_targets:
                        missing.append(f"项目: {title}")
                except Exception:
                    continue

        # 检查研究目录
        research_path = self.vault.path / "30_研究" / area
        if research_path.exists():
            for md_file in research_path.glob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    fm_obj = parse_frontmatter(content)
                    title = fm_obj.title if fm_obj else md_file.stem

                    if title not in existing_targets and md_file.stem not in existing_targets:
                        # 避免重复添加头脑风暴
                        if "头脑风暴" not in title:
                            missing.append(f"研究: {title}")
                except Exception:
                    continue

        return missing[:10]  # 最多返回 10 个

    def _generate_suggestions(
        self,
        broken_links: List[str],
        missing_notes: List[str]
    ) -> List[str]:
        """生成改进建议。

        Args:
            broken_links: 失效链接
            missing_notes: 遗漏笔记

        Returns:
            建议列表
        """
        suggestions = []

        if broken_links:
            suggestions.append(f"修复 {len(broken_links)} 个失效链接")

        if missing_notes:
            suggestions.append(f"添加 {len(missing_notes)} 个遗漏笔记到 MOC")

        if not broken_links and not missing_notes:
            suggestions.append("MOC 状态良好，定期更新保持同步")

        return suggestions

    def review_all_mocs(self) -> WorkflowResult:
        """回顾所有 MOC。

        Returns:
            WorkflowResult 包含所有 MOC 回顾结果
        """
        mocs_path = self.vault.path / "40_知识库" / "moc"

        if not mocs_path.exists():
            return WorkflowResult(
                success=True,
                message="没有找到 MOC",
                suggestions=["创建第一个 MOC: /moc-create 领域名"]
            )

        results = []
        for moc_file in mocs_path.glob("*.md"):
            result = self.execute(moc_path=str(moc_file.relative_to(self.vault.path)))
            if result.success:
                results.append(result.data["review"])

        # 统计
        total_issues = sum(len(r.issues) for r in results)
        total_broken = sum(r.broken_links for r in results)

        return WorkflowResult(
            success=True,
            message=f"回顾了 {len(results)} 个 MOC，发现 {total_issues} 个问题",
            suggestions=[f"更新 [[{r.moc_path}]]" for r in results if r.issues],
            data={
                "reviews": results,
                "summary": {
                    "total_mocs": len(results),
                    "total_issues": total_issues,
                    "total_broken_links": total_broken
                }
            }
        )