# Obsidian Knowledge Base 技能实施计划 - Part 1: 核心基础设施

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建 Obsidian 知识库管理技能的核心基础设施层，包括项目结构、配置管理、环境检查、ID生成器和Frontmatter解析器。

**Architecture:** 采用 Python 模块化设计，配置通过 JSON 文件注入，依赖检查在启动时自动执行，ID生成采用时间戳+随机码模式确保并发安全。

**Tech Stack:** Python 3.8+, pydantic (数据验证), pyyaml (YAML处理), click (CLI框架)

---

## 项目文件结构

```
obsidian-knowledge-base/
├── SKILL.md                    # 技能定义文件 (Part 7)
├── pyproject.toml              # Python项目配置
├── src/
│   └── obsidian_kb/
│       ├── __init__.py
│       ├── cli.py              # CLI入口 (Part 5)
│       ├── config.py           # 配置管理 (本Part)
│       ├── vault.py            # Vault操作 (Part 2)
│       ├── parser.py           # Markdown AST解析 (Part 2)
│       ├── link_resolver.py    # 链接解析器 (Part 2)
│       ├── workflows/          # 工作流模块 (Part 3-4)
│       │   ├── __init__.py
│       │   ├── start_my_day.py
│       │   ├── kickoff.py
│       │   ├── research.py
│       │   ├── brainstorm.py
│       │   ├── archive.py
│       │   ├── ask.py
│       │   ├── review.py
│       │   ├── health_check.py
│       │   ├── mocs.py
│       │   └── moc_review.py
│       └── utils/              # 工具函数 (本Part)
│           ├── __init__.py
│           ├── id_generator.py
│           ├── frontmatter.py
│           ├── check_env.py
│           └── templates.py    # Part 6
├── references/                 # 参考文档
│   ├── para-method.md
│   └── obsidian-cli-usage.md
└── tests/
    ├── conftest.py             # pytest配置和fixtures
    ├── test_config.py
    ├── test_utils/
    │   ├── test_id_generator.py
    │   ├── test_frontmatter.py
    │   └── test_check_env.py
    └── test_workflows/         # Part 3-4测试

注：模板文件存放在 Vault 的 99_模板/ 目录下，便于用户自定义修改。
```

---

## Task 1.1: 项目结构初始化

**Files:**
- Create: `pyproject.toml`
- Create: `src/obsidian_kb/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "obsidian-kb"
version = "1.0.0"
description = "Obsidian knowledge base management skill for AI agents"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your@email.com"}
]
dependencies = [
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "click>=8.0.0",
    "markdown-it-py>=3.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]

[project.scripts]
obsidian-kb = "obsidian_kb.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

- [ ] **Step 2: 创建 __init__.py**

```python
"""Obsidian Knowledge Base Management Skill.

提供 PARA 方法论的完整知识管理工作流实现。
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from obsidian_kb.config import Config, get_config
from obsidian_kb.utils.id_generator import generate_note_id
from obsidian_kb.utils.frontmatter import parse_frontmatter, extract_frontmatter
```

- [ ] **Step 3: 创建测试配置 conftest.py**

```python
"""pytest 配置和共享 fixtures."""
import pytest
import tempfile
import os
from pathlib import Path

@pytest.fixture
def temp_vault():
    """创建临时 Vault 目录用于测试."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = Path(tmpdir) / "vault"
        vault_path.mkdir(parents=True)

        # 创建 PARA 目录结构
        (vault_path / "00_收件箱").mkdir()
        (vault_path / "10_项目").mkdir()
        (vault_path / "20_领域").mkdir()
        (vault_path / "30_研究").mkdir()
        (vault_path / "40_知识库").mkdir()
        (vault_path / "40_知识库" / "moc").mkdir()
        (vault_path / "50_归档").mkdir()
        (vault_path / "99_模板").mkdir()
        (vault_path / "Daily").mkdir()
        (vault_path / "metadata").mkdir()

        yield vault_path

@pytest.fixture
def temp_config_file(temp_vault):
    """创建临时配置文件."""
    config_path = temp_vault.parent / "config.json"
    config_content = {
        "vault_path": str(temp_vault),
        "default_area": "编程",
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

    import json
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_content, f)

    yield config_path

@pytest.fixture
def sample_note_content():
    """示例笔记内容."""
    return """---
id: kb-20250330-143052-a3f9
title: Python 装饰器详解
type: knowledge
date: 2025-03-30
created: 2025-03-30 14:30
updated: 2025-03-30 14:30
tags: [Python, 装饰器, 编程]
status: 进行中
mocs:
  - "moc-编程"
---

# Python 装饰器详解

> 创建于 2025-03-30

---

## 什么是装饰器

装饰器是一种高阶函数，用于在不修改原函数代码的情况下扩展功能。

## 核心概念

### 函数作为参数

```python
def my_decorator(func):
    def wrapper():
        print("Before function call")
        func()
        print("After function call")
    return wrapper
```

## 相关笔记

- [[Python函数式编程]]
- [[asyncio核心概念]]
"""
```

- [ ] **Step 4: 验证项目结构**

Run: `ls -la src/obsidian_kb/ tests/`
Expected: 显示创建的目录结构

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/obsidian_kb/__init__.py tests/conftest.py
git commit -m "feat: initialize project structure for obsidian-kb skill"
```

