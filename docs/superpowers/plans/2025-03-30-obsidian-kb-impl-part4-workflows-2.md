# Obsidian Knowledge Base 技能实施计划 - Part 4: 核心工作流 (下)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现四个工作流：归档、快速查询、回顾、健康检查。

**Architecture:** 继续使用工作流基类模式，每个命令作为独立模块实现。

**Tech Stack:** Python 3.8+, click (CLI)

---

## 项目文件结构（本 Part 新增）

```
src/obsidian_kb/workflows/
├── archive.py           # 归档
├── ask.py               # 快速查询
├── review.py            # 回顾
└── health_check.py      # 健康检查
tests/test_workflows/
├── test_archive.py
├── test_ask.py
├── test_review.py
└── test_health_check.py
```

---

## Task 4.1: `/archive` 归档工作流

**Files:**
- Create: `src/obsidian_kb/workflows/archive.py`
- Create: `tests/test_workflows/test_archive.py`

### CLI 命令映射

| 操作 | CLI 命令 |
|------|---------|
| 查找反向链接 | `obsidian backlinks file=<name> format=json` |
| 移动文件 | `obsidian move file=<name> to=<path>` |
| 更新属性 | `obsidian property:set name=status value=已归档 file=<name>` |
| 读取文件 | `obsidian read file=<name>` |
| 写入文件 | `obsidian append file=<name> content=<text>` |

### 支持模式

| 模式 | 命令示例 |
|------|---------|
| 单个归档 | `/archive "项目名"` |
| 批量归档 | `/archive --folder "00_收件箱"` |

### 工作流程

```
1. 查找笔记/文件夹
   CLI: obsidian search query=<name>

2. 检查关联（反向链接）
   CLI: obsidian backlinks file=<name> format=json

3. Dry-run 预览
   ┌──────────────────────────────────────┐
   │ 即将执行以下修改：                    │
   │ - 移动: 10_项目/旧项目.md             │
   │   → 50_归档/2025-03/旧项目.md         │
   │ - 修改: 20_领域/某笔记.md 中的 2 处链接 │
   │   [[旧项目]] → [[50_归档/2025-03/旧项目|旧项目]] │
   └──────────────────────────────────────┘

4. 确认归档

5. 执行归档
   ├─ CLI: obsidian move file=<name> to=50_归档/2025-03/
   ├─ CLI: obsidian property:set name=status value=已归档 file=<name>
   └─ 更新反向链接（读取源文件 → 替换链接 → 写回）

6. 更新 MOC 状态标记
```

### 核心接口

```python
class ArchiveWorkflow(BaseWorkflow):
    """归档工作流（基于 CLI）。"""

    def execute(self, target: str, folder: bool = False) -> WorkflowResult:
        pass

    def find_note(self, name: str) -> List[str]:
        """查找匹配的笔记。
        
        CLI: obsidian search query=<name>
        """
        result = run(
            ["obsidian", "search", f"query={name}"],
            capture_output=True, text=True
        )
        return result.stdout.strip().split('\n') if result.stdout else []

    def find_backlinks(self, name: str) -> List[Backlink]:
        """查找反向链接。
        
        CLI: obsidian backlinks file=<name> format=json
        """
        result = run(
            ["obsidian", "backlinks", f"file={name}", "format=json"],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout) if result.stdout else []
        return [Backlink(
            source_path=item.get('file', ''),
            link_text=item.get('link', ''),
            link_count=item.get('count', 1)
        ) for item in data]

    def move_note(self, name: str, to_folder: str) -> None:
        """移动笔记。
        
        CLI: obsidian move file=<name> to=<path>
        """
        run(["obsidian", "move", f"file={name}", f"to={to_folder}"], check=True)

    def update_status(self, name: str, status: str = "已归档") -> None:
        """更新状态属性。
        
        CLI: obsidian property:set name=status value=<status> file=<name>
        """
        run([
            "obsidian", "property:set",
            "name=status", f"value={status}", f"file={name}"
        ], check=True)

    def preview_changes(self, name: str) -> ArchivePreview:
        """预览归档变更（Dry-run）。"""
        backlinks = self.find_backlinks(name)
        target_path = f"50_归档/{datetime.now().strftime('%Y-%m')}/{name}"
        
        return ArchivePreview(
            note_path=name,
            target_path=target_path,
            backlinks=backlinks,
            link_updates=[self._plan_link_update(bl, target_path) for bl in backlinks]
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
        
        for bl in backlinks:
            # 直接读取文件（不通过 CLI）
            file_path = self.vault.path / bl.source_path
            if not file_path.exists():
                continue
            
            content = file_path.read_text(encoding='utf-8')
            
            # 替换链接（支持 [[name]] 和 [[name|alias]] 两种形式）
            import re
            pattern = rf'\[\[{re.escape(old_name)}(\|[^\]]+)?\]\]'
            # 使用 replacer 函数正确处理别名
            def replacer(m):
                alias_part = m.group(1) or f"|{old_name}"
                return f'[[{new_path}{alias_part}]]'
            new_content, count = re.subn(pattern, replacer, content)
            
            if count > 0:
                # 备份原文件
                backup_path = self.vault.path / "metadata" / "backups" / f"{bl.source_path}.bak"
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                backup_path.write_text(content, encoding='utf-8')
                
                # 写回新内容
                file_path.write_text(new_content, encoding='utf-8')
                updated += count
        
        # 刷新 Obsidian 索引
        if updated > 0:
            self.vault.reload_index()
        
        return updated
```

