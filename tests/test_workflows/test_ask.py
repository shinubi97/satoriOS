"""问答工作流测试."""
import pytest
from pathlib import Path

from obsidian_kb.workflows.ask import AskWorkflow, AskResult, SearchResult
from obsidian_kb.config import Config
from obsidian_kb.vault import Vault


class TestAskWorkflow:
    """AskWorkflow 测试."""

    @pytest.fixture
    def setup_vault(self, temp_vault_for_workflow):
        """设置测试 Vault。"""
        vault_path = temp_vault_for_workflow

        # 创建研究笔记
        research_path = vault_path / "30_研究" / "编程"
        research_path.mkdir(parents=True, exist_ok=True)
        (research_path / "Python学习_2026-03-01.md").write_text("""---
id: kb-20260301-100000-0001
title: Python学习 研究笔记
type: research
area: 编程
date: 2026-03-01
---

# Python学习 研究笔记

## 核心概念

Python 是一种高级编程语言，以简洁著称。

### 变量

Python 变量不需要声明类型。

### 函数

使用 def 关键字定义函数。
""")

        # 创建项目笔记
        projects_path = vault_path / "10_项目" / "编程"
        projects_path.mkdir(parents=True, exist_ok=True)
        (projects_path / "Web开发项目.md").write_text("""---
id: kb-20260301-100000-0002
title: Web开发项目
type: project
area: 编程
date: 2026-03-01
status: 进行中
---

# Web开发项目

使用 Python Flask 进行 Web 开发。

## 目标

- 学习 Flask 框架
- 构建简单网站
""")

        yield vault_path

    def test_execute_success(self, setup_vault):
        """测试成功搜索。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = AskWorkflow(vault, config)

        result = workflow.execute("Python 编程")

        assert result.success is True
        assert result.data["ask"] is not None

    def test_extract_keywords(self, setup_vault):
        """测试关键词提取。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = AskWorkflow(vault, config)

        keywords = workflow._extract_keywords("Python 编程入门怎么学习？")

        assert "python" in keywords
        # "编程入门怎么学习" 作为一个整体被提取，因为中间没有分隔符
        assert any("编程" in kw or "入门" in kw for kw in keywords)

    def test_search_notes(self, setup_vault):
        """测试搜索笔记。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = AskWorkflow(vault, config)

        results = workflow._search_notes(["python"], 5)

        assert len(results) >= 1
        assert results[0].relevance > 0

    def test_extract_snippet(self, setup_vault):
        """测试提取摘要。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = AskWorkflow(vault, config)

        content = "这是开头内容。Python 是一种编程语言，用于 Web 开发。这是结尾内容。"
        snippet = workflow._extract_snippet(content, "Python", 100)

        # 摘要应该包含关键词附近的内容
        assert "python" in snippet.lower() or "编程" in snippet

    def test_assess_confidence(self, setup_vault):
        """测试置信度评估。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = AskWorkflow(vault, config)

        high_conf = workflow._assess_confidence([
            SearchResult(path="a", title="a", relevance=0.8, snippet="a")
        ])
        assert high_conf == "high"

        low_conf = workflow._assess_confidence([
            SearchResult(path="a", title="a", relevance=0.1, snippet="a")
        ])
        assert low_conf == "low"

    def test_no_results(self, setup_vault):
        """测试没有结果。"""
        config = Config(vault_path=setup_vault)
        vault = Vault(setup_vault)
        workflow = AskWorkflow(vault, config)

        result = workflow.execute("完全不存在的关键词xyz123")

        assert result.success is True  # 搜索成功，但没有结果
        assert result.data["ask"].confidence == "low"


class TestSearchResult:
    """SearchResult 数据类测试。"""

    def test_result_creation(self):
        """测试创建搜索结果。"""
        result = SearchResult(
            path="30_研究/test.md",
            title="测试笔记",
            relevance=0.5,
            snippet="测试内容",
            highlights=["测试"]
        )

        assert result.path == "30_研究/test.md"
        assert result.relevance == 0.5
        assert "测试" in result.highlights


class TestAskResult:
    """AskResult 数据类测试。"""

    def test_result_creation(self):
        """测试创建问答结果。"""
        result = AskResult(
            question="Python 怎么学？",
            answer="建议从基础开始...",
            sources=[],
            confidence="medium"
        )

        assert result.question == "Python 怎么学？"
        assert result.confidence == "medium"