---

## Task 1.2: 配置管理模块

**Files:**
- Create: `src/obsidian_kb/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: 编写配置测试**

```python
"""配置管理模块测试."""
import pytest
import json
from pathlib import Path
from obsidian_kb.config import Config, get_config, DEFAULT_CONFIG_PATH


class TestConfig:
    """Config 类测试."""

    def test_config_from_dict(self, temp_config_file):
        """测试从字典创建配置."""
        with open(temp_config_file, "r", encoding="utf-8") as f:
            config_dict = json.load(f)

        config = Config.from_dict(config_dict)

        assert config.vault_path == Path(config_dict["vault_path"])
        assert config.default_area == "编程"
        assert config.auto_confirm_threshold == 0.8

    def test_config_validation_missing_vault_path(self):
        """测试缺少 vault_path 时验证失败."""
        invalid_config = {
            "default_area": "编程",
        }

        with pytest.raises(ValueError, match="vault_path is required"):
            Config.from_dict(invalid_config)

    def test_config_validation_invalid_threshold(self):
        """测试无效的置信度阈值."""
        invalid_config = {
            "vault_path": "/tmp/vault",
            "auto_confirm_threshold": 1.5,  # 超出范围
        }

        with pytest.raises(ValueError, match="auto_confirm_threshold must be between 0 and 1"):
            Config.from_dict(invalid_config)

    def test_config_vault_path_not_exists(self):
        """测试 vault_path 不存在时抛出错误."""
        config = Config(
            vault_path=Path("/nonexistent/vault"),
            default_area="编程",
            quiet_mode=False,
            auto_confirm_threshold=0.8,
            auto_confirm_actions=["moc_link"],
            templates={}
        )

        with pytest.raises(FileNotFoundError, match="Vault path does not exist"):
            config.validate_vault_path()

    def test_config_templates_path(self, temp_vault):
        """测试模板路径解析."""
        config = Config(
            vault_path=temp_vault,
            default_area="编程",
            quiet_mode=False,
            auto_confirm_threshold=0.8,
            auto_confirm_actions=["moc_link"],
            templates={
                "project": "99_模板/项目启动模板.md"
            }
        )

        template_path = config.get_template_path("project")
        assert template_path == temp_vault / "99_模板" / "项目启动模板.md"

    def test_get_config_singleton(self, temp_config_file):
        """测试 get_config 返回单例."""
        # 设置环境变量指向临时配置文件
        import os
        os.environ["OBSIDIAN_KB_CONFIG"] = str(temp_config_file)

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2  # 应该是同一个实例

        # 清理环境变量
        del os.environ["OBSIDIAN_KB_CONFIG"]

    def test_get_config_first_run_creates_default(self):
        """测试首次运行时创建默认配置."""
        # 使用临时目录作为配置路径
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            os.environ["OBSIDIAN_KB_CONFIG_DIR"] = tmpdir

            # 清除任何已存在的单例
            from obsidian_kb import config as config_module
            config_module._config_instance = None

            # get_config 应该提示用户配置 vault_path
            with pytest.raises(ValueError, match="Configuration file not found"):
                get_config()

            del os.environ["OBSIDIAN_KB_CONFIG_DIR"]
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_config.py -v`
Expected: FAIL - 模块未找到

- [ ] **Step 3: 实现配置管理模块**

```python
"""配置管理模块.

管理 Obsidian Vault 路径、用户偏好设置等配置。
配置文件位置: ~/.config/obsidian-kb/config.json
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator


# 配置文件默认路径
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "obsidian-kb"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.json"


class Config(BaseModel):
    """Obsidian KB 配置模型."""

    vault_path: Path = Field(..., description="Obsidian Vault 的绝对路径")
    default_area: str = Field(default="未分类", description="默认领域分类")
    quiet_mode: bool = Field(default=False, description="静默模式，减少输出")
    auto_confirm_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="自动执行的置信度阈值 (0-1)"
    )
    auto_confirm_actions: List[str] = Field(
        default_factory=lambda: ["moc_link", "tag_extraction"],
        description="允许自动执行的操作列表"
    )
    templates: Dict[str, str] = Field(
        default_factory=dict,
        description="模板文件路径映射"
    )

    @field_validator('vault_path')
    @classmethod
    def validate_vault_path(cls, v: Path) -> Path:
        """验证 vault_path 是否存在."""
        if not v.exists():
            raise FileNotFoundError(f"Vault path does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Vault path must be a directory: {v}")
        return v

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """从字典创建配置实例."""
        # 验证必填字段
        if "vault_path" not in data:
            raise ValueError("vault_path is required in configuration")

        # 验证阈值范围
        threshold = data.get("auto_confirm_threshold", 0.8)
        if not 0 <= threshold <= 1:
            raise ValueError("auto_confirm_threshold must be between 0 and 1")

        return cls(**data)

    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """从 JSON 文件加载配置."""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls.from_dict(data)

    def to_file(self, config_path: Path) -> None:
        """保存配置到 JSON 文件."""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "vault_path": str(self.vault_path),
            "default_area": self.default_area,
            "quiet_mode": self.quiet_mode,
            "auto_confirm_threshold": self.auto_confirm_threshold,
            "auto_confirm_actions": self.auto_confirm_actions,
            "templates": self.templates
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def validate_vault_structure(self) -> bool:
        """验证 Vault 目录结构是否符合 PARA 方法."""
        required_dirs = [
            "00_收件箱",
            "10_项目",
            "20_领域",
            "30_研究",
            "40_知识库",
            "50_归档",
            "99_模板",
            "Daily",
        ]

        missing = []
        for dir_name in required_dirs:
            if not (self.vault_path / dir_name).exists():
                missing.append(dir_name)

        if missing:
            raise ValueError(f"Missing required directories in vault: {missing}")

        return True

    def get_template_path(self, template_type: str) -> Path:
        """获取模板文件的完整路径."""
        template_rel_path = self.templates.get(template_type)
        if template_rel_path:
            return self.vault_path / template_rel_path
        return self.vault_path / "99_模板" / f"{template_type}模板.md"


# 全局配置实例（单例模式）
_config_instance: Optional[Config] = None


def get_config(config_path: Optional[Path] = None) -> Config:
    """获取配置实例（单例模式）.

    如果配置文件不存在，会提示用户配置 vault_path。

    Args:
        config_path: 可选的配置文件路径，默认使用 ~/.config/obsidian-kb/config.json

    Returns:
        Config 实例
    """
    global _config_instance

    if _config_instance is not None:
        return _config_instance

    # 确定配置文件路径
    if config_path is None:
        # 检查环境变量
        env_config = os.environ.get("OBSIDIAN_KB_CONFIG")
        if env_config:
            config_path = Path(env_config)
        else:
            config_path = DEFAULT_CONFIG_PATH

    # 加载配置
    try:
        _config_instance = Config.from_file(config_path)
        return _config_instance
    except FileNotFoundError:
        raise ValueError(
            f"Configuration file not found at {config_path}\n"
            "Please create a config.json file with your vault_path:\n"
            "{\n"
            "  \"vault_path\": \"/path/to/your/ObsidianVault\"\n"
            "}\n"
        )


def reset_config() -> None:
    """重置配置实例（用于测试）."""
    global _config_instance
    _config_instance = None
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_config.py -v`
Expected: PASS - 所有测试通过

- [ ] **Step 5: Commit**

```bash
git add src/obsidian_kb/config.py tests/test_config.py
git commit -m "feat: implement configuration management module"
```

---

## Task 1.3: 环境依赖检查模块

**Files:**
- Create: `src/obsidian_kb/utils/check_env.py`
- Create: `tests/test_utils/test_check_env.py`

- [ ] **Step 1: 编写环境检查测试**

```python
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

    def test_check_dependencies_all_ok(self, temp_config_file):
        """测试所有依赖检查通过."""
        with patch('obsidian_kb.utils.check_env.check_obsidian_cli') as mock_obsidian:
            mock_obsidian.return_value = {'available': True, 'version': '1.0'}

        with patch('obsidian_kb.config.get_config') as mock_config:
            from obsidian_kb.config import Config
            mock_config.return_value = Config(
                vault_path=Path("/tmp/vault"),
                default_area="编程"
            )

        result = check_dependencies()
        assert result['success'] is True
        assert len(result['issues']) == 0

    def test_check_dependencies_with_issues(self):
        """测试依赖检查发现问题."""
        with patch('obsidian_kb.utils.check_env.check_obsidian_cli') as mock_obsidian:
            mock_obsidian.return_value = {'available': False, 'error': 'not found'}

        result = check_dependencies()
        assert result['success'] is False
        assert len(result['issues']) > 0
        assert 'obsidian' in result['install_instructions'][0]

    def test_check_dependencies_raises_on_critical_missing(self):
        """测试关键依赖缺失时抛出错误."""
        with patch('obsidian_kb.utils.check_env.check_obsidian_cli') as mock_obsidian:
            mock_obsidian.return_value = {'available': False, 'error': 'not found'}

        with pytest.raises(RuntimeError, match="Critical dependencies missing"):
            check_dependencies(raise_on_error=True)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_utils/test_check_env.py -v`
Expected: FAIL - 模块未找到

- [ ] **Step 3: 创建 utils 包初始化文件**

```python
"""工具函数模块."""
from obsidian_kb.utils.id_generator import generate_note_id, NoteId
from obsidian_kb.utils.frontmatter import parse_frontmatter, extract_frontmatter, update_frontmatter
from obsidian_kb.utils.check_env import check_dependencies, check_obsidian_cli
```

- [ ] **Step 4: 实现环境检查模块**

```python
"""环境依赖检查模块.

