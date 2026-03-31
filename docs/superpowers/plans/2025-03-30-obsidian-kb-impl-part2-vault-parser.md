# Obsidian Knowledge Base 技能实施计划 - Part 2: Vault 操作层与解析器

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建 Vault 操作封装层和 Markdown 解析器，为上层工作流提供文件读写、链接解析和结构化数据输出能力。

**Architecture:** 采用混合操作模式 - CLI 用于查询和索引操作，直接文件操作用于内容修改。充分利用 Obsidian 的搜索索引能力，同时保持内容修改的精确控制。

**Tech Stack:** Python 3.8+, markdown-it-py (AST解析), pydantic (数据模型), subprocess (CLI调用)

---

## 混合操作模式

本技能采用混合操作模式，根据操作类型选择最优实现：

| 操作类型 | 实现方式 | CLI 命令/方法 | 原因 |
|---------|---------|--------------|------|
| **文件读取** | CLI | `obsidian read file=<name>` | 利用 Obsidian 的文件解析 |
| **文件创建** | CLI | `obsidian create name=<name>` | 触发 Obsidian 索引更新 |
| **文件移动** | CLI | `obsidian move file=<name> to=<path>` | 自动更新 Obsidian 内部引用 |
| **搜索/查询** | CLI | `obsidian search/backlinks/etc` | 利用 Obsidian 的搜索索引 |
| **链接查询** | CLI | `obsidian backlinks/links/orphans` | 利用 Obsidian 的链接索引 |
| **任务提取** | CLI | `obsidian tasks todo` | 利用 Obsidian 的任务解析 |
| **标签统计** | CLI | `obsidian tags counts` | 利用 Obsidian 的标签索引 |
| **链接更新** | 直接文件操作 | Python `file.read/write` | CLI 无原地替换能力 |
| **内容修改** | 直接文件操作 | Python `file.read/write` | 精确控制，避免覆盖风险 |
| **备份** | 直接文件操作 | Python `shutil.copy` | CLI 无备份功能 |

**关键原则**：
- 查询操作优先使用 CLI（利用索引）
- 修改操作使用直接文件操作（精确控制）
- 修改后可选择调用 `obsidian reload` 刷新索引

---

## 项目文件结构（本 Part 新增）

```
src/obsidian_kb/
├── vault.py              # Vault 文件操作封装（基于 CLI）
├── parser.py             # Markdown AST 解析器（纯 Python）
└── link_resolver.py      # 链接解析器（基于 CLI）
tests/
├── test_vault.py
├── test_parser.py
└── test_link_resolver.py
```

---

## Obsidian CLI 命令映射

本技能完全依赖 Obsidian CLI，以下是命令映射：

| 功能 | CLI 命令 | 用途 |
|------|---------|------|
| **文件读取** | `obsidian read file=<name>` | 读取笔记内容 |
| **文件创建** | `obsidian create name=<name> content=<text>` | 创建新笔记 |
| **文件移动** | `obsidian move file=<name> to=<path>` | 移动/重命名 |
| **文件删除** | `obsidian delete file=<name>` | 删除笔记 |
| **文件列表** | `obsidian files folder=<path>` | 列出文件夹内容 |
| **搜索** | `obsidian search query=<text>` | 搜索内容 |
| **反向链接** | `obsidian backlinks file=<name> format=json` | 查找入链 |
| **出链** | `obsidian links file=<name>` | 查找出链 |
| **死链** | `obsidian unresolved format=json` | 未解析的链接 |
| **孤儿笔记** | `obsidian orphans` | 无入链的文件 |
| **死胡同** | `obsidian deadends` | 无出链的文件 |
| **任务列表** | `obsidian tasks todo format=json` | 未完成任务 |
| **标签列表** | `obsidian tags format=json` | 所有标签 |
| **属性操作** | `obsidian property:set/read/remove` | Frontmatter 操作 |

---

## Task 2.1: Vault 操作封装（基于 CLI）

**Files:**
- Create: `src/obsidian_kb/vault.py`
- Create: `tests/test_vault.py`

### 核心接口设计

