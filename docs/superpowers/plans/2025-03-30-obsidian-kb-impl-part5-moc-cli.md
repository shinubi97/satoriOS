# Obsidian Knowledge Base 技能实施计划 - Part 5: MOC 管理与 CLI 层

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现 MOC（Map of Content）管理和命令行入口，提供统一的交互界面。

**Architecture:** CLI 层使用 click 框架，MOC 管理作为独立工作流模块。

**Tech Stack:** Python 3.8+, click (CLI)

---

## 项目文件结构（本 Part 新增）

```
src/obsidian_kb/
├── cli.py               # CLI 入口
└── workflows/
    ├── mocs.py          # MOC 管理
    └── moc_review.py    # MOC 维护
tests/
├── test_cli.py
├── test_workflows/
│   ├── test_mocs.py
│   └── test_moc_review.py
```

---

## Task 5.1: `/mocs` MOC 管理工作流

**Files:**
- Create: `src/obsidian_kb/workflows/mocs.py`
- Create: `tests/test_workflows/test_mocs.py`

### 子命令

| 命令 | 功能 |
|------|------|
| `/mocs list` | 列出所有 MOC |
| `/mocs open <名称>` | 打开指定 MOC |
| `/mocs stats` | MOC 统计信息 |
| `/mocs create <名称>` | 创建新 MOC |

### `/mocs list` 输出示例

```
🗺️ MOC 列表
━━━━━━━━━━━━━━━━━━━━

40_知识库/moc/
├── moc-编程.md          12 个链接  更新: 2天前
├── moc-工作.md           8 个链接  更新: 5天前
├── moc-个人成长.md       5 个链接  更新: 1周前
└── moc-健康生活.md       3 个链接  更新: 2周前

💡 提示: 使用 `/mocs open 编程` 快速打开
```

### `/mocs stats` 输出示例

```
📊 MOC 统计: 编程
━━━━━━━━━━━━━━━━━━━━

笔记数: 12
健康度: 92%
⚠️  1 个死链
💡  3 个未链接的潜在相关笔记
```

### 核心接口

```python
class MocsWorkflow(BaseWorkflow):
    def list_mocs(self) -> List[MocInfo]:
        """列出所有 MOC。"""
        pass

    def open_moc(self, name: str) -> Note:
        """打开 MOC（模糊匹配名称）。"""
        pass

    def get_stats(self, moc_path: str) -> MocStats:
        """获取 MOC 统计信息。"""
        pass

    def create_moc(self, name: str, area: str) -> Note:
        """创建新 MOC。"""
        pass

@dataclass
class MocInfo:
    path: str
    title: str
    link_count: int
    last_updated: datetime

@dataclass
class MocStats:
    note_count: int
    health_score: int
    dead_links: List[str]
    unlinked_candidates: List[NoteMeta]
```

---

## Task 5.2: `/moc-review` MOC 维护工作流

**Files:**
- Create: `src/obsidian_kb/workflows/moc_review.py`
- Create: `tests/test_workflows/test_moc_review.py`

### 工作流程

```
1. 扫描未链接笔记
   ├─ 找出最近 7 天内创建的笔记
   ├─ 排除：Daily、已归档、模板
   └─ 检查是否已存在于 MOC 中

2. 按主题分组建议
   ├─ AI 分析每篇笔记内容
   └─ 建议归属的 MOC

3. 批量确认
   └─ 按 MOC 分组显示，一次性确认多个链接
```

### 输出示例

```
🗺️ MOC 维护建议
━━━━━━━━━━━━━━━━━━━━

最近 7 天未链接笔记: 5 篇

建议链接到 [[moc-编程]]:
   ✅ [[Python 装饰器详解]]
   ✅ [[异步编程笔记]]

建议链接到 [[moc-工作]]:
   ✅ [[会议记录-项目启动]]
   ✅ [[周报-2025-W13]]

建议新建 MOC [[moc-机器学习]]:
   ⚠️ [[机器学习入门]] 无法匹配现有 MOC

确认执行？ (全部确认/逐项确认/取消)
```

### 核心接口

```python
class MocReviewWorkflow(BaseWorkflow):
    def execute(self, days: int = 7) -> WorkflowResult:
        pass

    def find_unlinked_notes(self, days: int) -> List[Note]:
        """查找未链接笔记。"""
        pass

    def suggest_moc(self, note: Note) -> Optional[str]:
        """AI 建议笔记应归属的 MOC。"""
        pass

    def batch_link(self, links: List[Tuple[str, str]]) -> int:
        """批量添加链接到 MOC。返回成功数量。"""
        pass
```