---

## Task 4.2: `/ask` 快速查询工作流

**Files:**
- Create: `src/obsidian_kb/workflows/ask.py`
- Create: `tests/test_workflows/test_ask.py`

### 工作流程

```
1. 知识库搜索
   └─ obsidian search query="问题关键词"

2. AI 回答
   └─ 基于搜索结果生成回答，引用相关笔记

3. 相关笔记推荐
   └─ 列出最相关的 2-3 篇笔记

4. 保存选项
   └─ 询问是否保存此回答到知识库
```

### 核心接口

```python
class AskWorkflow(BaseWorkflow):
    def execute(self, question: str) -> WorkflowResult:
        pass

    def search_knowledge(self, query: str) -> List[Note]:
        """搜索知识库。"""
        pass

    def generate_answer(self, question: str, notes: List[Note]) -> str:
        """基于笔记生成回答。"""
        pass

    def save_answer(self, question: str, answer: str) -> Note:
        """保存回答到知识库。"""
        pass
```

---

## Task 4.3: `/review` 回顾工作流

**Files:**
- Create: `src/obsidian_kb/workflows/review.py`
- Create: `tests/test_workflows/test_review.py`

### 范围选项

| 命令 | 范围 |
|------|------|
| `/review inbox` | 仅收件箱 |
| `/review projects` | 仅项目 |
| `/review all` | 全面回顾（默认） |

### 工作流程

```
1. 收件箱回顾（如果范围包含 inbox）
   ├─ 扫描 00_收件箱/ 所有笔记
   ├─ 按时间分组：今天/本周/更早
   └─ 给出处理建议

2. 项目回顾（如果范围包含 projects）
   ├─ 扫描 10_项目/ 所有项目
   ├─ 识别僵尸项目（30 天未更新）
   └─ 给出建议：激活/归档/继续推进

3. 生成回顾报告
   └─ 可选保存到 Daily/YYYY-MM-DD_回顾.md
```

### 输出格式

```python
@dataclass
class ReviewReport:
    date: str
    inbox: InboxReview
    projects: ProjectReview
    suggestions: List[Suggestion]

@dataclass
class InboxReview:
    total_count: int
    overdue_count: int  # 超过 7 天
    items: List[InboxItem]

@dataclass
class ProjectReview:
    total_count: int
    zombie_count: int  # 30 天未更新
    completing_soon: List[ProjectSummary]  # 即将完成
    zombies: List[ProjectSummary]

@dataclass
class Suggestion:
    priority: int  # 1 最高
    action: str
    target: str
    reason: str
```

---

## Task 4.4: `/health-check` 健康检查工作流