```python
from subprocess import run
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
import re
import shutil

@dataclass
class Note:
    """笔记数据模型。"""
    path: Path
    frontmatter: Frontmatter
    body: str
    links: List[str]      # 通过 CLI links 命令获取
    sections: List[Section]  # 通过 parser 解析
    tasks: List[TaskItem]    # 通过 CLI tasks 命令获取

@dataclass
class NoteMeta:
    """笔记元数据（轻量级）。"""
    path: Path
    title: str
    id: str
    type: str
    date: str
    modified: datetime


class Vault:
    """Obsidian Vault 操作封装（混合模式：CLI + 直接文件操作）。"""

    def __init__(self, path: Path):
        self.path = path
        self._cli_available = self._check_cli()

    def _check_cli(self) -> bool:
        """检查 CLI 是否可用。"""
        result = run(["obsidian", "version"], capture_output=True)
        return result.returncode == 0

    # ========== CLI 操作 ==========

    def read_note(self, name: str) -> str:
        """读取笔记内容（CLI）。
        
        CLI: obsidian read file=<name>
        """
        result = run(
            ["obsidian", "read", f"file={name}"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise FileNotFoundError(f"Note not found: {name}")
        return result.stdout

    def create_note(self, name: str, content: str, overwrite: bool = False) -> None:
        """创建笔记（CLI）。
        
        CLI: obsidian create name=<name> content=<content> [--overwrite]
        """
        args = ["obsidian", "create", f"name={name}", f"content={content}"]
        if overwrite:
            args.append("overwrite")
        run(args, check=True)

    def move_note(self, name: str, to_path: str) -> None:
        """移动/重命名笔记（CLI）。
        
        CLI: obsidian move file=<name> to=<path>
        """
        run(["obsidian", "move", f"file={name}", f"to={to_path}"], check=True)

    def delete_note(self, name: str, permanent: bool = False) -> None:
        """删除笔记（CLI）。
        
        CLI: obsidian delete file=<name> [--permanent]
        """
        args = ["obsidian", "delete", f"file={name}"]
        if permanent:
            args.append("permanent")
        run(args, check=True)

    def search(self, query: str, path: str = None) -> List[str]:
        """搜索内容（CLI）。"""
        args = ["obsidian", "search", f"query={query}"]
        if path:
            args.append(f"path={path}")
        result = run(args, capture_output=True, text=True)
        return result.stdout.strip().split('\n') if result.stdout else []

    # ========== 直接文件操作（用于精确修改） ==========

    def read_file_direct(self, relative_path: str) -> str:
        """直接读取文件（不通过 CLI）。
        
        用于需要精确修改内容的场景。
        """
        file_path = self.path / relative_path
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path.read_text(encoding='utf-8')

    def write_file_direct(self, relative_path: str, content: str) -> None:
        """直接写入文件（不通过 CLI）。
        
        用于精确修改内容的场景，如链接替换。
        """
        file_path = self.path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')

    def backup_file(self, relative_path: str) -> Path:
        """备份文件到 metadata/backups/。
        
        Returns:
            备份文件路径
        """
        src = self.path / relative_path
        backup_dir = self.path / "metadata" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{relative_path.replace('/', '_')}.{timestamp}.bak"
        backup_path = backup_dir / backup_name
        
        shutil.copy(src, backup_path)
        return backup_path

    def replace_in_file(self, relative_path: str, pattern: str, replacement: str) -> int:
        """在文件中替换内容。
        
        Args:
            relative_path: 相对于 Vault 的文件路径
            pattern: 正则表达式模式
            replacement: 替换字符串
        
        Returns:
            替换次数
        """
        content = self.read_file_direct(relative_path)
        new_content, count = re.subn(pattern, replacement, content)
        
        if count > 0:
            self.backup_file(relative_path)  # 先备份
            self.write_file_direct(relative_path, new_content)
        
        return count

    def update_wiki_links(self, relative_path: str, link_map: Dict[str, str]) -> int:
        """更新文件中的 Wiki 链接。
        
        Args:
            relative_path: 文件路径
            link_map: {旧链接名: 新链接路径} 映射
        
        Returns:
            总替换次数
        """
        content = self.read_file_direct(relative_path)
        total_count = 0
        
        for old_name, new_path in link_map.items():
            # 匹配 [[name]] 和 [[name|alias]]
            pattern = rf'\[\[{re.escape(old_name)}(\|[^\]]+)?\]\]'
            # 替换为 [[new_path|old_name]] 或 [[new_path|alias]]
            def replacer(m):
                alias_part = m.group(1) or f"|{old_name}"
                return f'[[{new_path}{alias_part}]]'
            
            new_content, count = re.subn(pattern, replacer, content)
            if count > 0:
                content = new_content
                total_count += count
        
        if total_count > 0:
            self.backup_file(relative_path)
            self.write_file_direct(relative_path, content)
        
        return total_count

    def reload_index(self) -> None:
        """刷新 Obsidian 索引。
        
        直接文件操作后调用，确保 Obsidian 的搜索索引同步。
        
        CLI: obsidian reload
        """
        run(["obsidian", "reload"], check=True)
```

