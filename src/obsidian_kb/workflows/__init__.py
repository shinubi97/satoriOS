"""工作流模块.

提供 PARA 方法论的各种工作流实现。
"""
from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult
from obsidian_kb.workflows.open import OpenWorkflow, NoteDetail

__all__ = ["BaseWorkflow", "WorkflowResult", "OpenWorkflow", "NoteDetail"]