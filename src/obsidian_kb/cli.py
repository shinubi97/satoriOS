"""命令行入口.

提供 obsidian-kb CLI 命令，使用 click 框架实现。
"""
import click
import json
from pathlib import Path
from typing import Optional

from obsidian_kb.config import Config, get_config, reset_config
from obsidian_kb.vault import Vault
from obsidian_kb.workflows.start_my_day import StartMyDayWorkflow
from obsidian_kb.workflows.kickoff import KickoffWorkflow
from obsidian_kb.workflows.research import ResearchWorkflow
from obsidian_kb.workflows.brainstorm import BrainstormWorkflow
from obsidian_kb.workflows.archive import ArchiveWorkflow
from obsidian_kb.workflows.ask import AskWorkflow
from obsidian_kb.workflows.review import ReviewWorkflow
from obsidian_kb.workflows.health_check import HealthCheckWorkflow
from obsidian_kb.workflows.mocs import MocsWorkflow
from obsidian_kb.workflows.moc_review import MocReviewWorkflow
from obsidian_kb.workflows.import_workflow import ImportWorkflow
from obsidian_kb.backup import BackupManager


# ========== 辅助函数 ==========

def _print_result(result):
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


def _print_daily_plan(result):
    """打印每日规划报告。"""
    from datetime import date
    from obsidian_kb.workflows.start_my_day import DailyPlanData, InboxItem, ProjectSummary, TaskItem
    today = date.today().isoformat()

    click.echo(f"📅 {today} 每日规划")
    click.echo("━" * 40)

    if result.data:
        # 数据可能嵌套在 'plan' 字段中，也可能直接在 data 中
        plan_data = result.data.get('plan') or result.data

        # 处理 dataclass 或 dict 类型
        if isinstance(plan_data, DailyPlanData):
            inbox_count = plan_data.inbox_count
            inbox_items = plan_data.inbox_items
            projects = plan_data.active_projects
            todos = plan_data.todos
        else:
            inbox_count = plan_data.get('inbox_count', 0)
            inbox_items = plan_data.get('inbox_items', [])
            projects = plan_data.get('active_projects', [])
            todos = plan_data.get('todos', [])

        # 收件箱
        click.echo(f"📥 收件箱待处理: {inbox_count} 项")

        if inbox_items:
            for item in inbox_items[:5]:
                if isinstance(item, InboxItem):
                    title = item.title
                else:
                    title = item.get('title', 'N/A')
                click.echo(f"   • {title}")

        # 进行中项目
        click.echo(f"\n🚀 进行中项目: {len(projects)} 个")
        for p in projects[:5]:
            if isinstance(p, ProjectSummary):
                name = p.name
                status = p.status
            else:
                name = p.get('name', 'N/A')
                status = p.get('status', '进行中')
            click.echo(f"   • {name} [{status}]")

        # 待办事项
        if todos:
            click.echo(f"\n✅ 待办事项: {len(todos)} 条")
            for t in todos[:5]:
                if isinstance(t, TaskItem):
                    text = t.text
                else:
                    text = t.get('text', 'N/A')
                click.echo(f"   • {text}")

    click.echo("\n" + "━" * 40)

    if result.suggestions:
        click.echo("💡 今日建议重点:")
        for i, s in enumerate(result.suggestions[:5], 1):
            click.echo(f"   {i}. {s}")


def _print_moc_list(mocs):
    """打印 MOC 列表。"""
    click.echo("🗺️ MOC 列表")
    click.echo("━" * 30)
    for moc in mocs:
        link_count = getattr(moc, 'link_count', 0)
        updated = getattr(moc, 'modified_time', '未知')
        click.echo(f"  {moc.path}  ({link_count} 个链接, {updated})")


def _print_moc_detail(result):
    """打印单个 MOC 详情。"""
    if not result.success:
        click.secho(f"❌ {result.message}", fg='red')
        for s in result.suggestions:
            click.echo(f"  💡 {s}")
        return

    click.secho(f"✅ {result.message}", fg='green')

    if result.data and result.data.get('moc'):
        moc = result.data['moc']
        click.echo("\n" + "━" * 40)
        click.echo(f"📍 路径: {moc.get('path', 'N/A')}")
        click.echo(f"🏷️ 领域: {moc.get('area', 'N/A')}")

        # 显示内容摘要
        content = moc.get('content', '')
        if content:
            lines = content.split('\n')
            click.echo("\n📄 内容预览:")
            for line in lines[:15]:
                if line.strip():
                    click.echo(f"  {line}")

    for s in result.suggestions:
        click.echo(f"  💡 {s}")


