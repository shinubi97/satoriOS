"""环境依赖检查模块测试."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from obsidian_kb.utils.check_env import check_dependencies, check_obsidian_cli


class TestCheckEnv:
    """环境检查测试."""

    def test_check_obsidian_cli_available(self):
        """测试 Obsidian CLI 可用."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="obsidian-cli v1.0")

            result = check_obsidian_cli()
            assert result['available'] is True
            assert 'version' in result

    def test_check_obsidian_cli_not_available(self):
        """测试 Obsidian CLI 不可用."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = check_obsidian_cli()
            assert result['available'] is False
            assert 'error' in result

    def test_check_dependencies_all_ok(self, temp_vault, temp_config_file):
        """测试所有依赖检查通过."""
        import os
        os.environ["OBSIDIAN_KB_CONFIG"] = str(temp_config_file)

        with patch('obsidian_kb.utils.check_env.check_obsidian_cli') as mock_obsidian:
            mock_obsidian.return_value = {'available': True, 'version': '1.0'}

            result = check_dependencies()
            assert result['success'] is True
            assert len(result['issues']) == 0

        if "OBSIDIAN_KB_CONFIG" in os.environ:
            del os.environ["OBSIDIAN_KB_CONFIG"]

    def test_check_dependencies_with_issues(self):
        """测试依赖检查发现问题."""
        with patch('obsidian_kb.utils.check_env.check_obsidian_cli') as mock_obsidian:
            mock_obsidian.return_value = {'available': False, 'error': 'not found'}

            result = check_dependencies()
            assert result['success'] is False
            assert len(result['issues']) > 0

    def test_check_dependencies_raises_on_critical_missing(self):
        """测试关键依赖缺失时抛出错误."""
        with patch('obsidian_kb.utils.check_env.check_obsidian_cli') as mock_obsidian:
            mock_obsidian.return_value = {'available': False, 'error': 'not found'}

            with pytest.raises(RuntimeError, match="Critical dependencies missing"):
                check_dependencies(raise_on_error=True)