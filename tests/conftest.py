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