def _print_moc_stats(stats):
    """打印 MOC 统计。"""
    click.echo(f"📊 MOC 统计: {getattr(stats, 'title', 'N/A')}")
    click.echo("━" * 30)
    click.echo(f"笔记数: {getattr(stats, 'note_count', 0)}")
    click.echo(f"健康度: {getattr(stats, 'health_score', 0)}%")
    if hasattr(stats, 'dead_links') and stats.dead_links:
        click.secho(f"⚠️ {len(stats.dead_links)} 个死链", fg='yellow')
    if hasattr(stats, 'unlinked_candidates') and stats.unlinked_candidates:
        click.echo(f"💡 {len(stats.unlinked_candidates)} 个未链接的潜在相关笔记")


# ========== 主命令组 ==========

@click.group()
@click.option('--vault', type=click.Path(), help='Vault 路径')
@click.pass_context
def cli(ctx, vault):
    """Obsidian Knowledge Base 管理工具。"""
    ctx.ensure_object(dict)

    # 重置配置单例，确保每次都读取最新配置文件
    reset_config()

    try:
        config = get_config()
    except ValueError:
        # 配置不存在，使用默认值
        if vault:
            config = Config(
                vault_path=Path(vault),
                default_area="通用"
            )
        else:
            config = Config(
                vault_path=Path.cwd(),
                default_area="通用"
            )

    ctx.obj['config'] = config
    ctx.obj['vault'] = Vault(config.vault_path)


# ========== 每日规划 ==========

@cli.command()
@click.pass_context
def start_my_day(ctx):
    """每日规划工作流。无需参数。"""
    workflow = StartMyDayWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.execute()
    _print_daily_plan(result)


# ========== 项目启动 ==========