检查系统依赖：
- obsidian CLI 工具
- Vault 路径配置

注意：yq/jq 不需要检查，Python 有内置的 pyyaml 和 json 库。
"""
import shutil
import subprocess
from typing import List, Dict, Optional


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
            'path': str(config.vault_path),
            'structure_valid': config.validate_vault_structure()
        }
    except ValueError as e:
        return {
            'configured': False,
            'error': str(e)
        }
    except FileNotFoundError as e:
        return {
            'configured': False,
            'error': f"Vault path not found: {e}"
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
        print("✅ 所有依赖检查通过")
        print(f"   Vault 路径: {result['vault']['path']}")
        print(f"   Obsidian CLI: {result['obsidian']['version']}")
        print(f"   可用工具: {', '.join(result['tools']['available'])}")
    else:
        print("❌ 发现问题:")
        for issue in result['issues']:
            print(f"   - {issue}")

        if result['install_instructions']:
            print("\n安装指南:")
            for instruction in result['install_instructions']:
                print(f"   {instruction}")

    print("=" * 50)
```

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest tests/test_utils/test_check_env.py -v`
Expected: PASS - 所有测试通过

- [ ] **Step 6: Commit**

```bash
git add src/obsidian_kb/utils/__init__.py src/obsidian_kb/utils/check_env.py tests/test_utils/test_check_env.py
git commit -m "feat: implement environment dependency checking module"
```

---

## Task 1.4: ID生成器模块

**Files:**
- Create: `src/obsidian_kb/utils/id_generator.py`
- Create: `tests/test_utils/test_id_generator.py`

- [ ] **Step 1: 编写 ID 生成器测试**

```python
"""ID生成器模块测试."""
import pytest
from datetime import datetime
from obsidian_kb.utils.id_generator import generate_note_id, NoteId, parse_note_id


class TestIdGenerator:
    """ID生成器测试."""

    def test_generate_note_id_format(self):
        """测试生成的 ID 符合格式 kb-YYYYMMDD-HHMMSS-XXXX."""
        id_str = generate_note_id()

        # 验证格式
        assert id_str.startswith("kb-")
        parts = id_str.split("-")
        assert len(parts) == 4  # kb, YYYYMMDD, HHMMSS, XXXX

        # 验证日期部分
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 6  # HHMMSS
        assert len(parts[3]) == 4  # 随机码

    def test_generate_note_id_unique(self):
        """测试生成的 ID 在并发情况下唯一."""
        ids = [generate_note_id() for _ in range(100)]

        # 所有 ID 应该唯一
        assert len(ids) == len(set(ids))

    def test_generate_note_id_contains_current_date(self):
        """测试 ID 包含当前日期."""
        now = datetime.now()
        expected_date_part = now.strftime("%Y%m%d")

        id_str = generate_note_id()
        assert expected_date_part in id_str

    def test_note_id_class(self):
        """测试 NoteId 类."""
        id_str = "kb-20250330-143052-a3f9"
        note_id = NoteId.from_string(id_str)

        assert note_id.prefix == "kb"
        assert note_id.date == "20250330"
        assert note_id.time == "143052"
        assert note_id.random == "a3f9"
        assert str(note_id) == id_str

    def test_note_id_to_datetime(self):
        """测试 NoteId 转换为 datetime."""
        id_str = "kb-20250330-143052-a3f9"
        note_id = NoteId.from_string(id_str)

        dt = note_id.to_datetime()
        assert dt.year == 2025
        assert dt.month == 3
        assert dt.day == 30
        assert dt.hour == 14
        assert dt.minute == 30
        assert dt.second == 52

    def test_parse_note_id_valid(self):
        """测试解析有效的 ID."""
        id_str = "kb-20250330-143052-a3f9"
        note_id = parse_note_id(id_str)

        assert note_id is not None
        assert note_id.date == "20250330"

    def test_parse_note_id_invalid(self):
        """测试解析无效的 ID 返回 None."""
        invalid_ids = [
            "invalid-id",
            "kb-2025-14-30-a3f9",  # 格式错误
            "kb-20250330",  # 缺少部分
            "",
        ]

        for invalid_id in invalid_ids:
            assert parse_note_id(invalid_id) is None

    def test_note_id_sortable(self):
        """测试 ID 可按时间排序."""
        ids = [
            NoteId.from_string("kb-20250330-100000-a001"),
            NoteId.from_string("kb-20250330-143052-a3f9"),
            NoteId.from_string("kb-20250330-090000-b002"),
        ]

        sorted_ids = sorted(ids, key=lambda x: x.to_datetime())

        assert sorted_ids[0].time == "090000"
        assert sorted_ids[1].time == "100000"
        assert sorted_ids[2].time == "143052"

    def test_note_id_from_datetime(self):
        """测试从 datetime 创建 NoteId."""
        dt = datetime(2025, 3, 30, 14, 30, 52)
        note_id = NoteId.from_datetime(dt, random_code="test")

        assert note_id.date == "20250330"
        assert note_id.time == "143052"
        assert note_id.random == "test"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_utils/test_id_generator.py -v`
Expected: FAIL - 模块未找到

- [ ] **Step 3: 实现 ID 生成器模块**

```python
"""笔记 ID 生成器模块.

