"""链接解析器模块.

处理 Obsidian wiki link 的解析、查找和更新。
使用 Obsidian CLI 进行链接关系查询。
"""
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class LinkInfo:
    """链接信息数据类.

    Attributes:
        source: 链接来源笔记路径
        target: 链接目标笔记路径
        link_text: 链接文本（不含 [[]]）
        is_embed: 是否是嵌入链接（![[...]]）
    """

    source: str
    target: str
    link_text: str
    is_embed: bool = False

    def __str__(self) -> str:
        """返回链接的字符串表示。"""
        return f"[[{self.link_text}]] -> {self.target} (from {self.source})"


class LinkResolver:
    """Obsidian wiki link 解析器.

    提供以下功能：
    - 解析 wiki link 到文件路径
    - 获取反向链接（backlinks）
    - 提取笔记中的所有链接
    - 更新笔记中的链接
    - 查找死链（broken links）
    - 查找孤儿笔记（orphans）

    Attributes:
        vault_path: Obsidian Vault 的绝对路径
    """

    # Wiki link 正则表达式
    WIKI_LINK_PATTERN = r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]"
    # 嵌入链接正则表达式（图片、文件等）
    EMBED_LINK_PATTERN = r"!\[\[([^\]|]+)(?:\|[^\]]+)?\]\]"

    def __init__(self, vault_path: Path):
        """初始化链接解析器.

        Args:
            vault_path: Vault 的绝对路径

        Raises:
            ValueError: 路径不存在或不是目录
        """
        if not vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")
        if not vault_path.is_dir():
            raise ValueError(f"Vault path must be a directory: {vault_path}")

        self.vault_path = vault_path

    def resolve(self, link_text: str) -> Optional[Path]:
        """解析 wiki link 到文件路径.

        支持以下格式：
        - [[Note Name]] -> 简单链接
        - [[Note Name|Alias]] -> 带别名链接
        - [[folder/Note Name]] -> 嵌套路径链接

        Args:
            link_text: 链接文本（可能包含别名）

        Returns:
            找到的文件路径，如果未找到则返回 None
        """
        # 去除别名部分（如果有）
        # 格式: Note Name|Alias -> Note Name
        if "|" in link_text:
            link_text = link_text.split("|")[0].strip()

        # 去除可能的前缀符号（如 ![[...]] 中的 !）
        link_text = link_text.lstrip("!")

        # 尝试多种匹配方式
        search_patterns = [
            # 精确匹配（文件名）
            f"{link_text}.md",
            # 去除空格的匹配
            f"{link_text.replace(' ', '')}.md",
        ]

        # 搜索所有 .md 文件
        for md_file in self.vault_path.rglob("*.md"):
            file_name = md_file.stem

            # 精确匹配
            if file_name == link_text:
                return md_file

            # 去除空格匹配
            if file_name.replace(" ", "") == link_text.replace(" ", ""):
                return md_file

            # 大小写不敏感匹配
            if file_name.lower() == link_text.lower():
                return md_file

        # 尝试作为相对路径解析
        if "/" in link_text:
            potential_path = self.vault_path / f"{link_text}.md"
            if potential_path.exists():
                return potential_path

        return None

    def get_backlinks(self, note_path: str) -> List[Dict[str, Any]]:
        """获取笔记的反向链接.

        使用 `obsidian backlinks` CLI 命令查询，
        如果 CLI 不可用则使用本地搜索。

        Args:
            note_path: 目标笔记路径

        Returns:
            反向链接列表，每个元素包含 file 等信息
        """
        try:
            result = subprocess.run(
                ["obsidian", "backlinks", note_path, "--vault", str(self.vault_path)],
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
        """本地查找反向链接。

        Args:
            note_path: 目标笔记路径

        Returns:
            反向链接列表
        """
        # 提取笔记名称（用于匹配 [[]] 链接）
        note_name = Path(note_path).stem
        link_pattern = f"[[{note_name}]"

        backlinks = []

        for md_file in self.vault_path.rglob("*.md"):
            if str(md_file.relative_to(self.vault_path)) == note_path:
                continue

            try:
                content = md_file.read_text(encoding="utf-8")
                if link_pattern in content:
                    rel_path = str(md_file.relative_to(self.vault_path))
                    backlinks.append({
                        "file": rel_path,
                        "link": f"[[{note_name}]]"
                    })
            except Exception:
                continue

        return backlinks

    def extract_links(self, content: str) -> List[str]:
        """从内容中提取所有 wiki link.

        提取 [[]] 格式的链接，返回链接文本列表。
        不包含嵌入链接（![[...]]）。

        Args:
            content: 笔记内容

        Returns:
            链接文本列表（不含 [[]] 包裹）
        """
        links = []

        # 匹配普通 wiki link
        matches = re.findall(self.WIKI_LINK_PATTERN, content)

        for match in matches:
            # 去除别名部分
            link_text = match.strip()
            if "|" in link_text:
                link_text = link_text.split("|")[0].strip()
            links.append(link_text)

        return links

    def extract_all_links(self, content: str) -> List[LinkInfo]:
        """从内容中提取所有链接信息（包括嵌入链接）.

        Args:
            content: 笔记内容

        Returns:
            LinkInfo 对象列表
        """
        links = []

        # 提取普通链接
        for match in re.finditer(self.WIKI_LINK_PATTERN, content):
            link_text = match.group(1).strip()
            if "|" in link_text:
                link_text = link_text.split("|")[0].strip()
            links.append(LinkInfo(
                source="",
                target=link_text,
                link_text=match.group(1).strip(),
                is_embed=False
            ))

        # 提取嵌入链接
        for match in re.finditer(self.EMBED_LINK_PATTERN, content):
            link_text = match.group(1).strip()
            if "|" in link_text:
                link_text = link_text.split("|")[0].strip()
            links.append(LinkInfo(
                source="",
                target=link_text,
                link_text=match.group(1).strip(),
                is_embed=True
            ))

        return links

    def update_link(self, content: str, old: str, new: str) -> str:
        """更新内容中的链接.

        将所有 [[old]] 替换为 [[new]]，
        保留原有的别名部分（如 [[old|alias]] -> [[new|alias]]）。

        Args:
            content: 原始内容
            old: 旧链接文本
            new: 新链接文本

        Returns:
            更新后的内容
        """
        # 替换简单链接 [[old]] -> [[new]]
        content = re.sub(
            rf"\[\[{re.escape(old)}\]\]",
            f"[[{new}]]",
            content
        )

        # 替换带别名的链接 [[old|alias]] -> [[new|alias]]
        content = re.sub(
            rf"\[\[{re.escape(old)}\|([^\]]+)\]\]",
            f"[[{new}|\\1]]",
            content
        )

        return content

    def find_broken_links(self) -> List[Dict[str, Any]]:
        """查找死链（链接到不存在的笔记）.

        使用 `obsidian unresolved` CLI 命令查询，
        如果 CLI 不可用则使用本地检测。

        Returns:
            死链列表，每个元素包含 link, file 等信息
        """
        try:
            result = subprocess.run(
                ["obsidian", "unresolved", "--vault", str(self.vault_path)],
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
            # obsidian CLI 未安装，使用本地检测
            return self._local_broken_links()

        return []

    def _local_broken_links(self) -> List[Dict[str, Any]]:
        """本地检测死链。

        Returns:
            死链列表
        """
        broken = []

        for md_file in self.vault_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                links = self.extract_links(content)

                for link in links:
                    if self.resolve(link) is None:
                        rel_path = str(md_file.relative_to(self.vault_path))
                        broken.append({
                            "link": f"[[{link}]]",
                            "file": rel_path,
                            "target": link
                        })
            except Exception:
                continue

        return broken

    def find_orphans(self) -> List[Dict[str, Any]]:
        """查找孤儿笔记（没有任何反向链接的笔记）.

        使用 `obsidian orphans` CLI 命令查询，
        如果 CLI 不可用则使用本地检测。

        Returns:
            孤儿笔记列表，每个元素包含 file 等信息
        """
        try:
            result = subprocess.run(
                ["obsidian", "orphans", "--vault", str(self.vault_path)],
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
            # obsidian CLI 未安装，使用本地检测
            return self._local_orphans()

        return []

    def _local_orphans(self) -> List[Dict[str, Any]]:
        """本地检测孤儿笔记。

        Returns:
            孤儿笔记列表
        """
        # 收集所有被链接的笔记
        linked_notes = set()

        for md_file in self.vault_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                links = self.extract_links(content)

                for link in links:
                    target_path = self.resolve(link)
                    if target_path:
                        linked_notes.add(str(target_path.relative_to(self.vault_path)))
            except Exception:
                continue

        # 找出没有被链接的笔记
        orphans = []

        for md_file in self.vault_path.rglob("*.md"):
            rel_path = str(md_file.relative_to(self.vault_path))

            # 排除模板目录
            if "99_模板" in rel_path:
                continue

            if rel_path not in linked_notes:
                orphans.append({
                    "file": rel_path,
                    "title": md_file.stem
                })

        return orphans

    def get_outgoing_links(self, note_path: str) -> List[LinkInfo]:
        """获取笔记的所有出链。

        Args:
            note_path: 笔记路径

        Returns:
            LinkInfo 对象列表
        """
        full_path = self.vault_path / note_path

        if not full_path.exists():
            raise FileNotFoundError(f"Note not found: {note_path}")

        content = full_path.read_text(encoding="utf-8")
        links = self.extract_all_links(content)

        # 设置 source
        result = []
        for link in links:
            result.append(LinkInfo(
                source=note_path,
                target=link.target,
                link_text=link.link_text,
                is_embed=link.is_embed
            ))

        return result

    def check_link_exists(self, link_text: str) -> bool:
        """检查链接目标是否存在。

        Args:
            link_text: 链接文本

        Returns:
            是否存在
        """
        return self.resolve(link_text) is not None

    def suggest_link_target(self, link_text: str) -> List[Path]:
        """建议可能的链接目标（模糊匹配）。

        Args:
            link_text: 链接文本

        Returns:
            可能匹配的文件路径列表
        """
        suggestions = []
        link_lower = link_text.lower()

        for md_file in self.vault_path.rglob("*.md"):
            file_name = md_file.stem
            file_lower = file_name.lower()

            # 包含匹配
            if link_lower in file_lower or file_lower in link_lower:
                suggestions.append(md_file)

        return suggestions