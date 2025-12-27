"""
Reflexion - LLM驱动的自我反思工具调用框架

基于 ReAct 和 Reflexion 模式，实现:
- 行动 -> 观察 -> 反思 -> 纠正 -> 再行动
- 智能工具调用与错误恢复
- 反思库与多智能体协作
"""

__version__ = "0.1.0"

from reflexion.core.orchestrator import ReflexionOrchestrator
from reflexion.core.reflector import Reflector
from reflexion.core.executor import ExecutorAgent
from reflexion.memory.context_manager import ContextManager
from reflexion.tools.tool_registry import ToolRegistry
from reflexion.agents.collaboration import CollaborativeAgents
from reflexion.agents.specialized import PlannerAgent, CriticAgent

__all__ = [
    # 核心编排器
    "ReflexionOrchestrator",
    # 核心组件
    "Reflector",
    "ExecutorAgent",
    # 记忆管理
    "ContextManager",
    # 工具管理
    "ToolRegistry",
    # 多智能体
    "CollaborativeAgents",
    "PlannerAgent",
    "CriticAgent",
]
