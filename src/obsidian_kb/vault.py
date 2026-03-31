"""Vault 操作封装模块.

封装 Obsidian CLI 进行文件操作，提供统一的 Vault 访问接口。
"""
import json
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class NoteInfo:
    """笔记基本信息."""

    path: str
    title: str
    modified_time: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.title} ({self.path})"


@dataclass
class NoteContent:
    """笔记完整内容."""

    path: str
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    body: str = ""

    def __str__(self) -> str:
        return f"Note: {self.path}"


class Vault:
    """Obsidian Vault 操作封装.

    提供对 Obsidian Vault 的文件操作接口，包括：
    - 列出笔记
    - 读取/创建笔记
    - 搜索笔记
    - 获取链接关系
    - 移动笔记
    - 目录管理

    Attributes:
        path: Vault 的绝对路径
        inbox_path: 收件箱路径 (00_收件箱)
        projects_path: 项目路径 (10_项目)
        areas_path: 领域路径 (20_领域)
        research_path: 研究路径 (30_研究)
        knowledge_path: 知识库路径 (40_知识库)
        archive_path: 归档路径 (50_归档)
        templates_path: 模板路径 (99_模板)
        daily_path: 每日笔记路径 (Daily)
    """

    # PARA 目录名常量
    INBOX_DIR = "00_收件箱"
    PROJECTS_DIR = "10_项目"
    AREAS_DIR = "20_领域"
    RESEARCH_DIR = "30_研究"
    KNOWLEDGE_DIR = "40_知识库"
    ARCHIVE_DIR = "50_归档"
    TEMPLATE_DIR = "99_模板"
    DAILY_DIR = "Daily"

    def __init__(self, path: Path):
        """初始化 Vault 实例.

        Args:
            path: Vault 的绝对路径

        Raises:
            ValueError: 路径不存在或不是目录
        """
        if not path.exists():
            raise ValueError(f"Vault path does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Vault path must be a directory: {path}")

        self.path = path

        # 设置 PARA 目录路径属性
        self.inbox_path = path / self.INBOX_DIR
        self.projects_path = path / self.PROJECTS_DIR
        self.areas_path = path / self.AREAS_DIR
        self.research_path = path / self.RESEARCH_DIR
        self.knowledge_path = path / self.KNOWLEDGE_DIR
        self.archive_path = path / self.ARCHIVE_DIR
        self.templates_path = path / self.TEMPLATE_DIR
        self.daily_path = path / self.DAILY_DIR

    def _resolve_path(self, rel_path: str) -> Path:
        """解析相对路径为绝对路径.

        Args:
            rel_path: 相对于 Vault 的路径

        Returns:
            绝对路径
        """
        return self.path / rel_path

    def list_inbox(self) -> List[NoteInfo]:
        """列出收件箱中的笔记.

        Returns:
            收件箱笔记列表
        """
        return self._list_notes_in_dir(self.inbox_path)

    def list_projects(self) -> List[NoteInfo]:
        """列出活跃项目目录中的笔记.

        Returns:
            项目笔记列表
        """
        return self._list_notes_in_dir(self.projects_path, recursive=True)

    def list_knowledge(self) -> List[NoteInfo]:
        """列出知识库中的笔记.

        Returns:
            知识库笔记列表
        """
        return self._list_notes_in_dir(self.knowledge_path, recursive=True)

    def _list_notes_in_dir(
        self,
        dir_path: Path,
        recursive: bool = False
    ) -> List[NoteInfo]:
        """列出目录中的所有 Markdown 笔记.

        Args:
            dir_path: 目录路径
            recursive: 是否递归搜索子目录

        Returns:
            笔记信息列表
        """
        notes = []

        if not dir_path.exists():
            return notes

        # 获取所有 .md 文件
        if recursive:
            md_files = list(dir_path.rglob("*.md"))
        else:
            md_files = list(dir_path.glob("*.md"))

        for md_file in md_files:
            # 获取相对路径
            rel_path = str(md_file.relative_to(self.path))

            # 尝试从文件提取标题
            title = self._extract_title(md_file)

            # 获取修改时间
            modified_time = datetime.fromtimestamp(
                md_file.stat().st_mtime
            ).strftime("%Y-%m-%d %H:%M")

            notes.append(NoteInfo(
                path=rel_path,
                title=title,
                modified_time=modified_time
            ))

        return notes

    def _extract_title(self, file_path: Path) -> str:
        """从笔记文件提取标题.

        优先级：
        1. Frontmatter 中的 title
        2. 第一个 # 标题
        3. 文件名（去除扩展名）

        Args:
            file_path: 笔记文件路径

        Returns:
            标题字符串
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # 尝试从 frontmatter 提取
            if content.startswith("---"):
                # 查找第二个 ---
                second_marker = content.find("\n---", 3)
                if second_marker != -1:
                    yaml_content = content[4:second_marker].strip()
                    import yaml
                    try:
                        data = yaml.safe_load(yaml_content)
                        if isinstance(data, dict) and "title" in data:
                            return str(data["title"])
                    except yaml.YAMLError:
                        pass

            # 尝试从第一个标题提取
            for line in content.split("\n"):
                if line.startswith("# "):
                    return line[2:].strip()

        except Exception:
            pass

        # 默认使用文件名
        return file_path.stem

    def read_note(self, path: str) -> str:
        """读取笔记内容.

        Args:
            path: 相对于 Vault 的路径

        Returns:
            笔记完整内容（包含 frontmatter）

        Raises:
            FileNotFoundError: 笔记不存在
        """
        full_path = self._resolve_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"Note not found: {path}")

        return full_path.read_text(encoding="utf-8")

    def read_note_parsed(self, path: str) -> NoteContent:
        """读取并解析笔记内容.

        Args:
            path: 相对于 Vault 的路径

        Returns:
            NoteContent 实例（包含解析后的 frontmatter 和正文）

        Raises:
            FileNotFoundError: 笔记不存在
        """
        content = self.read_note(path)
        frontmatter = {}
        body = content

        # 解析 frontmatter
        if content.startswith("---"):
            second_marker = content.find("\n---", 3)
            if second_marker != -1:
                yaml_content = content[4:second_marker].strip()
                import yaml
                try:
                    data = yaml.safe_load(yaml_content)
                    if isinstance(data, dict):
                        frontmatter = data
                    body = content[second_marker + 4:].strip()
                except yaml.YAMLError:
                    pass

        return NoteContent(
            path=path,
            frontmatter=frontmatter,
            body=body
        )

    def create_note(self, path: str, content: str) -> Path:
        """创建新笔记.

        Args:
            path: 相对于 Vault 的路径
            content: 笔记内容

        Returns:
            创建的笔记文件的绝对路径

        Raises:
            ValueError: 笔记已存在
        """
        full_path = self._resolve_path(path)

        # 确保父目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # 检查文件是否已存在
        if full_path.exists():
            raise ValueError(f"Note already exists: {path}")

        # 写入内容
        full_path.write_text(content, encoding="utf-8")

        return full_path

    def update_note(self, path: str, content: str) -> Path:
        """更新现有笔记.

        Args:
            path: 相对于 Vault 的路径
            content: 新的笔记内容

        Returns:
            更新的笔记文件的绝对路径

        Raises:
            FileNotFoundError: 笔记不存在
        """
        full_path = self._resolve_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"Note not found: {path}")

        full_path.write_text(content, encoding="utf-8")

        return full_path

    def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索笔记.

        使用 obsidian CLI 的搜索功能。

        Args:
            query: 搜索关键词

        Returns:
            搜索结果列表，每个结果包含 path, title 等信息
        """
        try:
            result = subprocess.run(
                ["obsidian", "search", query, "--vault", str(self.path)],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0 and result.stdout:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return []

        except FileNotFoundError:
            # obsidian CLI 未安装，使用本地搜索
            return self._local_search(query)

        return []

    def _local_search(self, query: str) -> List[Dict[str, Any]]:
        """本地搜索笔记（当 obsidian CLI 不可用时）.

        Args:
            query: 搜索关键词

        Returns:
            搜索结果列表
        """
        results = []

        for md_file in self.path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                if query.lower() in content.lower():
                    rel_path = str(md_file.relative_to(self.path))
                    results.append({
                        "path": rel_path,
                        "title": self._extract_title(md_file)
                    })
            except Exception:
                continue

        return results

    def get_backlinks(self, note_path: str) -> List[Dict[str, Any]]:
        """获取笔记的反向链接.

        Args:
            note_path: 目标笔记路径

        Returns:
            反向链接列表，每个链接包含 source, link 等信息
        """
        try:
            result = subprocess.run(
                ["obsidian", "backlinks", note_path, "--vault", str(self.path)],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0 and result.stdout:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return []

        except FileNotFoundError:
            # obsidian CLI 未安装，使用本地搜索
            return self._local_backlinks(note_path)

        return []

    def _local_backlinks(self, note_path: str) -> List[Dict[str, Any]]:
        """本地查找反向链接.

        Args:
            note_path: 目标笔记路径

        Returns:
            反向链接列表
        """
        # 提取笔记名称（用于匹配 [[]] 链接）
        note_name = Path(note_path).stem
        link_pattern = f"[[{note_name}]"

        backlinks = []

        for md_file in self.path.rglob("*.md"):
            if str(md_file.relative_to(self.path)) == note_path:
                continue

            try:
                content = md_file.read_text(encoding="utf-8")
                if link_pattern in content:
                    rel_path = str(md_file.relative_to(self.path))
                    backlinks.append({
                        "source": rel_path,
                        "link": f"[[{note_name}]]"
                    })
            except Exception:
                continue

        return backlinks

    def get_links(self, note_path: str) -> List[Dict[str, Any]]:
        """获取笔记的出链（正向链接）.

        Args:
            note_path: 笔记路径

        Returns:
            出链列表
        """
        content = self.read_note(note_path)
        links = []

        # 匹配 [[]] 格式的链接
        import re
        pattern = r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]"
        matches = re.findall(pattern, content)

        for match in matches:
            links.append({
                "target": match.strip(),
                "link": f"[[{match}]]"
            })

        return links

    def move_note(self, src: str, dst: str) -> Path:
        """移动/重命名笔记.

        Args:
            src: 源路径
            dst: 目标路径

        Returns:
            新笔记的绝对路径

        Raises:
            FileNotFoundError: 源笔记不存在
            ValueError: 目标笔记已存在
        """
        src_path = self._resolve_path(src)
        dst_path = self._resolve_path(dst)

        if not src_path.exists():
            raise FileNotFoundError(f"Source note not found: {src}")

        if dst_path.exists():
            raise ValueError(f"Target already exists: {dst}")

        # 确保目标目录存在
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        # 移动文件
        shutil.move(str(src_path), str(dst_path))

        return dst_path

    def delete_note(self, path: str) -> bool:
        """删除笔记.

        Args:
            path: 笔记路径

        Returns:
            是否成功删除

        Raises:
            FileNotFoundError: 笔记不存在
        """
        full_path = self._resolve_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"Note not found: {path}")

        full_path.unlink()
        return True

    def ensure_directory(self, path: str) -> Path:
        """确保目录存在，不存在则创建.

        Args:
            path: 相对于 Vault 的目录路径

        Returns:
            目录的绝对路径
        """
        full_path = self._resolve_path(path)
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path

    def exists(self, path: str) -> bool:
        """检查笔记或目录是否存在.

        Args:
            path: 相对于 Vault 的路径

        Returns:
            是否存在
        """
        return self._resolve_path(path).exists()

    def get_all_notes(self) -> List[NoteInfo]:
        """获取 Vault 中所有笔记.

        Returns:
            所有笔记列表
        """
        notes = []

        for md_file in self.path.rglob("*.md"):
            rel_path = str(md_file.relative_to(self.path))
            title = self._extract_title(md_file)
            modified_time = datetime.fromtimestamp(
                md_file.stat().st_mtime
            ).strftime("%Y-%m-%d %H:%M")

            notes.append(NoteInfo(
                path=rel_path,
                title=title,
                modified_time=modified_time
            ))

        return notes

    def get_notes_by_type(self, note_type: str) -> List[NoteInfo]:
        """按类型获取笔记.

        Args:
            note_type: 笔记类型 (project, research, knowledge, etc.)

        Returns:
            该类型的笔记列表
        """
        all_notes = self.get_all_notes()
        typed_notes = []

        for note in all_notes:
            try:
                content = self.read_note(note.path)
                # 检查 frontmatter 中的 type
                if content.startswith("---"):
                    second_marker = content.find("\n---", 3)
                    if second_marker != -1:
                        yaml_content = content[4:second_marker].strip()
                        import yaml
                        try:
                            data = yaml.safe_load(yaml_content)
                            if isinstance(data, dict) and data.get("type") == note_type:
                                typed_notes.append(note)
                        except yaml.YAMLError:
                            pass
            except Exception:
                continue

        return typed_notes