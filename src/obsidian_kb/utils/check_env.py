"""环境依赖检查模块.

检查系统依赖：
- obsidian CLI 工具
- Vault 路径配置
"""
import shutil
import subprocess
from typing import Dict, Optional


# Obsidian CLI 命令名
OBSIDIAN_CLI_CMD = 'obsidian'


def check_obsidian_cli() -> Dict[str, any]:
    """检查 Obsidian CLI 是否可用.

    Returns:
        包含 'available' (bool) 和 'version' 或 'error' 的字典
    """
    try:
        result = subprocess.run(
            [OBSIDIAN_CLI_CMD, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return {
                'available': True,
                'version': result.stdout.strip()
            }
        else:
            return {
                'available': False,
                'error': f"Obsidian CLI returned error: {result.stderr}"
            }
    except FileNotFoundError:
        return {
            'available': False,
            'error': 'Obsidian CLI not found. Please ensure Obsidian is running with CLI plugin enabled.'
        }
    except subprocess.TimeoutExpired:
        return {
            'available': False,
            'error': 'Obsidian CLI timed out'
        }


def check_vault_config() -> Dict[str, any]:
    """检查 Vault 路径配置.

    Returns:
        包含 'configured' (bool) 和 'path' 或 'error' 的字典
    """
    try:
        from obsidian_kb.config import get_config
        config = get_config()

        return {
            'configured': True,
            'path': str(config.vault_path)
        }
    except (ValueError, FileNotFoundError) as e:
        return {
            'configured': False,
            'error': str(e)
        }


def check_dependencies(raise_on_error: bool = False) -> Dict[str, any]:
    """执行完整的环境依赖检查.

    Args:
        raise_on_error: 如果为 True，关键依赖缺失时抛出 RuntimeError

    Returns:
        检查结果字典，包含 success、issues、install_instructions
    """
    issues = []
    install_instructions = []

    # 检查 Obsidian CLI
    obsidian_result = check_obsidian_cli()
    if not obsidian_result['available']:
        issues.append(f"Obsidian CLI: {obsidian_result['error']}")
        install_instructions.append(
            "- obsidian CLI: Open Obsidian app and enable the CLI plugin"
        )

    # 检查 Vault 配置
    vault_result = check_vault_config()
    if not vault_result['configured']:
        issues.append(f"Vault config: {vault_result['error']}")

    # 构建结果
    success = len(issues) == 0
    result = {
        'success': success,
        'issues': issues,
        'install_instructions': install_instructions,
        'obsidian': obsidian_result,
        'vault': vault_result
    }

    # 如果需要抛出错误
    if not success and raise_on_error:
        error_msg = "Critical dependencies missing:\n" + "\n".join(issues)
        if install_instructions:
            error_msg += "\n\nInstall instructions:\n" + "\n".join(install_instructions)
        raise RuntimeError(error_msg)

    return result


def print_dependency_report(result: Dict[str, any]) -> None:
    """打印依赖检查报告.

    Args:
        result: check_dependencies 的返回结果
    """
    print("=" * 50)
    print("Obsidian KB 环境检查报告")
    print("=" * 50)

    if result['success']:
        print("All dependency checks passed")
        print(f"   Vault path: {result['vault']['path']}")
        print(f"   Obsidian CLI: {result['obsidian']['version']}")
    else:
        print("Issues found:")
        for issue in result['issues']:
            print(f"   - {issue}")

        if result['install_instructions']:
            print("\nInstall instructions:")
            for instruction in result['install_instructions']:
                print(f"   {instruction}")

    print("=" * 50)