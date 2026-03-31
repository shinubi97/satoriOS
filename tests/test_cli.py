"""CLI 测试."""
import pytest
import json
from pathlib import Path
from click.testing import CliRunner

from obsidian_kb.cli import cli
from obsidian_kb.config import Config, reset_config


class TestCLI:
    """CLI 测试."""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器。"""
        return CliRunner()

    @pytest.fixture
    def setup_vault(self, temp_vault):
        """设置测试 Vault。"""
        vault_path = temp_vault

        # 创建一些测试笔记
        inbox_path = vault_path / "00_收件箱"
        inbox_path.mkdir(parents=True, exist_ok=True)
        (inbox_path / "测试想法.md").write_text("""---
id: kb-20260331-100000-0001
title: 测试想法
type: idea
area: 编程
date: 2026-03-31
---

# 测试想法

这是一个测试想法。
""")

        # 创建项目
        projects_path = vault_path / "10_项目" / "编程"
        projects_path.mkdir(parents=True, exist_ok=True)
        (projects_path / "测试项目.md").write_text("""---
id: kb-20260331-100000-0002
title: 测试项目
type: project
area: 编程
date: 2026-03-31
status: 进行中
---

# 测试项目

这是一个测试项目。
""")

        yield vault_path

    def test_cli_help(self, runner):
        """测试 CLI 帮助信息。"""
        result = runner.invoke(cli, ['--help'])

        assert result.exit_code == 0
        assert "Obsidian Knowledge Base" in result.output

    def test_start_my_day(self, runner, setup_vault):
        """测试 start-my-day 命令。"""
        vault_path = setup_vault

        result = runner.invoke(cli, [
            '--vault', str(vault_path),
            'start-my-day'
        ])

        assert result.exit_code == 0

    def test_kickoff(self, runner, setup_vault):
        """测试 kickoff 命令。"""
        vault_path = setup_vault

        result = runner.invoke(cli, [
            '--vault', str(vault_path),
            'kickoff', '测试想法',
            '--area', '编程'
        ])

        assert result.exit_code == 0

    def test_research(self, runner, setup_vault):
        """测试 research 命令。"""
        vault_path = setup_vault

        result = runner.invoke(cli, [
            '--vault', str(vault_path),
            'research', 'Python 异步编程',
            '--area', '编程',
            '--depth', '深入学习'
        ])

        assert result.exit_code == 0

    def test_brainstorm(self, runner, setup_vault):
        """测试 brainstorm 命令。"""
        vault_path = setup_vault

        result = runner.invoke(cli, [
            '--vault', str(vault_path),
            'brainstorm', '项目架构设计',
            '--area', '编程'
        ])

        assert result.exit_code == 0

    def test_archive(self, runner, setup_vault):
        """测试 archive 命令。"""
        vault_path = setup_vault

        result = runner.invoke(cli, [
            '--vault', str(vault_path),
            'archive', '00_收件箱/测试想法.md',
            '--reason', '完成'
        ])

        assert result.exit_code == 0

    def test_archive_dry_run(self, runner, setup_vault):
        """测试 archive dry-run 命令。"""
        vault_path = setup_vault

        result = runner.invoke(cli, [
            '--vault', str(vault_path),
            'archive', '00_收件箱/测试想法.md',
            '--dry-run'
        ])

        assert result.exit_code == 0
        assert "预览" in result.output or "Dry" in result.output

    def test_ask(self, runner, setup_vault):
        """测试 ask 命令。"""
        vault_path = setup_vault

        result = runner.invoke(cli, [
            '--vault', str(vault_path),
            'ask', 'Python'
        ])

        assert result.exit_code == 0

    def test_review(self, runner, setup_vault):
        """测试 review 命令。"""
        vault_path = setup_vault

        result = runner.invoke(cli, [
            '--vault', str(vault_path),
            'review', 'inbox'
        ])

        assert result.exit_code == 0

    def test_health_check(self, runner, setup_vault):
        """测试 health-check 命令。"""
        vault_path = setup_vault

        result = runner.invoke(cli, [
            '--vault', str(vault_path),
            'health-check', 'all'
        ])

        assert result.exit_code == 0

    def test_mocs_list(self, runner, setup_vault):
        """测试 mocs list 命令。"""
        vault_path = setup_vault

        # 创建 MOC
        mocs_path = vault_path / "40_知识库" / "moc"
        mocs_path.mkdir(parents=True, exist_ok=True)
        (mocs_path / "moc-编程.md").write_text("""---
id: kb-20260331-100000-0003
title: 编程 MOC
type: moc
area: 编程
date: 2026-03-31
---

# 编程 MOC

## 相关项目

- [[测试项目]]
""")

        result = runner.invoke(cli, [
            '--vault', str(vault_path),
            'mocs', 'list'
        ])

        assert result.exit_code == 0

    def test_mocs_create(self, runner, setup_vault):
        """测试 mocs create 命令。"""
        vault_path = setup_vault

        result = runner.invoke(cli, [
            '--vault', str(vault_path),
            'mocs', 'create', '编程',
            '--description', '编程相关内容'
        ])

        assert result.exit_code == 0

    def test_moc_review(self, runner, setup_vault):
        """测试 moc-review 命令。"""
        vault_path = setup_vault

        result = runner.invoke(cli, [
            '--vault', str(vault_path),
            'moc-review',
            '--area', '编程'
        ])

        assert result.exit_code == 0


class TestConfigCommand:
    """配置命令测试."""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器。"""
        return CliRunner()

    @pytest.fixture
    def setup_vault(self, temp_vault):
        """设置测试 Vault。"""
        yield temp_vault

    def test_config_show(self, runner, setup_vault):
        """测试 config show 命令。"""
        vault_path = setup_vault

        result = runner.invoke(cli, [
            '--vault', str(vault_path),
            'config', 'show'
        ])

        assert result.exit_code == 0
        assert "Vault 路径" in result.output or "vault" in result.output.lower()

    def test_config_set(self, runner, setup_vault):
        """测试 config set 命令。"""
        vault_path = setup_vault

        result = runner.invoke(cli, [
            '--vault', str(vault_path),
            'config', 'set', 'default_area', '工作'
        ])

        assert result.exit_code == 0
        assert "已更新" in result.output

    def test_config_init(self, runner, setup_vault, tmp_path):
        """测试 config init 命令。"""
        vault_path = setup_vault

        result = runner.invoke(cli, [
            'config', 'init',
            '--vault', str(vault_path),
            '--area', '编程'
        ])

        assert result.exit_code == 0
        assert "配置已初始化" in result.output

    def test_config_init_invalid_vault(self, runner):
        """测试 config init 命令使用无效路径。"""
        result = runner.invoke(cli, [
            'config', 'init',
            '--vault', '/nonexistent/vault/path'
        ])

        # 应该失败或显示错误
        assert "不存在" in result.output or result.exit_code != 0


class TestConfigGroup:
    """配置组测试."""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器。"""
        return CliRunner()

    def test_config_help(self, runner):
        """测试 config 帮助信息。"""
        result = runner.invoke(cli, ['config', '--help'])

        assert result.exit_code == 0
        assert "show" in result.output
        assert "set" in result.output
        assert "init" in result.output


class TestMocsGroup:
    """MOCs 组测试."""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器。"""
        return CliRunner()

    def test_mocs_help(self, runner):
        """测试 mocs 帮助信息。"""
        result = runner.invoke(cli, ['mocs', '--help'])

        assert result.exit_code == 0
        assert "list" in result.output
        assert "open" in result.output
        assert "stats" in result.output
        assert "create" in result.output