生成唯一、可排序的笔记 ID。
格式: kb-YYYYMMDD-HHMMSS-XXXX (时间戳 + 4位随机码)

优势:
- 并发安全：无需读取现有文件
- 可排序：按时间顺序排列
- 简洁：固定长度，易于存储和引用
"""
import random
import string
from datetime import datetime
from typing import Optional
from dataclasses import dataclass


# ID 格式常量
ID_PREFIX = "kb"
ID_FORMAT = "{prefix}-{date}-{time}-{random}"
DATE_FORMAT = "%Y%m%d"
TIME_FORMAT = "%H%M%S"
RANDOM_LENGTH = 4


@dataclass
class NoteId:
    """笔记 ID 数据类."""

    prefix: str
    date: str  # YYYYMMDD
    time: str  # HHMMSS
    random: str  # 4位随机码

    @classmethod
    def from_string(cls, id_str: str) -> Optional["NoteId"]:
        """从字符串解析 ID.

        Args:
            id_str: 格式为 "kb-YYYYMMDD-HHMMSS-XXXX" 的字符串

        Returns:
            NoteId 实例，如果格式无效返回 None
        """
        parts = id_str.split("-")
        if len(parts) != 4:
            return None

        prefix, date, time, random_code = parts

        # 验证各部分格式
        if prefix != ID_PREFIX:
            return None
        if len(date) != 8 or not date.isdigit():
            return None
        if len(time) != 6 or not time.isdigit():
            return None
        if len(random_code) != RANDOM_LENGTH:
            return None

        return cls(prefix=prefix, date=date, time=time, random=random_code)

    @classmethod
    def from_datetime(cls, dt: datetime, random_code: Optional[str] = None) -> "NoteId":
        """从 datetime 创建 ID.

        Args:
            dt: datetime 实例
            random_code: 可选的随机码，默认自动生成

        Returns:
            NoteId 实例
        """
        if random_code is None:
            random_code = _generate_random_code()

        return cls(
            prefix=ID_PREFIX,
            date=dt.strftime(DATE_FORMAT),
            time=dt.strftime(TIME_FORMAT),
            random=random_code
        )

    def to_datetime(self) -> datetime:
        """转换为 datetime.

        Returns:
            datetime 实例（忽略随机码）
        """
        date_str = f"{self.date}{self.time}"
        return datetime.strptime(date_str, "%Y%m%d%H%M%S")

    def __str__(self) -> str:
        """转换为字符串格式."""
        return ID_FORMAT.format(
            prefix=self.prefix,
            date=self.date,
            time=self.time,
            random=self.random
        )

    def __repr__(self) -> str:
        return f"NoteId('{str(self)}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, NoteId):
            return False
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))


def _generate_random_code(length: int = RANDOM_LENGTH) -> str:
    """生成随机码.

    使用小写字母和数字，避免混淆字符（0/o, 1/l）。

    Args:
        length: 随机码长度

    Returns:
        随机字符串
    """
    # 使用不含混淆字符的字符集
    chars = string.ascii_lowercase.replace('o', '') + string.digits.replace('0', '').replace('1', '')
    return ''.join(random.choices(chars, k=length))


def generate_note_id(dt: Optional[datetime] = None) -> str:
    """生成唯一的笔记 ID.

    Args:
        dt: 可选的 datetime，默认使用当前时间

    Returns:
        格式为 "kb-YYYYMMDD-HHMMSS-XXXX" 的字符串
    """
    if dt is None:
        dt = datetime.now()

    note_id = NoteId.from_datetime(dt)
    return str(note_id)


def parse_note_id(id_str: str) -> Optional[NoteId]:
    """解析笔记 ID.

    Args:
        id_str: ID 字符串

    Returns:
        NoteId 实例，如果格式无效返回 None
    """
    return NoteId.from_string(id_str)


def is_valid_note_id(id_str: str) -> bool:
    """检查 ID 是否有效.

    Args:
        id_str: ID 字符串

    Returns:
        True 如果格式有效
    """
    return parse_note_id(id_str) is not None
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_utils/test_id_generator.py -v`
Expected: PASS - 所有测试通过

- [ ] **Step 5: Commit**

```bash
git add src/obsidian_kb/utils/id_generator.py tests/test_utils/test_id_generator.py
git commit -m "feat: implement note ID generator module"
```

---

## Task 1.5: Frontmatter 解析器模块

**Files:**
- Create: `src/obsidian_kb/utils/frontmatter.py`
- Create: `tests/test_utils/test_frontmatter.py`

- [ ] **Step 1: 编写 Frontmatter 解析器测试**

```python
"""Frontmatter 解析器模块测试."""
import pytest
from datetime import datetime
from obsidian_kb.utils.frontmatter import (
    parse_frontmatter,
    extract_frontmatter,
    update_frontmatter,
    create_frontmatter,
    Frontmatter
)


class TestFrontmatter:
    """Frontmatter 解析器测试."""

    def test_parse_frontmatter_valid(self, sample_note_content):
        """测试解析有效的 frontmatter."""
        fm = parse_frontmatter(sample_note_content)

        assert fm is not None
        assert fm.id == "kb-20250330-143052-a3f9"
        assert fm.title == "Python 装饰器详解"
        assert fm.type == "knowledge"
        assert fm.date == "2025-03-30"
        assert "Python" in fm.tags
        assert fm.status == "进行中"

    def test_parse_frontmatter_missing(self):
        """测试缺少 frontmatter 的内容."""
        content = "# 没有 frontmatter 的笔记\n\n正文内容..."

        fm = parse_frontmatter(content)
        assert fm is None

    def test_parse_frontmatter_invalid_yaml(self):
        """测试无效的 YAML frontmatter."""
        content = """---
