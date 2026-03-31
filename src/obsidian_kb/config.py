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
    def validate_vault_path_field(cls, v: Path) -> Path:
        """验证 vault_path 字段是否存在且是目录."""
        if not v.exists():
            raise FileNotFoundError(f"Vault path does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Vault path must be a directory: {v}")
        return v

    def validate_vault_path(self) -> bool:
        """验证 vault_path 是否存在."""
        if not self.vault_path.exists():
            raise FileNotFoundError(f"Vault path does not exist: {self.vault_path}")
        if not self.vault_path.is_dir():
            raise ValueError(f"Vault path must be a directory: {self.vault_path}")
        return True

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

        # 将 vault_path 转换为 Path 对象
        data["vault_path"] = Path(data["vault_path"])

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