### 实现要点

1. **CLI 不可用降级**: 检测 CLI 是否可用，不可用时提示用户启动 Obsidian
2. **JSON 格式优先**: 尽量使用 `format=json` 参数，便于解析
3. **错误处理**: 解析 CLI 返回的错误信息，抛出合适的异常
4. **PARA 目录常量**: 定义标准目录名
5. **索引同步**: 直接文件操作后调用 `obsidian reload` 刷新索引
6. **内容转义**: CLI create 命令需要转义换行符 (`\n`) 和制表符 (`\t`)，复杂内容建议用直接文件操作

---

## Task 2.2: Markdown AST 解析器（纯 Python）

**Files:**
- Create: `src/obsidian_kb/parser.py`
- Create: `tests/test_parser.py`

### 说明

此模块**仅用于 Markdown 结构解析**，不涉及链接验证。链接相关操作全部使用 CLI。

### 核心接口设计

```python
from markdown_it import MarkdownIt
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Section:
    """章节。"""
    title: str
    level: int
    content: str
    start_line: int
    end_line: int

@dataclass
class TaskItem:
    """任务项。"""
    text: str
    done: bool
    line: int

@dataclass
class ParsedDocument:
    """解析后的结构化文档。"""
    frontmatter: Optional['Frontmatter']
    sections: List[Section]
    tags: List[str]
    tasks: List[TaskItem]
    word_count: int


class MarkdownParser:
    """基于 markdown-it-py 的 AST 解析器。
    
    注意：链接提取和验证使用 LinkResolver（基于 CLI），
    此类仅用于章节、任务、标签等结构解析。
    """

    def __init__(self):
        self.md = MarkdownIt()

    def parse(self, content: str) -> ParsedDocument:
        """解析 Markdown 内容。"""
        pass

    def extract_sections(self, content: str) -> List[Section]:
        """提取章节结构。"""
        pass

    def extract_tasks(self, content: str) -> List[TaskItem]:
        """提取任务项（- [ ] 和 - [x]）。"""
        pass

    def extract_tags(self, content: str) -> List[str]:
        """提取 #标签（排除代码块中的）。"""
        pass

    def count_words(self, content: str) -> int:
        """统计字数。"""
        pass
```

### 实现要点

1. **AST 解析**: 使用 markdown-it-py 进行结构化解析
2. **代码块排除**: 解析时跳过代码块内的内容（避免误提取标签）
3. **章节边界**: 记录行号便于精确修改
4. **不处理链接**: 链接提取和验证交给 LinkResolver

---

## Task 2.3: 链接解析器（完全基于 CLI）

**Files:**
- Create: `src/obsidian_kb/link_resolver.py`
- Create: `tests/test_link_resolver.py`

### CLI 命令映射

| 方法 | CLI 命令 |
|------|---------|
| `get_backlinks(name)` | `obsidian backlinks file=<name> format=json` |
| `get_outlinks(name)` | `obsidian links file=<name>` |
| `find_broken_links()` | `obsidian unresolved format=json counts` |
| `find_orphans()` | `obsidian orphans` |
| `find_deadends()` | `obsidian deadends` |

### 核心接口设计

