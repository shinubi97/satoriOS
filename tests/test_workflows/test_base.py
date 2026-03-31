"""工作流基类测试."""
import pytest
from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult


class TestWorkflowResult:
    """WorkflowResult 测试."""

    def test_success_result(self):
        """测试成功结果。"""
        result = WorkflowResult(
            success=True,
            message="操作成功",
            created_files=["test.md"],
            suggestions=["下一步建议"]
        )

        assert result.success is True
        assert result.message == "操作成功"
        assert result.created_files == ["test.md"]
        assert "下一步建议" in result.suggestions

    def test_failure_result(self):
        """测试失败结果。"""
        result = WorkflowResult(
            success=False,
            message="操作失败"
        )

        assert result.success is False
        assert "❌" in str(result)

    def test_str_representation(self):
        """测试字符串表示。"""
        result = WorkflowResult(
            success=True,
            message="测试成功",
            created_files=["a.md", "b.md"],
            modified_files=["c.md"],
            suggestions=["建议1", "建议2"]
        )

        result_str = str(result)
        assert "✅" in result_str
        assert "测试成功" in result_str
        assert "a.md" in result_str
        assert "建议1" in result_str

    def test_default_values(self):
        """测试默认值。"""
        result = WorkflowResult(
            success=True,
            message="OK"
        )

        assert result.created_files == []
        assert result.modified_files == []
        assert result.suggestions == []
        assert result.data is None


class ConcreteWorkflow(BaseWorkflow):
    """用于测试的具体工作流实现。"""

    def execute(self, **kwargs) -> WorkflowResult:
        """测试执行方法。"""
        action = kwargs.get("action", "default")

        if action == "fail":
            return WorkflowResult(
                success=False,
                message="执行失败"
            )

        return WorkflowResult(
            success=True,
            message=f"执行成功: {action}",
            created_files=["new_note.md"],
            suggestions=["下一步操作"]
        )


class TestBaseWorkflow:
    """BaseWorkflow 测试."""

    def test_workflow_init(self, temp_vault, temp_config_file):
        """测试工作流初始化。"""
        from obsidian_kb.vault import Vault
        from obsidian_kb.config import Config

        config = Config.from_file(temp_config_file)
        vault = Vault(config.vault_path)

        workflow = ConcreteWorkflow(vault, config)

        assert workflow.vault is vault
        assert workflow.config is config

    def test_execute_success(self, temp_vault, temp_config_file):
        """测试成功执行。"""
        from obsidian_kb.vault import Vault
        from obsidian_kb.config import Config

        config = Config.from_file(temp_config_file)
        vault = Vault(config.vault_path)
        workflow = ConcreteWorkflow(vault, config)

        result = workflow.execute(action="test")

        assert result.success is True
        assert "test" in result.message

    def test_execute_failure(self, temp_vault, temp_config_file):
        """测试失败执行。"""
        from obsidian_kb.vault import Vault
        from obsidian_kb.config import Config

        config = Config.from_file(temp_config_file)
        vault = Vault(config.vault_path)
        workflow = ConcreteWorkflow(vault, config)

        result = workflow.execute(action="fail")

        assert result.success is False
        assert result.message == "执行失败"