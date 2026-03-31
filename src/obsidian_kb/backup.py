"""备份与恢复模块.

提供操作前自动备份和恢复功能。
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import shutil
import zipfile


@dataclass
class BackupRecord:
    """备份记录。"""
    backup_id: str
    timestamp: str
    operation: str
    files: List[str]
    backup_path: str
    status: str = "success"


class BackupManager:
    """备份管理器。

    管理操作前备份和恢复。

    备份目录结构:
    metadata/backups/
    ├── 2026-03-31/
    │   ├── 10_项目/
    │   │   └── 编程/
    │   │       └── 项目笔记.md.bak
    │   └── archive/
    │       └── 旧项目.md.bak
    └── backup-log.json
    """

    BACKUP_DIR = "metadata/backups"
    LOG_FILE = "backup-log.json"

    def __init__(self, vault_path: Path):
        """初始化备份管理器。

        Args:
            vault_path: Vault 根目录
        """
        self.vault_path = vault_path
        self.backup_dir = vault_path / self.BACKUP_DIR
        self.log_file = self.backup_dir / self.LOG_FILE

        # 确保备份目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(
        self,
        files: List[str],
        operation: str = "unknown"
    ) -> BackupRecord:
        """创建备份。

        Args:
            files: 要备份的文件路径列表
            operation: 操作类型

        Returns:
            备份记录
        """
        timestamp = datetime.now()
        backup_id = f"bk-{timestamp.strftime('%Y%m%d-%H%M%S')}"
        date_dir = timestamp.strftime("%Y-%m-%d")

        # 创建日期目录
        date_backup_dir = self.backup_dir / date_dir
        date_backup_dir.mkdir(parents=True, exist_ok=True)

        backed_up_files = []

        for file_path in files:
            source_file = self.vault_path / file_path

            if not source_file.exists():
                continue

            # 保持相对路径结构
            relative_dir = source_file.parent.relative_to(self.vault_path)
            backup_subdir = date_backup_dir / relative_dir
            backup_subdir.mkdir(parents=True, exist_ok=True)

            # 备份文件
            backup_file = backup_subdir / f"{source_file.name}.bak"
            try:
                shutil.copy2(source_file, backup_file)
                backed_up_files.append(file_path)
            except Exception:
                continue

        # 创建备份记录
        record = BackupRecord(
            backup_id=backup_id,
            timestamp=timestamp.isoformat(),
            operation=operation,
            files=backed_up_files,
            backup_path=str(date_backup_dir.relative_to(self.vault_path)),
            status="success" if backed_up_files else "failed"
        )

        # 记录到日志
        self._append_log(record)

        return record

    def create_batch_backup(
        self,
        files: List[str],
        operation: str = "batch"
    ) -> BackupRecord:
        """创建批量备份（打包）。

        Args:
            files: 文件列表
            operation: 操作类型

        Returns:
            备份记录
        """
        timestamp = datetime.now()
        backup_id = f"bk-{timestamp.strftime('%Y%m%d-%H%M%S')}"

        # 创建 zip 文件
        date_dir = timestamp.strftime("%Y-%m-%d")
        date_backup_dir = self.backup_dir / date_dir
        date_backup_dir.mkdir(parents=True, exist_ok=True)

        zip_path = date_backup_dir / f"{backup_id}.zip"

        backed_up_files = []

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in files:
                    source_file = self.vault_path / file_path
                    if source_file.exists():
                        zf.write(source_file, file_path)
                        backed_up_files.append(file_path)
        except Exception:
            pass

        record = BackupRecord(
            backup_id=backup_id,
            timestamp=timestamp.isoformat(),
            operation=operation,
            files=backed_up_files,
            backup_path=str(zip_path.relative_to(self.vault_path)),
            status="success" if backed_up_files else "failed"
        )

        self._append_log(record)

        return record

    def restore_backup(self, backup_id: str) -> bool:
        """恢复备份。

        Args:
            backup_id: 备份 ID

        Returns:
            是否成功
        """
        record = self.get_backup_record(backup_id)

        if not record:
            return False

        success = True

        for file_path in record.files:
            # 查找备份文件
            backup_file = self._find_backup_file(backup_id, file_path)

            if not backup_file or not backup_file.exists():
                success = False
                continue

            # 恢复文件
            target_file = self.vault_path / file_path
            try:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_file, target_file)
            except Exception:
                success = False

        return success

    def get_backup_record(self, backup_id: str) -> Optional[BackupRecord]:
        """获取备份记录。

        Args:
            backup_id: 备份 ID

        Returns:
            备份记录
        """
        logs = self._load_logs()

        for log in logs:
            if log.get("backup_id") == backup_id:
                return BackupRecord(**log)

        return None

    def list_backups(
        self,
        limit: int = 20,
        operation: str = None
    ) -> List[BackupRecord]:
        """列出备份。

        Args:
            limit: 最大数量
            operation: 过滤操作类型

        Returns:
            备份记录列表
        """
        logs = self._load_logs()

        if operation:
            logs = [l for l in logs if l.get("operation") == operation]

        # 按时间倒序
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return [BackupRecord(**l) for l in logs[:limit]]

    def cleanup_old_backups(self, days: int = 30) -> int:
        """清理旧备份。

        Args:
            days: 保留天数

        Returns:
            清理的备份数量
        """
        import time

        threshold = time.time() - (days * 24 * 60 * 60)
        cleaned = 0

        for date_dir in self.backup_dir.iterdir():
            if not date_dir.is_dir():
                continue

            # 检查日期目录
            try:
                dir_time = datetime.strptime(date_dir.name, "%Y-%m-%d").timestamp()
                if dir_time < threshold:
                    shutil.rmtree(date_dir)
                    cleaned += 1
            except ValueError:
                continue

        return cleaned

    def _find_backup_file(self, backup_id: str, original_path: str) -> Optional[Path]:
        """查找备份文件。

        Args:
            backup_id: 备份 ID
            original_path: 原始文件路径

        Returns:
            备份文件路径
        """
        # 从 backup_id 提取日期
        try:
            date_str = backup_id.split("-")[1]
            # 格式: YYYYMMDD -> YYYY-MM-DD
            date_dir = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        except (IndexError, ValueError):
            return None

        # 构建备份路径
        original_file = Path(original_path)
        backup_path = self.backup_dir / date_dir / original_path

        backup_file = backup_path.with_suffix(original_file.suffix + ".bak")

        if backup_file.exists():
            return backup_file

        # 也检查 zip 文件
        zip_file = self.backup_dir / date_dir / f"{backup_id}.zip"
        if zip_file.exists():
            return zip_file

        return None

    def _load_logs(self) -> List[Dict[str, Any]]:
        """加载备份日志。"""
        if not self.log_file.exists():
            return []

        try:
            content = self.log_file.read_text(encoding="utf-8")
            data = json.loads(content)
            return data.get("backups", [])
        except Exception:
            return []

    def _append_log(self, record: BackupRecord) -> None:
        """追加备份日志。"""
        logs = self._load_logs()

        logs.append({
            "backup_id": record.backup_id,
            "timestamp": record.timestamp,
            "operation": record.operation,
            "files": record.files,
            "backup_path": record.backup_path,
            "status": record.status
        })

        try:
            self.log_file.write_text(
                json.dumps({"backups": logs}, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass


class RestoreWorkflow:
    """恢复工作流。

    提供交互式恢复功能。
    """

    def __init__(self, backup_manager: BackupManager, vault_path: Path):
        """初始化恢复工作流。

        Args:
            backup_manager: 备份管理器
            vault_path: Vault 路径
        """
        self.backup_manager = backup_manager
        self.vault_path = vault_path

    def list_restorable_operations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """列出可恢复的操作。

        Args:
            limit: 最大数量

        Returns:
            可恢复操作列表
        """
        backups = self.backup_manager.list_backups(limit=limit)

        return [
            {
                "id": b.backup_id,
                "timestamp": b.timestamp,
                "operation": b.operation,
                "files_count": len(b.files),
                "status": b.status
            }
            for b in backups if b.status == "success"
        ]

    def restore(self, backup_id: str) -> Dict[str, Any]:
        """执行恢复。

        Args:
            backup_id: 备份 ID

        Returns:
            恢复结果
        """
        record = self.backup_manager.get_backup_record(backup_id)

        if not record:
            return {
                "success": False,
                "message": f"备份不存在: {backup_id}"
            }

        success = self.backup_manager.restore_backup(backup_id)

        if success:
            return {
                "success": True,
                "message": f"已恢复 {len(record.files)} 个文件",
                "restored_files": record.files
            }
        else:
            return {
                "success": False,
                "message": "恢复失败，部分文件可能未找到"
            }