**Files:**
- Create: `src/obsidian_kb/workflows/health_check.py`
- Create: `tests/test_workflows/test_health_check.py`

### CLI 命令映射

| 检查类型 | CLI 命令 |
|---------|---------|
| 孤儿笔记 | `obsidian orphans` |
| 死链 | `obsidian unresolved format=json` |
| 死胡同 | `obsidian deadends` |
| 标签统计 | `obsidian tags counts format=json` |
| 文件总数 | `obsidian vault info=files` |

### 检查类型

| 命令 | 检查内容 | CLI 命令 |
|------|---------|---------|
| `/health-check orphans` | 孤儿笔记 | `obsidian orphans` |
| `/health-check deadlinks` | 死链 | `obsidian unresolved format=json` |
| `/health-check tags` | 标签一致性 | `obsidian tags counts format=json` |
| `/health-check all` | 全面检查（默认） | 以上全部 |

### 孤儿笔记检测规则（PARA 分级）

| 目录 | 检查策略 |
|------|---------|
| `00_收件箱/` | 放宽 - 临时存放 |
| `10_项目/` | 放宽 - 进行中 |
| `20_领域/` | 放宽 - 分类容器 |
| `30_研究/` | **严格** - 应有链接 |
| `40_知识库/` | **严格** - 必须有入链或出链 |
| `99_模板/` | 放宽 - 模板文件 |
| `Daily/` | 放宽 - 每日笔记 |

### 核心实现

```python
class HealthCheckWorkflow(BaseWorkflow):
    """健康检查工作流（完全基于 CLI）。"""

    def check_orphans(self) -> List[str]:
        """检查孤儿笔记。
        
        CLI: obsidian orphans
        """
        result = run(["obsidian", "orphans"], capture_output=True, text=True)
        all_orphans = result.stdout.strip().split('\n') if result.stdout else []
        
        # PARA 分级过滤
        strict_orphans = [
            p for p in all_orphans
            if p.startswith("30_研究/") or p.startswith("40_知识库/")
        ]
        return strict_orphans

    def check_deadlinks(self) -> List[BrokenLink]:
        """检查死链。
        
        CLI: obsidian unresolved format=json counts
        """
        result = run(
            ["obsidian", "unresolved", "format=json", "counts"],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout) if result.stdout else []
        return [BrokenLink(
            link_text=item.get('link', ''),
            source_files=item.get('files', []),
            count=item.get('count', 1)
        ) for item in data]

    def check_tags(self) -> Dict[str, int]:
        """检查标签统计。
        
        CLI: obsidian tags counts format=json
        """
        result = run(
            ["obsidian", "tags", "counts", "format=json"],
            capture_output=True, text=True
        )
        return json.loads(result.stdout) if result.stdout else {}

    def get_vault_stats(self) -> Dict:
        """获取 Vault 统计。
        
        CLI: obsidian vault info=files
        CLI: obsidian vault info=size
        """
        files = run(["obsidian", "vault", "info=files"], capture_output=True, text=True)
        return {"total_files": int(files.stdout.strip()) if files.stdout else 0}
```

### 输出格式

```python
@dataclass
class HealthReport:
    total_notes: int
    total_links: int
    total_tags: int
    health_score: int  # 0-100
    issues: List[HealthIssue]
    fix_suggestions: List[FixSuggestion]

@dataclass
class HealthIssue:
    type: str  # "orphan" | "deadlink" | "tag_duplicate"
    severity: str  # "warning" | "error"
    location: str
    description: str
    suggestion: str

@dataclass
class FixSuggestion:
    issue_type: str
    auto_fixable: bool
    fix_command: Optional[str]
```

---

## Part 4 完成检查清单

- [ ] `/archive` 工作流完成 - Dry-run 预览，链接更新
- [ ] `/ask` 工作流完成 - 知识库搜索 + AI 回答
- [ ] `/review` 工作流完成 - 收件箱/项目回顾
- [ ] `/health-check` 工作流完成 - 孤儿检测、死链检测、标签检查
- [ ] 所有测试通过

**下一步:** Part 5 将实现 MOC 管理和 CLI 层。