@cli.command()
@click.argument('idea_name', required=False)
@click.option('--area', help='所属领域，默认使用配置中的 default_area')
@click.option('--timeline', default='1个月', help='期望完成时间')
@click.option('--goals', multiple=True, help='项目目标')
@click.pass_context
def kickoff(ctx, idea_name, area, timeline, goals):
    """项目启动工作流。"""
    workflow = KickoffWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.execute(
        idea_name=idea_name,
        area=area,
        timeline=timeline,
        goals=list(goals) if goals else []
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
@click.option('--idea', 'initial_idea', help='初始想法描述')
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
@click.option('--reason', default='完成', help='归档原因')
@click.option('--dry-run', is_flag=True, help='只预览不执行')
@click.pass_context
def archive(ctx, target, folder, reason, dry_run):
    """归档工作流。"""
    workflow = ArchiveWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.execute(
        note_path=target,
        reason=reason,
        dry_run=dry_run
    )
    _print_result(result)


# ========== 快速查询 ==========

@cli.command()
@click.argument('question')
@click.option('--max-results', default=5, help='最大结果数')
@click.pass_context
def ask(ctx, question, max_results):
    """快速查询工作流。"""
    workflow = AskWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.execute(question=question, max_results=max_results)
    _print_result(result)


# ========== 回顾 ==========

@cli.command()
@click.argument('note_path', required=False)
@click.option('--focus', help='关注重点')
@click.pass_context
def review(ctx, note_path, focus):
    """知识库回顾工作流。"""
    workflow = ReviewWorkflow(ctx.obj['vault'], ctx.obj['config'])

    if note_path:
        result = workflow.execute(note_path=note_path, focus=focus)
        _print_result(result)
    else:
        # 如果没有指定笔记路径，扫描收件箱
        result = workflow.review_inbox()
        _print_review_inbox(result)


def _print_review_inbox(result):
    """打印收件箱回顾结果。"""
    if not result.success:
        click.secho(f"❌ {result.message}", fg='red')
        return

    click.echo("📥 收件箱回顾")
    click.echo("━" * 40)

    if result.data:
        inbox_count = result.data.get('inbox_count', 0)
        items = result.data.get('items', [])

        click.echo(f"\n待处理: {inbox_count} 条\n")

        if items:
            for i, item in enumerate(items[:10], 1):
                # 从路径中提取文件名
                import os
                filename = os.path.basename(item)
                click.echo(f"{i}. \"{filename}\"")

            click.echo("\n" + "━" * 40)
            click.echo("\n处理方式:")
            click.echo("  A. 逐条处理 (使用 /kickoff 或 /research)")
            click.echo("  B. 批量归档")
            click.echo("  C. 暂不处理")
        else:
            click.echo("✅ 收件箱为空")

    for s in result.suggestions:
        click.echo(f"  💡 {s}")


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


@mocs.command(name='list')
@click.pass_context
def list_mocs(ctx):
    """列出所有 MOC。"""
    workflow = MocsWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.execute()

    if result.success and result.data and result.data.get('mocs'):
        click.echo("🗺️ MOC 列表")
        click.echo("━" * 40)

        moc_path = ctx.obj['vault'].path / "40_知识库" / "moc"
        click.echo(f"\n{moc_path.relative_to(ctx.obj['vault'].path)}/")

        for moc in result.data['mocs']:
            title = moc.get('title', moc.get('path', 'Unknown'))
            area = moc.get('area', '')
            click.echo(f"├── {title}")
            if area:
                click.echo(f"│   领域: {area}")

        click.echo(f"\n💡 提示: 使用 `obsidian-kb mocs open <名称>` 快速打开")
    else:
        _print_result(result)


@mocs.command(name='open')
@click.argument('name')
@click.pass_context
def open_moc(ctx, name):
    """打开指定 MOC（模糊匹配）。"""
    workflow = MocsWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.get_moc(name)
    _print_moc_detail(result)


@mocs.command()
@click.argument('name', required=False)
@click.pass_context
def stats(ctx, name):
    """显示 MOC 统计信息。不指定名称则显示所有 MOC 概览。"""
    workflow = MocsWorkflow(ctx.obj['vault'], ctx.obj['config'])
    if name:
        result = workflow.get_moc(name)
        _print_result(result)
    else:
        result = workflow.execute()
        _print_result(result)


@mocs.command()
@click.argument('area')
@click.option('--description', default='', help='MOC 描述')
@click.pass_context
def create(ctx, area, description):
    """创建新 MOC。"""
    workflow = MocsWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.create_moc(area=area, description=description)
    _print_result(result)


@mocs.command()
@click.argument('name')
@click.pass_context
def update(ctx, name):
    """更新 MOC。"""
    workflow = MocsWorkflow(ctx.obj['vault'], ctx.obj['config'])
    result = workflow.update_moc(name)
    _print_result(result)


# ========== MOC 维护 ==========

@cli.command('moc-review')
@click.option('--area', help='指定领域')
@click.option('--path', 'moc_path', help='MOC 路径')
@click.option('--all', 'review_all', is_flag=True, help='回顾所有 MOC')
@click.pass_context
def moc_review(ctx, area, moc_path, review_all):
    """MOC 维护工作流：扫描未链接笔记并建议归档。"""
    workflow = MocReviewWorkflow(ctx.obj['vault'], ctx.obj['config'])

    if review_all:
        result = workflow.review_all_mocs()
    else:
        result = workflow.execute(area=area, moc_path=moc_path)

    _print_result(result)


# ========== 外部内容导入 ==========

@cli.command()
@click.argument('content', required=False)
@click.option('--type', 'content_type', help='内容类型: article/tutorial/snippet/knowledge')
@click.option('--area', help='所属领域')
@click.option('--url', help='来源 URL')
@click.pass_context
def import_content(ctx, content, content_type, area, url):
    """导入外部内容到知识库。"""
    workflow = ImportWorkflow(ctx.obj['vault'], ctx.obj['config'])

    # 如果提供了 URL，使用 URL 导入
    if url and not content:
        result = workflow.import_from_url(url, area)
    elif content:
        result = workflow.execute(content=content, content_type=content_type, area=area)
    else:
        click.secho("❌ 请提供内容或 URL", fg='red')
        return

    _print_result(result)


# ========== 备份与恢复 ==========

@cli.command()
@click.argument('target', required=False)
@click.option('--full', is_flag=True, help='全量备份整个 Vault')
@click.pass_context
def backup(ctx, target, full):
    """备份笔记。"""
    backup_manager = BackupManager(ctx.obj['vault'].path)

    if full:
        # 全量备份
        all_notes = list(ctx.obj['vault'].path.rglob("*.md"))
        note_paths = [str(n.relative_to(ctx.obj['vault'].path)) for n in all_notes]
        record = backup_manager.create_batch_backup(note_paths, "full_backup")

        click.secho(f"✅ 全量备份完成", fg='green')
        click.echo(f"备份 ID: {record.backup_id}")
        click.echo(f"备份文件: {len(record.files)} 个")
        click.echo(f"备份路径: {record.backup_path}")
    elif target:
        # 单文件备份
        record = backup_manager.create_backup([target], "manual")
        click.secho(f"✅ 备份完成", fg='green')
        click.echo(f"备份 ID: {record.backup_id}")
    else:
        # 列出最近备份
        records = backup_manager.list_backups(limit=10)
        if not records:
            click.echo("暂无备份记录")
            return

        click.echo("📦 最近备份")
        click.echo("━" * 30)
        for r in records:
            click.echo(f"  {r.backup_id} - {r.operation} ({len(r.files)} 文件)")


@cli.command()
@click.argument('backup_id', required=False)
@click.option('--list', 'list_backups', is_flag=True, help='列出可恢复的备份')
@click.pass_context
def restore(ctx, backup_id, list_backups):
    """从备份恢复。"""
    backup_manager = BackupManager(ctx.obj['vault'].path)

    if list_backups or not backup_id:
        # 列出可恢复的备份
        records = backup_manager.list_backups(limit=20)
        if not records:
            click.echo("暂无可恢复的备份")
            return

        click.echo("📋 可恢复的操作")
        click.echo("━" * 30)
        for i, r in enumerate(records, 1):
            click.echo(f"  {i}. [{r.timestamp.split('T')[1][:5]}] {r.operation} ({len(r.files)} 文件)")

        click.echo("\n使用 /restore <backup_id> 恢复")
        return

    # 恢复指定备份
    success = backup_manager.restore_backup(backup_id)

    if success:
        click.secho(f"✅ 已恢复备份: {backup_id}", fg='green')
    else:
        click.secho(f"❌ 恢复失败: 备份不存在或文件缺失", fg='red')


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
    click.echo(f"自动确认阈值: {cfg.auto_confirm_threshold}")


@config.command()
@click.argument('key')
@click.argument('value')
@click.pass_context
def set(ctx, key, value):
    """设置配置项。"""
    cfg = ctx.obj['config']

    # 支持的配置项
    valid_keys = ['default_area', 'quiet_mode', 'auto_confirm_threshold']

    if key not in valid_keys:
        click.secho(f"❌ 未知的配置项: {key}", fg='red')
        click.echo(f"有效的配置项: {', '.join(valid_keys)}")
        return

    # 更新配置
    if key == 'default_area':
        cfg.default_area = value
    elif key == 'quiet_mode':
        cfg.quiet_mode = value.lower() in ('true', '1', 'yes')
    elif key == 'auto_confirm_threshold':
        try:
            cfg.auto_confirm_threshold = float(value)
        except ValueError:
            click.secho("❌ auto_confirm_threshold 必须是数字", fg='red')
            return

    # 保存配置
    config_path = Path.home() / ".config" / "obsidian-kb" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "vault_path": str(cfg.vault_path),
        "default_area": cfg.default_area,
        "quiet_mode": cfg.quiet_mode,
        "auto_confirm_threshold": cfg.auto_confirm_threshold,
        "auto_confirm_actions": list(cfg.auto_confirm_actions) if cfg.auto_confirm_actions else [],
        "templates": dict(cfg.templates) if cfg.templates else {}
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    click.secho(f"✅ 已更新 {key} = {value}", fg='green')


@config.command()
@click.option('--vault', required=True, help='Vault 路径')
@click.option('--area', default='通用', help='默认领域')
@click.pass_context
def init(ctx, vault, area):
    """初始化配置。"""
    config_path = Path.home() / ".config" / "obsidian-kb" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    vault_path = Path(vault).resolve()

    if not vault_path.exists():
        click.secho(f"❌ Vault 路径不存在: {vault_path}", fg='red')
        return

    data = {
        "vault_path": str(vault_path),
        "default_area": area,
        "quiet_mode": False,
        "auto_confirm_threshold": 0.8,
        "auto_confirm_actions": ["moc_link", "tag_extraction"],
        "templates": {
            "project": "99_模板/项目启动模板.md",
            "research": "99_模板/研究笔记模板.md",
            "brainstorm": "99_模板/头脑风暴模板.md",
            "daily": "99_模板/每日规划模板.md",
            "moc": "99_模板/MOC模板.md"
        }
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # 重置配置实例
    reset_config()

    click.secho(f"✅ 配置已初始化", fg='green')
    click.echo(f"Vault 路径: {vault_path}")
    click.echo(f"默认领域: {area}")
    click.echo(f"配置文件: {config_path}")


# ========== 主入口 ==========

def main():
    """主入口。"""
    cli()


if __name__ == '__main__':
    main()