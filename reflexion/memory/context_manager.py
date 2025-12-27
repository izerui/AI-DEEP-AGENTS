"""上下文管理器 - 管理执行历史和上下文"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    FINAL = "final"


@dataclass
class MemoryEntry:
    """记忆条目"""
    step_number: int
    timestamp: datetime
    action: str
    tool_name: Optional[str]
    tool_input: Optional[Dict[str, Any]]
    observation: str
    reflection: Optional[str]
    status: StepStatus
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "step_number": self.step_number,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "observation": self.observation,
            "reflection": self.reflection,
            "status": self.status.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """从字典创建"""
        return cls(
            step_number=data["step_number"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            action=data["action"],
            tool_name=data.get("tool_name"),
            tool_input=data.get("tool_input"),
            observation=data["observation"],
            reflection=data.get("reflection"),
            status=StepStatus(data["status"]),
            metadata=data.get("metadata", {}),
        )


class ContextManager:
    """
    上下文管理器

    功能：
    - 管理执行历史
    - 维护任务上下文
    - 提供历史查询
    - 支持持久化
    - 防止死循环
    """

    def __init__(
        self,
        max_steps: int = 20,
        max_history: int = 100,
        enable_persistence: bool = False,
        persistence_path: Optional[str] = None,
    ):
        """
        初始化上下文管理器

        Args:
            max_steps: 最大执行步数（防止死循环）
            max_history: 最大历史记录数
            enable_persistence: 是否启用持久化
            persistence_path: 持久化文件路径
        """
        self.max_steps = max_steps
        self.max_history = max_history
        self.enable_persistence = enable_persistence
        self.persistence_path = persistence_path or "reflexion_history.json"

        self.task: Optional[str] = None
        self.history: List[MemoryEntry] = []
        self.current_step = 0
        self.metadata: Dict[str, Any] = {}

        # 统计信息
        self.stats = {
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "tool_usage": {},
        }

    def start_task(self, task: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        开始新任务

        Args:
            task: 任务描述
            metadata: 任务元数据
        """
        self.task = task
        self.history = []
        self.current_step = 0
        self.metadata = metadata or {}
        self.stats = {
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "tool_usage": {},
        }

    def add_step(
        self,
        action: str,
        observation: str,
        tool_name: Optional[str] = None,
        tool_input: Optional[Dict[str, Any]] = None,
        reflection: Optional[str] = None,
        status: StepStatus = StepStatus.SUCCESS,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryEntry:
        """
        添加执行步骤

        Args:
            action: 执行的动作
            observation: 观察结果
            tool_name: 使用的工具
            tool_input: 工具输入
            reflection: 反思内容
            status: 步骤状态
            metadata: 额外元数据

        Returns:
            创建的记忆条目
        """
        self.current_step += 1

        entry = MemoryEntry(
            step_number=self.current_step,
            timestamp=datetime.now(),
            action=action,
            tool_name=tool_name,
            tool_input=tool_input,
            observation=observation,
            reflection=reflection,
            status=status,
            metadata=metadata or {},
        )

        self.history.append(entry)

        # 更新统计
        self.stats["total_steps"] += 1
        if status == StepStatus.SUCCESS:
            self.stats["successful_steps"] += 1
        elif status == StepStatus.FAILED:
            self.stats["failed_steps"] += 1

        if tool_name:
            self.stats["tool_usage"][tool_name] = \
                self.stats["tool_usage"].get(tool_name, 0) + 1

        # 限制历史大小
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        return entry

    def get_history(
        self,
        last_n: Optional[int] = None,
        status: Optional[StepStatus] = None,
    ) -> List[MemoryEntry]:
        """
        获取历史记录

        Args:
            last_n: 只返回最近N条
            status: 筛选状态

        Returns:
            历史记录列表
        """
        history = self.history

        if status:
            history = [e for e in history if e.status == status]

        if last_n:
            history = history[-last_n:]

        return history

    def get_last_entry(self) -> Optional[MemoryEntry]:
        """获取最后一条记录"""
        return self.history[-1] if self.history else None

    def get_failed_steps(self) -> List[MemoryEntry]:
        """获取所有失败的步骤"""
        return [e for e in self.history if e.status == StepStatus.FAILED]

    def should_stop(self) -> bool:
        """
        判断是否应该停止（防止死循环）

        Returns:
            是否应该停止
        """
        if self.current_step >= self.max_steps:
            return True

        # 检查是否陷入循环（最近N步完全相同）
        if len(self.history) >= 3:
            last_three = self.history[-3:]
            if (
                len(set(e.action for e in last_three)) == 1 and
                len(set(e.observation for e in last_three)) == 1
            ):
                return True

        return False

    def get_context_summary(self) -> str:
        """
        获取上下文摘要

        Returns:
            上下文摘要字符串
        """
        lines = [
            f"任务: {self.task or '无'}",
            f"当前步骤: {self.current_step}/{self.max_steps}",
            f"成功步骤: {self.stats['successful_steps']}",
            f"失败步骤: {self.stats['failed_steps']}",
        ]

        if self.stats["tool_usage"]:
            lines.append("\n工具使用统计:")
            for tool, count in self.stats["tool_usage"].items():
                lines.append(f"  - {tool}: {count}次")

        return "\n".join(lines)

    def format_for_reflection(self, last_n: int = 5) -> str:
        """
        格式化为反思提示词

        Args:
            last_n: 包含最近N步

        Returns:
            格式化的历史字符串
        """
        recent_history = self.get_history(last_n=last_n)

        if not recent_history:
            return "无历史记录"

        lines = []
        for entry in recent_history:
            status_icon = {
                StepStatus.SUCCESS: "✓",
                StepStatus.FAILED: "✗",
                StepStatus.RUNNING: "→",
                StepStatus.PENDING: "○",
                StepStatus.FINAL: "■",
            }.get(entry.status, "?")

            lines.append(f"{status_icon} 步骤{entry.step_number}: {entry.action}")

            if entry.tool_name:
                lines.append(f"    工具: {entry.tool_name}")

            lines.append(f"    观察: {entry.observation[:100]}...")

            if entry.reflection:
                lines.append(f"    反思: {entry.reflection[:100]}...")

        return "\n".join(lines)

    def save(self) -> None:
        """保存历史到文件"""
        if not self.enable_persistence:
            return

        data = {
            "task": self.task,
            "current_step": self.current_step,
            "metadata": self.metadata,
            "stats": self.stats,
            "history": [entry.to_dict() for entry in self.history],
        }

        with open(self.persistence_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self) -> None:
        """从文件加载历史"""
        if not self.enable_persistence:
            return

        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.task = data.get("task")
            self.current_step = data.get("current_step", 0)
            self.metadata = data.get("metadata", {})
            self.stats = data.get("stats", {})
            self.history = [
                MemoryEntry.from_dict(entry_data)
                for entry_data in data.get("history", [])
            ]

        except FileNotFoundError:
            pass

    def clear(self) -> None:
        """清空历史"""
        self.history = []
        self.current_step = 0
        self.stats = {
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "tool_usage": {},
        }

    def export(self) -> Dict[str, Any]:
        """导出上下文数据"""
        return {
            "task": self.task,
            "current_step": self.current_step,
            "metadata": self.metadata,
            "stats": self.stats,
            "history": [entry.to_dict() for entry in self.history],
        }

    def __len__(self) -> int:
        """返回历史记录数"""
        return len(self.history)

    def __repr__(self) -> str:
        """字符串表示"""
        return f"ContextManager(task={self.task!r}, steps={self.current_step})"
