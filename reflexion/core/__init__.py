"""核心模块 - 包含框架的主要组件"""

from reflexion.core.reflector import Reflector, ReflectionResult
from reflexion.core.executor import ExecutorAgent, ExecutionResult
from reflexion.core.orchestrator import ReflexionOrchestrator
from reflexion.core.base import BaseReflector, BaseExecutor

__all__ = [
    "BaseReflector",
    "BaseExecutor",
    "Reflector",
    "ReflectorAgent",
    "ExecutionResult",
    "ReflectionResult",
    "ExecutorAgent",
    "ReflexionOrchestrator",
]
