"""归档工作流.

将完成的笔记移动到归档目录，支持反向链接检查和批量归档。
完全基于 Obsidian CLI 进行操作，利用 CLI 的索引能力。
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import re
import subprocess

from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult
from obsidian_kb.utils.frontmatter import parse_frontmatter, update_frontmatter
from obsidian_kb.config import Config
from obsidian_kb.vault import Vault


@dataclass
class BacklinkInfo:
    """反向链接信息。"""
    source_path: str
    link_text: str
    needs_update: bool = True


@dataclass
class ArchivePreview:
    """归档预览（Dry-run 结果）。"""
    note_path: str
    target_path: str
    backlinks: List[BacklinkInfo]
    link_updates: List[Dict[str, str]]


@dataclass
class ArchiveDetails:
    """归档详情。"""
    original_path: str
    archived_path: str
    archive_date: str
    reason: str = "完成"
    backlinks: List[BacklinkInfo] = field(default_factory=list)


class ArchiveWorkflow(BaseWorkflow):
    """归档工作流（基于 CLI）。

    将笔记移动到归档目录，更新状态，处理反向链接。

    工作流程：
    1. 验证源笔记存在
    2. 检查反向链接
    3. 创建备份
    4. Dry-run 预览
    5. 确认归档
    6. 移动笔记
    7. 更新 frontmatter 状态
    8. 更新反向链接
    9. 返回归档结果
    """

    ARCHIVE_DIR = "50_归档"
    BACKUP_DIR = "metadata/backups"

    def execute(
        self,
        note_path: str,
        reason: str = "完成",
        dry_run: bool = False,
        check_backlinks: bool = True,
        confirm: bool = True
    ) -> WorkflowResult:
        """归档笔记。

        Args:
            note_path: 要归档的笔记路径
            reason: 归档原因
            dry_run: 是否只预览不执行
            check_backlinks: 是否检查反向链接
            confirm: 是否需要确认

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

        # 2. 检查反向链接
        backlinks = []
        if check_backlinks:
            backlinks = self.find_backlinks(note_path)

        # 3. 确定归档目标路径
        today = date.today()
        archive_dir = self.vault.path / self.ARCHIVE_DIR / today.strftime("%Y-%m")
        archive_dir.mkdir(parents=True, exist_ok=True)

        dest_file = archive_dir / source_file.name

        # 处理文件名冲突
        counter = 1
        while dest_file.exists():
            stem = source_file.stem
            suffix = source_file.suffix
            dest_file = archive_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        archived_path = str(dest_file.relative_to(self.vault.path))

        # 4. 生成预览
        preview = self.preview_changes(note_path, archived_path, backlinks)

        # 5. 如果是 dry-run，只返回预览
        if dry_run:
            return WorkflowResult(
                success=True,
                message="📋 归档预览 (Dry-run)",
                suggestions=[
                    f"移动: {note_path} → {archived_path}",
                    f"需更新反向链接: {len(backlinks)} 个文件"
                ],
                data={
                    "preview": preview,
                    "dry_run": True
                }
            )

        # 6. 创建备份
        self._create_backup(note_path, content)

        # 7. 更新 frontmatter
        updated_content = self._update_status(content, "已归档", reason)

        # 8. 移动笔记
        try:
            dest_file.write_text(updated_content, encoding="utf-8")
            source_file.unlink()
        except Exception as e:
            return WorkflowResult(
                success=False,
                message=f"移动笔记失败: {e}",
                suggestions=["检查目录权限"]
            )

        # 9. 更新反向链接
        updated_count = 0
        if backlinks:
            updated_count = self.update_links(note_path, archived_path)

        details = ArchiveDetails(
            original_path=note_path,
            archived_path=archived_path,
            archive_date=today.isoformat(),
            reason=reason,
            backlinks=backlinks
        )

        return WorkflowResult(
            success=True,
            message=f"✅ 笔记已归档: {note_path} → {archived_path}",
            created_files=[archived_path],
            modified_files=[bl.source_path for bl in backlinks],
            suggestions=[
                f"已更新 {updated_count} 处反向链接",
                "可以继续归档其他笔记"
            ],
            data={
                "archive": details
            }
        )

    def find_note(self, name: str) -> List[str]:
        """查找匹配的笔记。

        CLI: obsidian search query=<name>
        """
        try:
            result = subprocess.run(
                ["obsidian", "search", f"query={name}"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip().split('\n')
        except FileNotFoundError:
            # CLI 不可用，使用本地搜索
            pass

        # 本地搜索作为后备
        results = []
        for md_file in self.vault.path.rglob("*.md"):
            if name.lower() in md_file.stem.lower():
                results.append(str(md_file.relative_to(self.vault.path)))
        return results

    def find_backlinks(self, name: str) -> List[BacklinkInfo]:
        """查找反向链接。

        CLI: obsidian backlinks file=<name> format=json
        """
        try:
            result = subprocess.run(
                ["obsidian", "backlinks", f"file={name}", "format=json"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout:
                try:
                    data = json.loads(result.stdout)
                    return [
                        BacklinkInfo(
                            source_path=item.get('file', item.get('source', '')),
                            link_text=item.get('link', ''),
                            needs_update=True
                        )
                        for item in data
                    ]
                except json.JSONDecodeError:
                    pass
        except FileNotFoundError:
            pass

        # 本地搜索作为后备
        return self._local_find_backlinks(name)

    def _local_find_backlinks(self, name: str) -> List[BacklinkInfo]:
        """本地查找反向链接。"""
        note_name = Path(name).stem
        backlinks = []

        for md_file in self.vault.path.rglob("*.md"):
            if str(md_file.relative_to(self.vault.path)) == name:
                continue

            try:
                content = md_file.read_text(encoding="utf-8")
                # 查找 [[note_name]] 或 [[note_name|alias]]
                pattern = rf'\[\[{re.escape(note_name)}(\|[^\]]+)?\]\]'
                if re.search(pattern, content):
                    backlinks.append(BacklinkInfo(
                        source_path=str(md_file.relative_to(self.vault.path)),
                        link_text=note_name,
                        needs_update=True
                    ))
            except Exception:
                continue

        return backlinks

    def move_note(self, name: str, to_folder: str) -> bool:
        """移动笔记。

        CLI: obsidian move file=<name> to=<path>
        """
        try:
            result = subprocess.run(
                ["obsidian", "move", f"file={name}", f"to={to_folder}"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            # 本地移动
            return self._local_move_note(name, to_folder)

    def _local_move_note(self, name: str, to_folder: str) -> bool:
        """本地移动笔记。"""
        try:
            src = self.vault.path / name
            if not src.exists():
                return False

            dest_dir = self.vault.path / to_folder
            dest_dir.mkdir(parents=True, exist_ok=True)

            dest = dest_dir / src.name
            src.rename(dest)
            return True
        except Exception:
            return False

    def update_status(self, name: str, status: str = "已归档") -> bool:
        """更新状态属性。

        CLI: obsidian property:set name=status value=<status> file=<name>
        """
        try:
            result = subprocess.run(
                ["obsidian", "property:set", "name=status", f"value={status}", f"file={name}"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def preview_changes(
        self,
        note_path: str,
        target_path: str,
        backlinks: List[BacklinkInfo]
    ) -> ArchivePreview:
        """预览归档变更（Dry-run）。"""
        link_updates = []
        for bl in backlinks:
            link_updates.append({
                "source_file": bl.source_path,
                "old_link": f"[[{bl.link_text}]]",
                "new_link": f"[[{target_path}|{bl.link_text}]]"
            })

        return ArchivePreview(
            note_path=note_path,
            target_path=target_path,
            backlinks=backlinks,
            link_updates=link_updates
        )

    def update_links(self, old_name: str, new_path: str) -> int:
        """更新所有引用该笔记的链接。返回更新数量。

        使用直接文件操作，不依赖 CLI（CLI 没有原地替换能力）。

        流程：
        1. CLI: obsidian backlinks file=<name> format=json 获取源文件列表
        2. Python: 直接读取源文件（不通过 CLI）
        3. Python: 正则替换 [[old_name]] → [[new_path|old_name]]
        4. Python: 直接写回文件
        """
        backlinks = self.find_backlinks(old_name)
        updated = 0

        # 提取旧名称（用于链接匹配）
        old_note_name = Path(old_name).stem

        for bl in backlinks:
            # 直接读取文件（不通过 CLI）
            file_path = self.vault.path / bl.source_path
            if not file_path.exists():
                continue

            try:
                content = file_path.read_text(encoding='utf-8')

                # 替换链接（支持 [[name]] 和 [[name|alias]] 两种形式）
                pattern = rf'\[\[{re.escape(old_note_name)}(\|[^\]]+)?\]\]'

                def replacer(m):
                    alias_part = m.group(1) or f"|{old_note_name}"
                    return f'[[{new_path}{alias_part}]]'

                new_content, count = re.subn(pattern, replacer, content)

                if count > 0:
                    # 备份原文件
                    backup_path = self._create_backup(bl.source_path, content)

                    # 写回新内容
                    file_path.write_text(new_content, encoding='utf-8')
                    updated += count
            except Exception:
                continue

        # 刷新 Obsidian 索引
        if updated > 0:
            self._reload_index()

        return updated

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

    def _create_backup(self, relative_path: str, content: str) -> Path:
        """创建备份文件。"""
        backup_dir = self.vault.path / self.BACKUP_DIR
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{relative_path.replace('/', '_')}.{timestamp}.bak"
        backup_path = backup_dir / backup_name

        backup_path.write_text(content, encoding='utf-8')
        return backup_path

    def _reload_index(self) -> bool:
        """刷新 Obsidian 索引。

        CLI: obsidian reload
        """
        try:
            result = subprocess.run(
                ["obsidian", "reload"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

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
            result = self.execute(path, reason, dry_run=False, confirm=False)
            if result.success:
                archived.append(path)
            else:
                failed.append({
                    "path": path,
                    "error": result.message
                })

        archived_paths = []
        for p in archived:
            # 重新执行获取归档路径
            result = self.execute(p, reason, dry_run=True, confirm=False)
            if result.success and result.data.get("preview"):
                archived_paths.append(result.data["preview"].target_path)

        if failed:
            return WorkflowResult(
                success=len(archived) > 0,
                message=f"归档完成: {len(archived)} 成功, {len(failed)} 失败",
                created_files=archived_paths,
                data={
                    "archived": archived,
                    "failed": failed
                }
            )

        return WorkflowResult(
            success=True,
            message=f"✅ 批量归档完成: {len(archived)} 个笔记",
            created_files=archived_paths,
            data={
                "archived": archived
            }
        )