invalid: yaml: syntax
---

# 笔记内容
"""

        with pytest.raises(ValueError, match="Invalid YAML"):
            parse_frontmatter(content)

    def test_extract_frontmatter_with_content(self, sample_note_content):
        """测试提取 frontmatter 和正文."""
        fm, body = extract_frontmatter(sample_note_content)

        assert fm is not None
        assert fm.title == "Python 装饰器详解"
        assert "# Python 装饰器详解" in body
        assert "什么是装饰器" in body

    def test_extract_frontmatter_without(self):
        """测试没有 frontmatter 时的提取."""
        content = "# 纯正文笔记"

        fm, body = extract_frontmatter(content)

        assert fm is None
        assert body == content

    def test_create_frontmatter_project(self):
        """测试创建项目类型 frontmatter."""
        from obsidian_kb.utils.id_generator import generate_note_id

        fm = create_frontmatter(
            note_type="project",
            title="新项目",
            area="编程",
            date="2025-03-30"
        )

        assert fm.type == "project"
        assert fm.title == "新项目"
        assert fm.tags == ["项目", "编程"]
        assert fm.status == "进行中"
        assert fm.id.startswith("kb-")

    def test_create_frontmatter_research(self):
        """测试创建研究类型 frontmatter."""
        fm = create_frontmatter(
            note_type="research",
            title="研究主题",
            area="编程",
            date="2025-03-30"
        )

        assert fm.type == "research"
        assert fm.status == "进行中"
        assert "研究" in fm.tags

    def test_update_frontmatter_field(self, sample_note_content):
        """测试更新 frontmatter 字段."""
        fm, body = extract_frontmatter(sample_note_content)

        # 更新状态
        updated_content = update_frontmatter(
            sample_note_content,
            {"status": "已完成", "updated": "2025-03-31 10:00"}
        )

        new_fm = parse_frontmatter(updated_content)
        assert new_fm.status == "已完成"
        assert new_fm.updated == "2025-03-31 10:00"
        assert "# Python 装饰器详解" in updated_content  # 正文保留

    def test_update_frontmatter_add_new_field(self, sample_note_content):
        """测试添加新字段到 frontmatter."""
        updated_content = update_frontmatter(
            sample_note_content,
            {"new_field": "new value"}
        )

        fm = parse_frontmatter(updated_content)
        assert hasattr(fm, 'new_field')
        assert fm.new_field == "new value"

    def test_frontmatter_class_methods(self):
        """测试 Frontmatter 类方法."""
        fm = Frontmatter(
            id="kb-20250330-143052-a3f9",
            title="测试",
            type="knowledge",
            date="2025-03-30",
            created="2025-03-30 14:30",
            updated="2025-03-30 14:30",
            tags=["测试"],
            status="进行中"
        )

        # 转换为 YAML
        yaml_str = fm.to_yaml()
        assert "id: kb-20250330-143052-a3f9" in yaml_str
        assert "title: 测试" in yaml_str

        # 转换为字符串（完整 frontmatter）
        full_fm = str(fm)
        assert full_fm.startswith("---\n")
        assert full_fm.endswith("---\n")

    def test_frontmatter_to_dict(self):
        """测试 Frontmatter 转换为字典."""
        fm = Frontmatter(
            id="kb-20250330-143052-a3f9",
            title="测试",
            type="knowledge",
            date="2025-03-30",
            tags=["测试"]
        )

        data = fm.to_dict()
        assert isinstance(data, dict)
        assert data["id"] == "kb-20250330-143052-a3f9"
        assert data["title"] == "测试"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_utils/test_frontmatter.py -v`
Expected: FAIL - 模块未找到

- [ ] **Step 3: 实现 Frontmatter 解析器模块**

```python
"""Frontmatter 解析器模块.