---

## Task 5.3: CLI 入口

**Files:**
- Create: `src/obsidian_kb/cli.py`
- Create: `tests/test_cli.py`

### 命令结构

```
obsidian-kb
├── start-my-day          # 每日规划
├── kickoff <名称>        # 项目启动
├── research <主题>       # 研究笔记
├── brainstorm <主题>     # 头脑风暴
├── archive <目标>        # 归档
│   └── --folder
├── ask <问题>            # 快速查询
├── review [范围]         # 回顾
│   └── inbox|projects|all
├── health-check [类型]   # 健康检查
│   └── orphans|deadlinks|tags|all
├── mocs                  # MOC 管理
│   ├── list
│   ├── open <名称>
│   ├── stats
│   └── create <名称>
├── moc-review            # MOC 维护
└── config                # 配置管理
    ├── show
    ├── set <key> <value>
    └── init

注：对于超出上述工作流的操作，Agent 可以直接调用 obsidian CLI：
    obsidian --help  # 查看所有可用命令
```

### 核心实现

```python
import click
from obsidian_kb.config import get_config, Config
from obsidian_kb.vault import Vault
from obsidian_kb.workflows import (
    StartMyDayWorkflow, KickoffWorkflow, ResearchWorkflow,
    BrainstormWorkflow, ArchiveWorkflow,
    AskWorkflow, ReviewWorkflow, HealthCheckWorkflow,
    MocsWorkflow, MocReviewWorkflow
)

@click.group()
@click.option('--vault', type=click.Path(), help='Vault 路径')
@click.pass_context
def cli(ctx, vault):
    """Obsidian Knowledge Base 管理工具。"""
    ctx.ensure_object(dict)
    config = get_config()
    ctx.obj['config'] = config
    ctx.obj['vault'] = Vault(config.vault_path)

# ========== 每日规划 ==========

@cli.command()
@click.pass_context
def start_my_day(ctx):
    """每日规划工作流。无需参数。"""
    workflow = StartMyDayWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.execute()
    _print_result(result)

# ========== 项目启动 ==========

@cli.command()
@click.argument('idea_name', required=False)
@click.option('--area', help='所属领域，默认使用配置中的 default_area')
@click.option('--timeline', default='1个月', help='期望完成时间')
@click.pass_context
def kickoff(ctx, idea_name, area, timeline):
    """项目启动工作流。"""
    workflow = KickoffWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.execute(
        idea_name=idea_name,
        area=area,
        timeline=timeline
    )
    _print_result(result)

# ========== 研究笔记 ==========

@cli.command()
@click.argument('topic')
@click.option('--area', help='所属领域')
@click.option('--depth', type=click.Choice(['快速了解', '深入学习', '精通掌握']), 
              default='深入学习', help='研究深度')
@click.pass_context
def research(ctx, topic, area, depth):
    """研究笔记工作流。"""
    workflow = ResearchWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.execute(topic=topic, area=area, depth=depth)
    _print_result(result)

# ========== 头脑风暴 ==========

@cli.command()
@click.argument('topic')
@click.option('--project', help='关联的项目名称')
@click.option('--area', help='所属领域')
@click.option('--initial-idea', help='初始想法描述')
@click.pass_context
def brainstorm(ctx, topic, project, area, initial_idea):
    """头脑风暴工作流。"""
    workflow = BrainstormWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.execute(
        topic=topic,
        project=project,
        area=area,
        initial_idea=initial_idea
    )
    _print_result(result)

# ========== 归档 ==========

@cli.command()
@click.argument('target')
@click.option('--folder', is_flag=True, help='批量归档文件夹')
@click.option('--confirm/--no-confirm', default=True, help='是否需要确认')
@click.pass_context
def archive(ctx, target, folder, confirm):
    """归档工作流。"""
    workflow = ArchiveWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.execute(target=target, folder=folder, confirm=confirm)
    _print_result(result)

# ========== 快速查询 ==========

@cli.command()
@click.argument('question')
@click.pass_context
def ask(ctx, question):
    """快速查询工作流。"""
    workflow = AskWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.execute(question=question)
    _print_result(result)

# ========== 回顾 ==========

@cli.command()
@click.argument('scope', type=click.Choice(['inbox', 'projects', 'all']), default='all')
@click.pass_context
def review(ctx, scope):
    """知识库回顾工作流。"""
    workflow = ReviewWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.execute(scope=scope)
    _print_result(result)

# ========== 健康检查 ==========

@cli.command('health-check')
@click.argument('check_type', type=click.Choice(['orphans', 'deadlinks', 'tags', 'all']), 
                default='all')
@click.pass_context
def health_check(ctx, check_type):
    """知识库健康检查工作流。"""
    workflow = HealthCheckWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.execute(check_type=check_type)
    _print_result(result)

# ========== MOC 管理 ==========

@cli.group()
@click.pass_context
def mocs(ctx):
    """MOC 管理命令。"""
    pass

@mocs.command()
@click.pass_context
def list(ctx):
    """列出所有 MOC。"""
    workflow = MocsWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.list_mocs()
    _print_moc_list(result)

@mocs.command()
@click.argument('name')
@click.pass_context
def open(ctx, name):
    """打开指定 MOC（模糊匹配）。"""
    workflow = MocsWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.open_moc(name)
    _print_result(result)

@mocs.command()
@click.argument('name', required=False)
@click.pass_context
def stats(ctx, name):
    """显示 MOC 统计信息。不指定名称则显示所有 MOC 概览。"""
    workflow = MocsWorkflow(ctx.obj['vault'], ctx.obj['config'])
    if name:
        result = workflow.get_stats(name)
        _print_moc_stats(result)
    else:
        result = workflow.list_mocs()
        _print_moc_list(result)

@mocs.command()
@click.argument('name')
@click.option('--area', help='所属领域')
@click.pass_context
def create(ctx, name, area):
    """创建新 MOC。"""
    workflow = MocsWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.create_moc(name, area)
    _print_result(result)

# ========== MOC 维护 ==========

@cli.command('moc-review')
@click.option('--days', default=7, help='扫描最近 N 天的笔记')
@click.pass_context
def moc_review(ctx, days):
    """MOC 维护工作流：扫描未链接笔记并建议归档。"""
    workflow = MocReviewWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.execute(days=days)
    _print_result(result)

# ========== 配置管理 ==========

@cli.group()
@click.pass_context
def config(ctx):
    """配置管理命令。"""
    pass

@config.command()
@click.pass_context
def show(ctx):
    """显示当前配置。"""
    cfg = ctx.obj['config']
    click.echo(f"Vault 路径: {cfg.vault_path}")
    click.echo(f"默认领域: {cfg.default_area}")
    click.echo(f"静默模式: {cfg.quiet_mode}")

@config.command()
@click.argument('key')
@click.argument('value')
@click.pass_context
def set(ctx, key, value):
    """设置配置项。"""
    # 更新配置逻辑
    pass

@config.command()
@click.pass_context
def init(ctx):
    """初始化配置。"""
    # 初始化配置逻辑
    pass

# ========== 辅助函数 ==========

def _print_result(result: WorkflowResult):
    """打印工作流结果。"""
    if result.success:
        click.secho(f"✅ {result.message}", fg='green')
    else:
        click.secho(f"❌ {result.message}", fg='red')

    for file in result.created_files:
        click.echo(f"  📄 创建: {file}")
    for file in result.modified_files:
        click.echo(f"  ✏️ 修改: {file}")
    for suggestion in result.suggestions:
        click.echo(f"  💡 {suggestion}")

def _print_moc_list(mocs):
    """打印 MOC 列表。"""
    click.echo("🗺️ MOC 列表")
    click.echo("━" * 30)
    for moc in mocs:
        click.echo(f"  {moc.path}  ({moc.link_count} 个链接, {moc.last_updated})")

def _print_moc_stats(stats):
    """打印 MOC 统计。"""
    click.echo(f"📊 MOC 统计: {stats.title}")
    click.echo("━" * 30)
    click.echo(f"笔记数: {stats.note_count}")
    click.echo(f"健康度: {stats.health_score}%")
    if stats.dead_links:
        click.secho(f"⚠️ {len(stats.dead_links)} 个死链", fg='yellow')
    if stats.unlinked_candidates:
        click.echo(f"💡 {len(stats.unlinked_candidates)} 个未链接的潜在相关笔记")

if __name__ == '__main__':
    cli()
```

---

## Part 5 完成检查清单

- [ ] `/mocs` MOC 管理工作流完成 - list/open/stats/create
- [ ] `/moc-review` MOC 维护工作流完成 - 未链接笔记扫描、批量链接
- [ ] CLI 入口完成 - 所有命令注册
- [ ] 所有测试通过

**下一步:** Part 6 将实现模板系统。