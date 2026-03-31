"""模板管理模块.

管理 Obsidian 笔记模板的加载、渲染和输出。
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, date
import re
import string

from obsidian_kb.config import Config


@dataclass
class TemplateContext:
    """模板渲染上下文。"""
    title: str
    area: str = "通用"
    date: str = field(default_factory=lambda: date.today().isoformat())
    tags: List[str] = field(default_factory=list)
    status: str = "活跃"
    # 额外变量
    variables: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        return {
            "title": self.title,
            "area": self.area,
            "date": self.date,
            "tags": self.tags,
            "status": self.status,
            **self.variables
        }


class TemplateManager:
    """模板管理器。

    负责加载、渲染和管理 Obsidian 笔记模板。
    """

    # 内置模板
    BUILTIN_TEMPLATES = {
        "project": "project.md",
        "research": "research.md",
        "brainstorm": "brainstorm.md",
        "daily": "daily.md",
        "moc": "moc.md"
    }

    def __init__(self, config: Config):
        """初始化模板管理器。

        Args:
            config: 配置对象
        """
        self.config = config
        self._templates_dir = Path(__file__).parent
        self._custom_templates_dir = config.vault_path / "templates" if config.vault_path else None
        self._cache: Dict[str, str] = {}

    def get_template(self, name: str) -> Optional[str]:
        """获取模板内容。

        先查找自定义模板，再查找内置模板。

        Args:
            name: 模板名称（不含扩展名）

        Returns:
            模板内容，如果未找到返回 None
        """
        # 检查缓存
        if name in self._cache:
            return self._cache[name]

        # 先查找自定义模板
        if self._custom_templates_dir:
            custom_path = self._custom_templates_dir / f"{name}.md"
            if custom_path.exists():
                content = custom_path.read_text(encoding="utf-8")
                self._cache[name] = content
                return content

        # 查找内置模板
        builtin_name = self.BUILTIN_TEMPLATES.get(name, f"{name}.md")
        builtin_path = self._templates_dir / builtin_name

        if builtin_path.exists():
            content = builtin_path.read_text(encoding="utf-8")
            self._cache[name] = content
            return content

        return None

    def list_templates(self) -> List[Dict[str, str]]:
        """列出所有可用模板。

        Returns:
            模板信息列表
        """
        templates = []

        # 内置模板
        for name, filename in self.BUILTIN_TEMPLATES.items():
            template_path = self._templates_dir / filename
            if template_path.exists():
                templates.append({
                    "name": name,
                    "type": "builtin",
                    "description": self._extract_description(template_path)
                })

        # 自定义模板
        if self._custom_templates_dir and self._custom_templates_dir.exists():
            for md_file in self._custom_templates_dir.glob("*.md"):
                name = md_file.stem
                templates.append({
                    "name": name,
                    "type": "custom",
                    "description": self._extract_description(md_file)
                })

        return templates

    def render(self, template_name: str, context: TemplateContext) -> str:
        """渲染模板。

        Args:
            template_name: 模板名称
            context: 渲染上下文

        Returns:
            渲染后的内容

        Raises:
            ValueError: 模板未找到
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")

        return self._render_template(template, context)

    def render_string(self, template: str, context: TemplateContext) -> str:
        """渲染模板字符串。

        Args:
            template: 模板字符串
            context: 渲染上下文

        Returns:
            渲染后的内容
        """
        return self._render_template(template, context)

    def _render_template(self, template: str, context: TemplateContext) -> str:
        """渲染模板。

        支持 {{ variable }} 和 {% if condition %}...{% endif %} 语法。

        Args:
            template: 模板内容
            context: 渲染上下文

        Returns:
            渲染后的内容
        """
        variables = context.to_dict()

        # 处理条件语句 {% if variable %}...{% endif %}
        def process_if(match):
            condition = match.group(1).strip()
            content = match.group(2)
            if condition in variables and variables[condition]:
                return content
            return ""

        template = re.sub(
            r'\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}',
            process_if,
            template,
            flags=re.DOTALL
        )

        # 处理变量 {{ variable }}
        def process_var(match):
            var_name = match.group(1).strip()
            value = variables.get(var_name, "")

            # 处理列表
            if isinstance(value, list):
                return ", ".join(str(v) for v in value)

            return str(value)

        template = re.sub(r'\{\{\s*(\w+)\s*\}\}', process_var, template)

        return template

    def _extract_description(self, template_path: Path) -> str:
        """从模板文件提取描述。

        模板描述在第一个注释行定义:
        <!-- description: 模板描述 -->

        Args:
            template_path: 模板文件路径

        Returns:
            描述文本
        """
        try:
            content = template_path.read_text(encoding="utf-8")
            match = re.search(r'<!--\s*description:\s*(.+?)\s*-->', content)
            if match:
                return match.group(1)
        except Exception:
            pass

        return ""

    def create_custom_template(self, name: str, content: str) -> Path:
        """创建自定义模板。

        Args:
            name: 模板名称
            content: 模板内容

        Returns:
            创建的模板文件路径
        """
        if not self._custom_templates_dir:
            raise ValueError("Custom templates directory not configured")

        self._custom_templates_dir.mkdir(parents=True, exist_ok=True)
        template_path = self._custom_templates_dir / f"{name}.md"
        template_path.write_text(content, encoding="utf-8")

        # 更新缓存
        self._cache[name] = content

        return template_path