处理 Obsidian 笔记的 YAML frontmatter：
- 解析 YAML 元数据
- 提取 frontmatter 和正文
- 更新 frontmatter 字段
- 创建标准化的 frontmatter

注意：使用精确替换而非全局正则，避免误伤代码块中的内容。
"""
import re
import yaml
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

from obsidian_kb.utils.id_generator import generate_note_id


# Frontmatter 边界标记
FM_START = "---\n"
FM_END = "---\n"


@dataclass
class Frontmatter:
    """笔记 Frontmatter 数据类。

    通用字段：id, title, type, date, created, updated, tags
    扩展字段（按类型）：
    - project/research: status, area, mocs
    - brainstorm: area, related_project
    - moc: area
    - daily-note: inbox_count, active_projects, todo_count
    - archive: status
    """

    # 通用字段
    id: str
    title: str
    type: str  # daily-note | project | research | brainstorm | moc | archive
    date: str
    created: Optional[str] = None
    updated: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    # 扩展字段（按类型使用）
    status: Optional[str] = None  # 进行中 | 已完成 | 已归档 | 待处理
    area: Optional[str] = None    # 所属领域
    mocs: List[str] = field(default_factory=list)  # 关联的 MOC
    related_project: Optional[str] = None  # 关联的项目（brainstorm）
    inbox_count: Optional[int] = None      # 收件箱数量（daily-note）
    active_projects: Optional[int] = None  # 进行中项目数（daily-note）
    todo_count: Optional[int] = None       # 待办数量（daily-note）

    # 允许其他额外字段
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        data = {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "date": self.date,
            "created": self.created,
            "updated": self.updated,
            "tags": self.tags,
            "status": self.status,
            "area": self.area,
            "mocs": self.mocs,
            "related_project": self.related_project,
            "inbox_count": self.inbox_count,
            "active_projects": self.active_projects,
            "todo_count": self.todo_count,
        }
        # 合并额外字段
        data.update(self.extra)
        # 移除 None 值
        return {k: v for k, v in data.items() if v is not None}

    def to_yaml(self) -> str:
        """转换为 YAML 字符串."""
        data = self.to_dict()
        return yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)

    def __str__(self) -> str:
        """转换为完整的 frontmatter 块."""
        return FM_START + self.to_yaml() + FM_END

    def get(self, key: str, default: Any = None) -> Any:
        """获取字段值."""
        if hasattr(self, key):
            return getattr(self, key)
        return self.extra.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置字段值."""
        if hasattr(self, key) and key not in ['extra']:
            setattr(self, key, value)
        else:
            self.extra[key] = value


