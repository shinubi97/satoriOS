"""归档工作流.

将完成的笔记移动到归档目录。
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any

from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult
from obsidian_kb.utils.frontmatter import parse_frontmatter, update_frontmatter


@dataclass
class ArchiveDetails:
    """归档详情。"""
    original_path: str
    archived_path: str
    archive_date: str
    reason: str = "完成"


class ArchiveWorkflow(BaseWorkflow):
    """归档工作流。

    将笔记移动到归档目录，更新状态。

    工作流程：
    1. 验证源笔记存在
    2. 确定归档目标路径
    3. 移动笔记
    4. 更新 frontmatter 状态
    5. 返回归档结果
    """

    def execute(
        self,
        note_path: str,
        reason: str = "完成"
    ) -> WorkflowResult:
        """归档笔记。

        Args:
            note_path: 要归档的笔记路径
            reason: 归档原因

        Returns:
            WorkflowResult 包含归档信息
        """
        source_file = self.vault.path / note_path

        if not source_file.exists():
            return WorkflowResult(
                success=False,
                message=f"笔记不存在: {note_path}",
                suggestions=["检查路径是否正确"]
            )

        # 1. 读取笔记内容
        try:
            content = source_file.read_text(encoding="utf-8")
        except Exception as e:
            return WorkflowResult(
                success=False,
                message=f"读取笔记失败: {e}",
                suggestions=["检查文件权限"]
            )

        # 2. 确定归档目标路径
        today = date.today()
        archive_dir = self.vault.path / "50_归档" / today.strftime("%Y-%m")
        archive_dir.mkdir(parents=True, exist_ok=True)

        dest_file = archive_dir / source_file.name

        # 处理文件名冲突
        counter = 1
        while dest_file.exists():
            stem = source_file.stem
            suffix = source_file.suffix
            dest_file = archive_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        # 3. 更新 frontmatter
        updated_content = self._update_status(content, "已归档", reason)

        # 4. 移动笔记
        try:
            dest_file.write_text(updated_content, encoding="utf-8")
            source_file.unlink()
        except Exception as e:
            return WorkflowResult(
                success=False,
                message=f"移动笔记失败: {e}",
                suggestions=["检查目录权限"]
            )

        archived_path = str(dest_file.relative_to(self.vault.path))

        details = ArchiveDetails(
            original_path=note_path,
            archived_path=archived_path,
            archive_date=today.isoformat(),
            reason=reason
        )

        return WorkflowResult(
            success=True,
            message=f"✅ 笔记已归档: {note_path} → {archived_path}",
            created_files=[archived_path],
            modified_files=[],
            suggestions=["可以继续归档其他笔记"],
            data={
                "archive": details
            }
        )

    def _update_status(self, content: str, status: str, reason: str) -> str:
        """更新笔记状态。

        Args:
            content: 笔记内容
            status: 新状态
            reason: 归档原因

        Returns:
            更新后的内容
        """
        try:
            fm_obj = parse_frontmatter(content)
            if fm_obj:
                # 更新状态
                fm_obj.status = status
                fm_obj.archive_date = date.today().isoformat()
                fm_obj.archive_reason = reason
                return update_frontmatter(content, fm_obj)
        except Exception:
            pass

        return content

    def batch_archive(
        self,
        note_paths: List[str],
        reason: str = "批量归档"
    ) -> WorkflowResult:
        """批量归档笔记。

        Args:
            note_paths: 笔记路径列表
            reason: 归档原因

        Returns:
            WorkflowResult 包含批量归档结果
        """
        archived = []
        failed = []

        for path in note_paths:
            result = self.execute(path, reason)
            if result.success:
                archived.append(path)
            else:
                failed.append({
                    "path": path,
                    "error": result.message
                })

        if failed:
            return WorkflowResult(
                success=len(archived) > 0,
                message=f"归档完成: {len(archived)} 成功, {len(failed)} 失败",
                created_files=[r.data["archive"].archived_path for r in [self.execute(p, reason) for p in archived] if r.success],
                data={
                    "archived": archived,
                    "failed": failed
                }
            )

        return WorkflowResult(
            success=True,
            message=f"✅ 批量归档完成: {len(archived)} 个笔记",
            created_files=[r.data["archive"].archived_path for r in [self.execute(p, reason) for p in archived] if r.success],
            data={
                "archived": archived
            }
        )