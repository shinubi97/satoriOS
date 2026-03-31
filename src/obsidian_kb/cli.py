"""命令行入口.

提供 obsidian-kb CLI 命令。
"""
import argparse
import sys
from pathlib import Path
from typing import Optional

from obsidian_kb.config import Config
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


def create_parser() -> argparse.ArgumentParser:
    """创建命令行解析器。"""
    parser = argparse.ArgumentParser(
        prog="obsidian-kb",
        description="Obsidian 知识库管理工作流"
    )

    parser.add_argument(
        "--vault", "-v",
        type=str,
        help="Vault 路径（默认使用当前目录或环境变量 OBSIDIAN_VAULT）"
    )

    parser.add_argument(
        "--area", "-a",
        type=str,
        help="默认领域"
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # start-my-day
    subparsers.add_parser(
        "start-my-day",
        help="每日规划 - 扫描收件箱、项目、待办"
    )

    # kickoff
    kickoff_parser = subparsers.add_parser(
        "kickoff",
        help="启动新项目"
    )
    kickoff_parser.add_argument("idea_name", help="想法名称")
    kickoff_parser.add_argument("--area", help="所属领域")
    kickoff_parser.add_argument("--timeline", default="1个月", help="完成时间")
    kickoff_parser.add_argument("--goals", nargs="+", help="项目目标")

    # research
    research_parser = subparsers.add_parser(
        "research",
        help="创建研究笔记"
    )
    research_parser.add_argument("topic", help="研究主题")
    research_parser.add_argument("--area", help="所属领域")
    research_parser.add_argument(
        "--depth",
        choices=["快速了解", "深入学习", "精通掌握"],
        default="深入学习",
        help="研究深度"
    )

    # brainstorm
    brainstorm_parser = subparsers.add_parser(
        "brainstorm",
        help="创建头脑风暴"
    )
    brainstorm_parser.add_argument("topic", help="主题")
    brainstorm_parser.add_argument("--area", help="所属领域")
    brainstorm_parser.add_argument("--project", help="关联项目")
    brainstorm_parser.add_argument("--idea", help="初始想法")

    # archive
    archive_parser = subparsers.add_parser(
        "archive",
        help="归档笔记"
    )
    archive_parser.add_argument("note_path", help="笔记路径")
    archive_parser.add_argument("--reason", default="完成", help="归档原因")

    # ask
    ask_parser = subparsers.add_parser(
        "ask",
        help="问答"
    )
    ask_parser.add_argument("question", help="问题")
    ask_parser.add_argument("--max-results", type=int, default=5, help="最大结果数")

    # review
    review_parser = subparsers.add_parser(
        "review",
        help="回顾笔记"
    )
    review_parser.add_argument("note_path", help="笔记路径")

    # health-check
    subparsers.add_parser(
        "health-check",
        help="健康检查"
    )

    # mocs
    mocs_parser = subparsers.add_parser(
        "mocs",
        help="管理 MOC"
    )
    mocs_parser.add_argument("--area", help="查看特定领域 MOC")
    mocs_parser.add_argument("--create", help="创建新 MOC")
    mocs_parser.add_argument("--update", help="更新 MOC")

    # moc-review
    moc_review_parser = subparsers.add_parser(
        "moc-review",
        help="回顾 MOC"
    )
    moc_review_parser.add_argument("--area", help="领域名称")
    moc_review_parser.add_argument("--path", help="MOC 路径")
    moc_review_parser.add_argument("--all", action="store_true", help="回顾所有 MOC")

    return parser


def get_config(args) -> Config:
    """获取配置。"""
    vault_path = args.vault

    if not vault_path:
        # 尝试环境变量
        import os
        vault_path = os.environ.get("OBSIDIAN_VAULT")

    if not vault_path:
        # 尝试当前目录
        vault_path = Path.cwd()
    else:
        vault_path = Path(vault_path)

    return Config(
        vault_path=vault_path,
        default_area=getattr(args, "area", None) or "通用"
    )


def main():
    """主入口。"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    config = get_config(args)
    vault = Vault(config.vault_path)

    # 执行命令
    result = None

    if args.command == "start-my-day":
        workflow = StartMyDayWorkflow(vault, config)
        result = workflow.execute()

    elif args.command == "kickoff":
        workflow = KickoffWorkflow(vault, config)
        result = workflow.execute(
            idea_name=args.idea_name,
            area=args.area,
            timeline=args.timeline,
            goals=args.goals or []
        )

    elif args.command == "research":
        workflow = ResearchWorkflow(vault, config)
        result = workflow.execute(
            topic=args.topic,
            area=args.area,
            depth=args.depth
        )

    elif args.command == "brainstorm":
        workflow = BrainstormWorkflow(vault, config)
        result = workflow.execute(
            topic=args.topic,
            area=args.area,
            project=args.project,
            initial_idea=args.idea
        )

    elif args.command == "archive":
        workflow = ArchiveWorkflow(vault, config)
        result = workflow.execute(
            note_path=args.note_path,
            reason=args.reason
        )

    elif args.command == "ask":
        workflow = AskWorkflow(vault, config)
        result = workflow.execute(
            question=args.question,
            max_results=args.max_results
        )

    elif args.command == "review":
        workflow = ReviewWorkflow(vault, config)
        result = workflow.execute(note_path=args.note_path)

    elif args.command == "health-check":
        workflow = HealthCheckWorkflow(vault, config)
        result = workflow.execute()

    elif args.command == "mocs":
        workflow = MocsWorkflow(vault, config)
        if args.create:
            result = workflow.create_moc(args.create)
        elif args.update:
            result = workflow.update_moc(args.update)
        elif args.area:
            result = workflow.get_moc(args.area)
        else:
            result = workflow.execute()

    elif args.command == "moc-review":
        workflow = MocReviewWorkflow(vault, config)
        if args.all:
            result = workflow.review_all_mocs()
        else:
            result = workflow.execute(area=args.area, moc_path=args.path)

    # 输出结果
    if result:
        print(result.message)
        if result.suggestions:
            print("\n建议:")
            for suggestion in result.suggestions:
                print(f"  - {suggestion}")
        if result.created_files:
            print("\n创建的文件:")
            for f in result.created_files:
                print(f"  - {f}")


if __name__ == "__main__":
    main()