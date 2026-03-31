"""模板管理模块测试."""
import pytest
from pathlib import Path
import tempfile

from obsidian_kb.templates import TemplateManager, TemplateContext
from obsidian_kb.config import Config


class TestTemplateManager:
    """TemplateManager 测试."""

    @pytest.fixture
    def config(self):
        """创建测试配置。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Config(vault_path=Path(tmpdir), default_area="测试")

    def test_init(self, config):
        """测试初始化。"""
        manager = TemplateManager(config)
        assert manager.config == config

    def test_get_builtin_template(self, config):
        """测试获取内置模板。"""
        manager = TemplateManager(config)

        template = manager.get_template("project")
        assert template is not None
        assert "{{ title }}" in template

    def test_get_builtin_research_template(self, config):
        """测试获取研究模板。"""
        manager = TemplateManager(config)

        template = manager.get_template("research")
        assert template is not None
        assert "研究笔记" in template

    def test_get_builtin_brainstorm_template(self, config):
        """测试获取头脑风暴模板。"""
        manager = TemplateManager(config)

        template = manager.get_template("brainstorm")
        assert template is not None
        assert "头脑风暴" in template

    def test_get_builtin_daily_template(self, config):
        """测试获取每日模板。"""
        manager = TemplateManager(config)

        template = manager.get_template("daily")
        assert template is not None
        assert "每日规划" in template

    def test_get_builtin_moc_template(self, config):
        """测试获取 MOC 模板。"""
        manager = TemplateManager(config)

        template = manager.get_template("moc")
        assert template is not None
        assert "MOC" in template

    def test_get_nonexistent_template(self, config):
        """测试获取不存在的模板。"""
        manager = TemplateManager(config)

        template = manager.get_template("nonexistent")
        assert template is None

    def test_render_template(self, config):
        """测试渲染模板。"""
        manager = TemplateManager(config)
        context = TemplateContext(
            title="测试项目",
            area="编程",
            variables={
                "id": "kb-20260331-100000-0001",
                "created": "2026-03-31",
                "updated": "2026-03-31",
                "timeline": "1个月",
                "source": "某个想法"
            }
        )

        result = manager.render("project", context)

        assert "测试项目" in result
        assert "编程" in result
        assert "1个月" in result
        assert "某个想法" in result

    def test_render_string(self, config):
        """测试渲染字符串。"""
        manager = TemplateManager(config)
        template = "# {{ title }}\n\n领域: {{ area }}"
        context = TemplateContext(title="测试", area="通用")

        result = manager.render_string(template, context)

        assert result == "# 测试\n\n领域: 通用"

    def test_render_with_list(self, config):
        """测试渲染包含列表的模板。"""
        manager = TemplateManager(config)
        template = "标签: {{ tags }}"
        context = TemplateContext(title="测试", tags=["标签1", "标签2"])

        result = manager.render_string(template, context)

        assert "标签1" in result
        assert "标签2" in result

    def test_list_templates(self, config):
        """测试列出模板。"""
        manager = TemplateManager(config)

        templates = manager.list_templates()

        assert len(templates) >= 4
        template_names = [t["name"] for t in templates]
        assert "project" in template_names
        assert "research" in template_names
        assert "brainstorm" in template_names

    def test_template_caching(self, config):
        """测试模板缓存。"""
        manager = TemplateManager(config)

        # 第一次加载
        template1 = manager.get_template("project")
        assert "project" in manager._cache

        # 第二次从缓存加载
        template2 = manager.get_template("project")
        assert template1 == template2

    def test_custom_template(self, config):
        """测试自定义模板。"""
        manager = TemplateManager(config)

        # 创建自定义模板
        custom_content = "# 自定义 {{ title }}"
        manager.create_custom_template("custom", custom_content)

        # 获取自定义模板
        template = manager.get_template("custom")
        assert template == custom_content

    def test_custom_template_overrides_builtin(self, config):
        """测试自定义模板覆盖内置模板。"""
        manager = TemplateManager(config)

        # 创建自定义项目模板
        custom_content = "# 自定义项目 {{ title }}"
        manager.create_custom_template("project", custom_content)

        # 获取模板应该是自定义的
        template = manager.get_template("project")
        assert "自定义项目" in template


class TestTemplateContext:
    """TemplateContext 测试."""

    def test_context_creation(self):
        """测试创建上下文。"""
        context = TemplateContext(
            title="测试标题",
            area="编程",
            date="2026-03-31",
            tags=["测试", "模板"]
        )

        assert context.title == "测试标题"
        assert context.area == "编程"
        assert context.date == "2026-03-31"
        assert len(context.tags) == 2

    def test_context_defaults(self):
        """测试上下文默认值。"""
        context = TemplateContext(title="测试")

        assert context.area == "通用"
        assert context.tags == []
        assert context.status == "活跃"

    def test_context_to_dict(self):
        """测试转换为字典。"""
        context = TemplateContext(
            title="测试",
            area="编程",
            variables={"custom": "value"}
        )

        d = context.to_dict()

        assert d["title"] == "测试"
        assert d["area"] == "编程"
        assert d["custom"] == "value"

    def test_context_variables(self):
        """测试额外变量。"""
        context = TemplateContext(
            title="测试",
            variables={
                "id": "kb-001",
                "timeline": "1个月"
            }
        )

        assert context.variables["id"] == "kb-001"
        assert context.variables["timeline"] == "1个月"