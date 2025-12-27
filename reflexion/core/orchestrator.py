"""主框架编排器 - 协调所有模块的执行流程"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from reflexion.core.base import StepResult
from reflexion.core.reflector import Reflector, ReflectorAgent, ReflectionResult
from reflexion.core.executor import ExecutorAgent, ExecutionResult
from reflexion.memory.context_manager import ContextManager, StepStatus
from reflexion.memory.reflection_library import ReflectionLibrary, ErrorType
from reflexion.tools.tool_registry import ToolRegistry


@dataclass
class OrchestratorConfig:
    """编排器配置"""
    max_steps: int = 20
    max_history: int = 100
    verbose: bool = False
    enable_reflection_library: bool = True
    enable_persistence: bool = False
    persistence_path: Optional[str] = None
    early_stop_threshold: int = 3  # 连续失败多少次后停止


@dataclass
class ExecutionSummary:
    """执行摘要"""
    task: str
    success: bool
    total_steps: int
    successful_steps: int
    failed_steps: int
    final_answer: Optional[str]
    history: List[StepResult]
    metadata: Dict[str, Any]


class ReflexionOrchestrator:
    """
    Reflexion框架主编排器

    实现完整的 "行动 -> 观察 -> 反思 -> 纠正 -> 再行动" 循环

    特性：
    - 智能工具调用
    - 自动错误反思和恢复
    - 反思库复用
    - 上下文管理
    - 防止死循环
    - 可观测性
    """

    def __init__(
        self,
        llm: BaseChatModel,
        tools: Dict[str, BaseTool],
        config: Optional[OrchestratorConfig] = None,
        reflector: Optional[Reflector] = None,
        executor: Optional[ExecutorAgent] = None,
        reflection_library: Optional[ReflectionLibrary] = None,
    ):
        """
        初始化编排器

        Args:
            llm: 语言模型
            tools: 工具字典
            config: 配置
            reflector: 自定义反思者
            executor: 自定义执行者
            reflection_library: 自定义反思库
        """
        self.config = config or OrchestratorConfig()

        # 初始化组件
        self.llm = llm
        self.tools = tools

        # 反思者
        self.reflector = reflector or Reflector(
            llm=llm,
            mode="full" if not self.config.verbose else "quick",
        )

        # 执行者
        self.executor = executor or ExecutorAgent(
            llm=llm,
            tools=tools,
            verbose=self.config.verbose,
        )

        # 上下文管理器
        self.context_manager = ContextManager(
            max_steps=self.config.max_steps,
            max_history=self.config.max_history,
            enable_persistence=self.config.enable_persistence,
            persistence_path=self.config.persistence_path,
        )

        # 反思库
        self.reflection_library = reflection_library
        if self.config.enable_reflection_library and self.reflection_library is None:
            self.reflection_library = ReflectionLibrary()

        # 回调函数
        self.on_step_callback: Optional[Callable] = None
        self.on_reflection_callback: Optional[Callable] = None
        self.on_complete_callback: Optional[Callable] = None

    async def run(
        self,
        task: str,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionSummary:
        """
        运行Reflexion循环

        Args:
            task: 任务描述
            initial_context: 初始上下文

        Returns:
            执行摘要
        """
        if self.config.verbose:
            print(f"\n{'='*60}")
            print(f"开始任务: {task}")
            print(f"{'='*60}\n")

        # 初始化
        self.context_manager.start_task(task, initial_context)
        consecutive_failures = 0
        final_answer = None

        while not self.context_manager.should_stop():
            # 获取历史
            history = self._convert_to_step_results()

            # 1. 执行者决定动作
            action_type, tool_name, tool_input = await self.executor.decide_action(
                task=task,
                observation=self.context_manager.get_last_entry().observation if self.context_manager.get_last_entry() else None,
                reflection=self.context_manager.get_last_entry().reflection if self.context_manager.get_last_entry() else None,
                history=history,
            )

            # 检查是否完成
            if action_type == "final_answer":
                final_answer = "任务完成"
                break

            # 2. 执行工具
            execution_result = await self.executor.execute_tool(
                tool_name=tool_name,
                tool_input=tool_input or {},
            )

            # 3. 记录执行结果
            status = StepStatus.SUCCESS if execution_result.success else StepStatus.FAILED

            self.context_manager.add_step(
                action=f"调用工具 {tool_name}",
                observation=execution_result.output or execution_result.error or "",
                tool_name=tool_name,
                tool_input=tool_input,
                status=status,
            )

            if self.config.verbose:
                print(f"[步骤 {self.context_manager.current_step}] {tool_name}")
                print(f"  输入: {tool_input}")
                print(f"  结果: {execution_result.output or execution_result.error}")

            # 更新连续失败计数
            if execution_result.success:
                consecutive_failures = 0
            else:
                consecutive_failures += 1

            # 检查是否需要提前停止
            if consecutive_failures >= self.config.early_stop_threshold:
                if self.config.verbose:
                    print(f"\n连续失败 {consecutive_failures} 次，提前停止")
                break

            # 4. 反思
            last_entry = self.context_manager.get_last_entry()
            reflection = await self.reflector.reflect(
                task=task,
                action=last_entry.action,
                observation=last_entry.observation,
                history=history,
            )

            # 尝试从反思库获取建议
            if self.reflection_library and not execution_result.success:
                library_reflection = self.reflection_library.find_reflection(
                    error_message=execution_result.error or execution_result.output,
                )
                if library_reflection:
                    if self.config.verbose:
                        print(f"  [反思库] 找到历史建议: {library_reflection.reflection}")
                    reflection += f"\n\n历史建议: {library_reflection.reflection}"
                    reflection += f"\n建议行动: {', '.join(library_reflection.suggested_actions)}"

            # 更新反思
            last_entry.reflection = reflection

            if self.config.verbose:
                print(f"  反思: {reflection[:200]}...\n")

            # 5. 判断是否应该继续
            should_continue = await self.reflector.should_continue(
                reflection=reflection,
                observation=last_entry.observation,
            )

            if not should_continue:
                final_answer = last_entry.observation
                break

            # 回调
            if self.on_step_callback:
                await self.on_step_callback(self.context_manager.get_last_entry())

        # 生成执行摘要
        summary = ExecutionSummary(
            task=task,
            success=consecutive_failures < self.config.early_stop_threshold,
            total_steps=self.context_manager.current_step,
            successful_steps=self.context_manager.stats["successful_steps"],
            failed_steps=self.context_manager.stats["failed_steps"],
            final_answer=final_answer,
            history=self._convert_to_step_results(),
            metadata={
                "tool_usage": self.context_manager.stats["tool_usage"],
                "context_summary": self.context_manager.get_context_summary(),
            },
        )

        if self.config.verbose:
            print(f"\n{'='*60}")
            print(f"任务完成")
            print(f"总步骤: {summary.total_steps}")
            print(f"成功: {summary.successful_steps}")
            print(f"失败: {summary.failed_steps}")
            print(f"最终答案: {final_answer}")
            print(f"{'='*60}\n")

        # 保存历史
        if self.config.enable_persistence:
            self.context_manager.save()

        # 完成回调
        if self.on_complete_callback:
            await self.on_complete_callback(summary)

        return summary

    def _convert_to_step_results(self) -> List[StepResult]:
        """转换上下文历史为StepResult列表"""
        results = []
        for entry in self.context_manager.history:
            result = StepResult(
                step_number=entry.step_number,
                action=entry.action,
                tool_name=entry.tool_name,
                tool_input=entry.tool_input,
                observation=entry.observation,
                reflection=entry.reflection,
                is_success=entry.status == StepStatus.SUCCESS,
                is_final=entry.status == StepStatus.FINAL,
            )
            results.append(result)
        return results

    def add_tool(self, name: str, tool: BaseTool) -> None:
        """
        添加工具

        Args:
            name: 工具名称
            tool: 工具实例
        """
        self.tools[name] = tool
        self.executor.tools[name] = tool

    def remove_tool(self, name: str) -> None:
        """
        移除工具

        Args:
            name: 工具名称
        """
        if name in self.tools:
            del self.tools[name]
        if name in self.executor.tools:
            del self.executor.tools[name]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "context": self.context_manager.stats,
            "reflection_library": self.reflection_library.get_stats() if self.reflection_library else None,
            "tools_count": len(self.tools),
        }

    def reset(self) -> None:
        """重置状态"""
        self.context_manager.clear()

    def export_history(self) -> Dict[str, Any]:
        """导出执行历史"""
        return self.context_manager.export()

    def __repr__(self) -> str:
        """字符串表示"""
        return f"ReflexionOrchestrator(tools={len(self.tools)}, max_steps={self.config.max_steps})"


# 便捷函数
async def run_reflexion(
    task: str,
    llm: BaseChatModel,
    tools: Dict[str, BaseTool],
    max_steps: int = 20,
    verbose: bool = False,
) -> ExecutionSummary:
    """
    快速运行Reflexion

    Args:
        task: 任务描述
        llm: 语言模型
        tools: 工具字典
        max_steps: 最大步数
        verbose: 是否输出详细信息

    Returns:
        执行摘要
    """
    config = OrchestratorConfig(
        max_steps=max_steps,
        verbose=verbose,
    )

    orchestrator = ReflexionOrchestrator(
        llm=llm,
        tools=tools,
        config=config,
    )

    return await orchestrator.run(task)