def find_frontmatter_bounds(content: str) -> Tuple[Optional[int], Optional[int]]:
    """找到 frontmatter 的边界位置.

    Args:
        content: 文件内容

    Returns:
        (start_index, end_index) tuple，如果不存在返回 (None, None)
    """
    # 必须以 --- 开头
    if not content.startswith(FM_START):
        return None, None

    # 找到结束的 ---
    # 注意：需要找到第二个 ---，而不是第一个（第一个是开始标记）
    lines = content.split('\n')

    end_line = None
    for i in range(1, len(lines)):  # 从第1行开始（跳过开始的 ---）
        if lines[i] == "---":
            end_line = i
            break

    if end_line is None:
        return None, None

    # 计算字符位置
    start_index = 0
    end_index = sum(len(lines[j]) + 1 for j in range(end_line + 1))  # +1 for newline

    return start_index, end_index


def parse_frontmatter(content: str) -> Optional[Frontmatter]:
    """解析内容中的 frontmatter.

    Args:
        content: 文件内容

    Returns:
        Frontmatter 实例，如果不存在返回 None

    Raises:
        ValueError: YAML 格式无效时
    """
    start, end = find_frontmatter_bounds(content)

    if start is None or end is None:
        return None

    # 提取 YAML 部分
    yaml_content = content[start + len(FM_START):end - len(FM_END)]

    try:
        data = yaml.safe_load(yaml_content)
        if not isinstance(data, dict):
            raise ValueError("Frontmatter must be a YAML dictionary")

        # 标准字段
        standard_fields = [
            'id', 'title', 'type', 'date', 'created', 'updated', 'tags',
            'status', 'area', 'mocs', 'related_project',
            'inbox_count', 'active_projects', 'todo_count'
        ]

        return Frontmatter(
            id=data.get('id', ''),
            title=data.get('title', ''),
            type=data.get('type', ''),
            date=data.get('date', ''),
            created=data.get('created'),
            updated=data.get('updated'),
            tags=data.get('tags', []),
            status=data.get('status'),
            area=data.get('area'),
            mocs=data.get('mocs', []),
            related_project=data.get('related_project'),
            inbox_count=data.get('inbox_count'),
            active_projects=data.get('active_projects'),
            todo_count=data.get('todo_count'),
            extra={k: v for k, v in data.items() if k not in standard_fields}
        )
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}")


def extract_frontmatter(content: str) -> Tuple[Optional[Frontmatter], str]:
    """提取 frontmatter 和正文.

    Args:
        content: 文件内容

    Returns:
        (Frontmatter, body) tuple，如果没有 frontmatter 返回 (None, content)
    """
    fm = parse_frontmatter(content)

    if fm is None:
        return None, content

    start, end = find_frontmatter_bounds(content)
    body = content[end:].strip()

    return fm, body


