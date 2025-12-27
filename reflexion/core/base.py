"""基础抽象类定义"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class StepResult:
    """单步执行结果"""
    step_number: int
    action: str
    tool_name: Optional[str]
    tool_input: Optional[Dict[str, Any]]
    observation: str
    reflection: Optional[str]
    is_success: bool
    is_final: bool


class BaseReflector(ABC):
    """反思者基类"""

    @abstractmethod
    async def reflect(
        self,
        task: str,
        action: str,
        observation: str,
        history: List[StepResult],
    ) -> str:
        """
        反思当前执行结果

        Args:
            task: 原始任务描述
            action: 执行的动作
            observation: 观察到的结果
            history: 历史步骤

        Returns:
            反思内容和建议
        """
        pass

    @abstractmethod
    async def should_continue(self, reflection: str, observation: str) -> bool:
        """
        判断是否应该继续执行

        Args:
            reflection: 反思内容
            observation: 观察结果

        Returns:
            是否继续
        """
        pass


class BaseExecutor(ABC):
    """执行者基类"""

    @abstractmethod
    async def decide_action(
        self,
        task: str,
        observation: Optional[str],
        reflection: Optional[str],
        history: List[StepResult],
    ) -> tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        """
        决定下一步动作

        Args:
            task: 任务描述
            observation: 上一步的观察结果
            reflection: 上一步的反思
            history: 历史步骤

        Returns:
            (action_type, tool_name, tool_input)
        """
        pass