```python
from subprocess import run
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
import json


@dataclass
class Backlink:
    """反向链接。"""
    source_path: str
    link_text: str
    link_count: int = 1

@dataclass
class BrokenLink:
    """死链。"""
    link_text: str
    source_files: List[str]
    count: int


class LinkResolver:
    """链接解析器（完全基于 Obsidian CLI）。
    
    所有链接相关操作都通过 CLI 完成，利用 Obsidian 的索引能力。
    """

    # ========== 链接查询 ==========

    def get_backlinks(self, name: str) -> List[Backlink]:
        """获取反向链接（指向该笔记的所有链接）。
        
        CLI: obsidian backlinks file=<name> format=json
        """
        result = run(
            ["obsidian", "backlinks", f"file={name}", "format=json"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return []
        
        data = json.loads(result.stdout)
        return [Backlink(
            source_path=item.get('file', ''),
            link_text=item.get('link', ''),
            link_count=item.get('count', 1)
        ) for item in data]

    def get_outlinks(self, name: str) -> List[str]:
        """获取出链（该笔记指向的所有链接）。
        
        CLI: obsidian links file=<name>
        """
        result = run(
            ["obsidian", "links", f"file={name}"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return []
        return result.stdout.strip().split('\n') if result.stdout else []

    # ========== 健康检查 ==========

    def find_broken_links(self) -> List[BrokenLink]:
        """查找所有死链（目标不存在的链接）。
        
        CLI: obsidian unresolved format=json counts
        """
        result = run(
            ["obsidian", "unresolved", "format=json", "counts"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return []
        
        data = json.loads(result.stdout)
        return [BrokenLink(
            link_text=item.get('link', ''),
            source_files=item.get('files', []),
            count=item.get('count', 1)
        ) for item in data]

    def find_orphans(self) -> List[str]:
        """查找孤儿笔记（没有入链的文件）。
        
        CLI: obsidian orphans
        """
        result = run(
            ["obsidian", "orphans"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return []
        return result.stdout.strip().split('\n') if result.stdout else []

    def find_deadends(self) -> List[str]:
        """查找死胡同笔记（没有出链的文件）。
        
        CLI: obsidian deadends
        """
        result = run(
            ["obsidian", "deadends"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return []
        return result.stdout.strip().split('\n') if result.stdout else []

    # ========== PARA 分级检查 ==========

    def find_orphans_by_para(self) -> Dict[str, List[str]]:
        """按 PARA 分级查找孤儿笔记。
        
        严格检查目录：30_研究/, 40_知识库/
        放宽检查目录：00_收件箱/, 10_项目/, Daily/
        """
        all_orphans = self.find_orphans()
        
        result = {
            "strict": [],      # 需要处理的孤儿（研究/知识库）
            "relaxed": [],     # 可接受的孤儿（收件箱/项目/每日）
        }
        
        for path in all_orphans:
            if path.startswith("30_研究/") or path.startswith("40_知识库/"):
                result["strict"].append(path)
            else:
                result["relaxed"].append(path)
        
        return result

    # ========== 链接语法解析（纯文本，不验证目标） ==========

    def parse_link_syntax(self, link_text: str) -> Dict:
        """解析链接语法（纯文本解析，不验证目标是否存在）。
        
        支持的语法：
        - [[笔记名]]
        - [[笔记名|别名]]
        - [[笔记名#标题]]
        - [[笔记名^block-id]]
        - ![[图片.png]]
        - ![[笔记名]]
        
        Returns:
            {
                "target": "笔记名",
                "alias": "别名" or None,
                "heading": "标题" or None,
                "block": "block-id" or None,
                "embed": True/False
            }
        """
        import re
        
        result = {
            "target": None,
            "alias": None,
            "heading": None,
            "block": None,
            "embed": link_text.startswith("!")
        }
        
        # 移除 [[ 和 ]]
        content = link_text.strip("![][").strip("]]")
        
        # 分割别名
        if "|" in content:
            content, result["alias"] = content.split("|", 1)
        
        # 提取标题引用
        if "#" in content:
            content, result["heading"] = content.rsplit("#", 1)
        
        # 提取块引用
        if "^" in content:
            content, result["block"] = content.rsplit("^", 1)
        
        result["target"] = content
        return result
```

### 支持的链接语法

| 语法 | 说明 | CLI 是否支持 |
|------|------|-------------|
| `[[笔记名]]` | 基本双链 | ✅ |
| `[[笔记名\|别名]]` | 带别名 | ✅ |
| `[[笔记名#标题]]` | 标题引用 | ✅ |
| `[[笔记名^block-id]]` | 块引用 | ✅ |
| `![[图片.png]]` | 嵌入图片 | ✅ |
| `![[笔记名]]` | 嵌入笔记 | ✅ |

### 实现要点

1. **完全依赖 CLI**: 所有链接查询都通过 CLI 完成，不自己实现索引
2. **JSON 格式优先**: 使用 `format=json` 参数便于解析
3. **PARA 分级孤儿检测**: 区分严格检查和放宽检查的目录
4. **语法解析不验证**: `parse_link_syntax` 仅解析语法，不验证目标是否存在

---

## Part 2 完成检查清单

- [ ] Vault 操作封装完成 (vault.py) - 基于 CLI 的文件读写、列表、搜索
- [ ] Markdown AST 解析器完成 (parser.py) - 章节、任务、标签提取
- [ ] 链接解析器完成 (link_resolver.py) - 基于 CLI 的链接查询
- [ ] CLI 命令全部验证通过
- [ ] 所有测试通过

**下一步:** Part 3 将实现核心工作流。