def update_frontmatter(content: str, updates: Dict[str, Any]) -> str:
    """更新 frontmatter 字段.

    使用精确替换策略，不修改正文内容。

    Args:
        content: 原文件内容
        updates: 要更新的字段字典

    Returns:
        更新后的完整内容
    """
    fm, body = extract_frontmatter(content)

    if fm is None:
        # 如果没有 frontmatter，创建一个新的
        fm = Frontmatter(
            id=generate_note_id(),
            title="",
            type="knowledge",
            date=datetime.now().strftime("%Y-%m-%d"),
            created=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

    # 应用更新
    for key, value in updates.items():
        fm.set(key, value)

    # 重新组装
    return str(fm) + "\n" + body


def create_frontmatter(
    note_type: str,
    title: str,
    area: str = None,
    date: str = None,
    status: str = "进行中",
    mocs: List[str] = None,
    related_project: str = None,
    inbox_count: int = 0,
    active_projects: int = 0,
    todo_count: int = 0,
    **extra_fields
) -> Frontmatter:
    """创建标准化的 frontmatter.

    Args:
        note_type: 笔记类型 (daily-note | project | research | brainstorm | moc | archive)
        title: 标题
        area: 领域分类 (project, research, brainstorm, moc 使用)
        date: 日期（默认今天）
        status: 状态 (project, research 使用)
        mocs: 关联的 MOC 列表 (project, research 使用)
        related_project: 关联的项目 (brainstorm 使用)
        inbox_count: 收件箱数量 (daily-note 使用)
        active_projects: 进行中项目数 (daily-note 使用)
        todo_count: 待办数量 (daily-note 使用)
        **extra_fields: 额外字段

    Returns:
        Frontmatter 实例
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    now = datetime.now()
    created = now.strftime("%Y-%m-%d %H:%M")

    # 根据类型设置默认标签
    type_tags = {
        "project": ["项目", area] if area else ["项目"],
        "research": ["研究", area] if area else ["研究"],
        "brainstorm": ["头脑风暴", area] if area else ["头脑风暴"],
        "daily-note": ["每日规划"],
        "moc": ["MOC", area] if area else ["MOC"],
        "archive": ["已归档", area] if area else ["已归档"],
    }

    tags = type_tags.get(note_type, [area] if area else [])

    # 默认 MOC 链接
    if mocs is None and area and note_type in ["project", "research"]:
        mocs = [f"moc-{area}"]

    # archive 类型状态固定为已归档
    if note_type == "archive":
        status = "已归档"

    # daily-note 不需要 updated 字段
    updated = None if note_type == "daily-note" else created

    return Frontmatter(
        id=generate_note_id(),
        title=title,
        type=note_type,
        date=date,
        created=created,
        updated=updated,
        tags=tags,
        status=status if note_type in ["project", "research", "archive"] else None,
        area=area if note_type in ["project", "research", "brainstorm", "moc"] else None,
        mocs=mocs if note_type in ["project", "research"] else [],
        related_project=related_project if note_type == "brainstorm" else None,
        inbox_count=inbox_count if note_type == "daily-note" else None,
        active_projects=active_projects if note_type == "daily-note" else None,
        todo_count=todo_count if note_type == "daily-note" else None,
        extra=extra_fields
    )


def add_tag(frontmatter: Frontmatter, tag: str) -> Frontmatter:
    """添加标签到 frontmatter.

    Args:
        frontmatter: Frontmatter 实例
        tag: 要添加的标签

    Returns:
        更新后的 Frontmatter
    """
    if tag not in frontmatter.tags:
        frontmatter.tags.append(tag)
    return frontmatter


def remove_tag(frontmatter: Frontmatter, tag: str) -> Frontmatter:
    """移除标签.

    Args:
        frontmatter: Frontmatter 实例
        tag: 要移除的标签

    Returns:
        更新后的 Frontmatter
    """
    frontmatter.tags = [t for t in frontmatter.tags if t != tag]
    return frontmatter
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_utils/test_frontmatter.py -v`
Expected: PASS - 所有测试通过

- [ ] **Step 5: Commit**

```bash
git add src/obsidian_kb/utils/frontmatter.py tests/test_utils/test_frontmatter.py
git commit -m "feat: implement frontmatter parser module"
```

---

## Part 1 完成检查清单

- [ ] 项目结构已初始化 (pyproject.toml, __init__.py, conftest.py)
- [ ] 配置管理模块完成 (config.py) - 支持单例、JSON加载、路径验证
- [ ] 环境依赖检查完成 (check_env.py) - 检测 obsidian CLI
- [ ] ID生成器完成 (id_generator.py) - kb-YYYYMMDD-HHMMSS-XXXX 格式
- [ ] Frontmatter解析器完成 (frontmatter.py) - 解析、提取、更新、创建

**下一步:** Part 2 将实现 Markdown AST 解析器和链接解析器。