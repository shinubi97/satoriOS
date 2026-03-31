"""工作流基类模块.

定义所有工作流的公共接口和返回类型。

重要：这个 skill 是给 AI Agent 用的，不是传统软件。
- 工作流代码**不处理交互**，只负责执行操作
- 所有需要的参数由 Agent 收集后传入
- 返回值清晰描述执行结果
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class WorkflowResult:
    """工作流执行结果.

    Attributes:
        success: 是否成功
        message: 给用户的简要消息
        created_files: 创建的文件路径列表
        modified_files: 修改的文件路径列表
        suggestions: 给 Agent 的建议（如"询问用户是否链接到 MOC"）
        data: 返回的结构化数据（如创建的笔记内容、找到的项目列表等）
    """
    success: bool
    message: str
    created_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    data: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        """返回简要描述。"""
        status = "✅" if self.success else "❌"
        files = ""
        if self.created_files:
            files += f"\n创建: {', '.join(self.created_files)}"
        if self.modified_files:
            files += f"\n修改: {', '.join(self.modified_files)}"
        suggestions = ""
        if self.suggestions:
            suggestions = f"\n💡 建议: {'; '.join(self.suggestions)}"
        return f"{status} {self.message}{files}{suggestions}"


class BaseWorkflow(ABC):
    """工作流基类.

    所有工作流继承此类，实现 execute 方法。

    注意：不包含交互逻辑。所有参数由 Agent 收集后传入。
    交互步骤在 SKILL.md 中描述，Agent 负责与用户沟通。

    Attributes:
        vault: Vault 操作实例
        config: 配置实例
    """

    def __init__(self, vault, config):
        """初始化工作流.

        Args:
            vault: Vault 操作实例
            config: 配置实例
        """
        self.vault = vault
        self.config = config

    @abstractmethod
    def execute(self, **kwargs) -> WorkflowResult:
        """执行工作流.

        Args 由 Agent 根据用户输入和 SKILL.md 说明收集。

        Returns:
            WorkflowResult 描述执行结果
        """
        pass

    def _ensure_area(self, area: Optional[str]) -> str:
        """确保 area 有值，使用配置中的默认值.

        Args:
            area: 用户指定的领域

        Returns:
            领域名称
        """
        if area:
            return area
        return self.config.default_area or "通用"

    def _generate_note_id(self) -> str:
        """生成笔记 ID.

        Returns:
            笔记 ID (格式: kb-YYYYMMDD-HHMMSS-XXXX)
        """
        from obsidian_kb.utils.id_generator import generate_note_id
        return generate_note_id()

    def _get_template_path(self, template_type: str) -> Optional[str]:
        """获取模板路径.

        Args:
            template_type: 模板类型 (project, research, brainstorm, daily, moc)

        Returns:
            模板文件路径（相对于 Vault 根目录），如果未配置则返回 None
        """
        if not self.config.templates:
            return None
        return self.config.templates.get(template_type)