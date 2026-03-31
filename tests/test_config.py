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
        # Pydantic validator 在构造时就会验证，所以错误在构造时抛出
        with pytest.raises(FileNotFoundError, match="Vault path does not exist"):
            Config(
                vault_path=Path("/nonexistent/vault"),
                default_area="编程",
                quiet_mode=False,
                auto_confirm_threshold=0.8,
                auto_confirm_actions=["moc_link"],
                templates={}
            )

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