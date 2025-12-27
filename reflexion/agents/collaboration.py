"""多智能体协作框架"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from reflexion.agents.specialized import PlannerAgent, ExecutorAgent, CriticAgent


@dataclass
class CollaborationResult:
    """协作结果"""
    task: str
    success: bool
    plan: Optional[Dict[str, Any]]
    execution_history: List[Dict[str, Any]]
    reviews: List[Dict[str, Any]]
    final_result: Optional[Any]
    iterations: int


class CollaborativeAgents:
    """
    多智能体协作框架

    实现规划者-执行者-批判者的协作模式：
    - Planner Agent: 规划任务
    - Executor Agent: 执行步骤
    - Critic Agent: 审查结果

    特性：
    - 智能体间协作
    - 迭代改进
    - 质量保证
    """

    def __init__(
        self,
        llm: BaseChatModel,
        tools: Dict[str, BaseTool],
        planner_llm: Optional[BaseChatModel] = None,
        executor_llm: Optional[BaseChatModel] = None,
        critic_llm: Optional[BaseChatModel] = None,
        verbose: bool = False,
    ):
        """
        初始化协作智能体

        Args:
            llm: 默认语言模型
            tools: 可用工具
            planner_llm: 规划者专用模型（可选）
            executor_llm: 执行者专用模型（可选）
            critic_llm: 批判者专用模型（可选）
            verbose: 是否输出详细信息
        """
        self.tools = tools
        self.verbose = verbose

        # 初始化各个智能体（可以使用不同的模型）
        self.planner = PlannerAgent(
            llm=planner_llm or llm,
            verbose=verbose,
        )

        self.executor = ExecutorAgent(
            llm=executor_llm or llm,
            tools=tools,
            verbose=verbose,
        )

        self.critic = CriticAgent(
            llm=critic_llm or llm,
            verbose=verbose,
        )

        # 回调函数
        self.on_plan_callback: Optional[Callable] = None
        self.on_execute_callback: Optional[Callable] = None
        self.on_review_callback: Optional[Callable] = None

    async def run(
        self,
        task: str,
        max_iterations: int = 3,
        quality_threshold: float = 0.7,
    ) -> CollaborationResult:
        """
        运行协作流程

        流程：
        1. Planner 规划任务
        2. Executor 执行步骤
        3. Critic 审查结果
        4. 如果不满足要求，返回步骤2改进
        5. 直到满足要求或达到最大迭代次数

        Args:
            task: 任务描述
            max_iterations: 最大迭代次数
            quality_threshold: 质量阈值

        Returns:
            协作结果
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"开始协作任务: {task}")
            print(f"{'='*60}\n")

        execution_history = []
        reviews = []
        plan = None
        final_result = None

        # 1. 规划阶段
        plan = await self.planner.plan(
            task=task,
            available_tools=list(self.tools.keys()),
        )

        if self.on_plan_callback:
            await self.on_plan_callback(plan)

        # 2. 执行-审查迭代
        for iteration in range(max_iterations):
            if self.verbose:
                print(f"\n--- 迭代 {iteration + 1}/{max_iterations} ---\n")

            # 执行阶段
            execution_result = await self._execute_plan(
                plan=plan,
                context={
                    "iteration": iteration + 1,
                    "previous_results": execution_history,
                },
            )

            execution_history.append(execution_result)

            if self.on_execute_callback:
                await self.on_execute_callback(execution_result)

            # 审查阶段
            review = await self.critic.review(
                task=task,
                execution_result=execution_result,
            )

            reviews.append(review)

            if self.on_review_callback:
                await self.on_review_callback(review)

            # 检查是否通过
            if review.get("passed", False):
                final_result = execution_result
                if self.verbose:
                    print(f"\n✓ 质量检查通过！\n")
                break
            else:
                if self.verbose:
                    print(f"\n✗ 质量检查未通过，继续改进...\n")

                # 根据审查意见改进计划
                plan = await self._improve_plan(
                    original_plan=plan,
                    execution_result=execution_result,
                    review=review,
                )

        # 生成结果
        result = CollaborationResult(
            task=task,
            success=final_result is not None,
            plan=plan,
            execution_history=execution_history,
            reviews=reviews,
            final_result=final_result,
            iterations=len(execution_history),
        )

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"协作完成")
            print(f"成功: {result.success}")
            print(f"迭代次数: {result.iterations}")
            print(f"{'='*60}\n")

        return result

    async def _execute_plan(
        self,
        plan: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        执行计划

        Args:
            plan: 计划
            context: 上下文

        Returns:
            执行结果
        """
        # 这里简化处理，实际应该解析计划并执行多个步骤
        # 演示目的，只执行一个代表性步骤

        plan_text = plan.get("raw_plan", "")
        steps = self._extract_steps(plan_text)

        results = []
        for step in steps:
            result = await self.executor.execute_step(
                step_description=step,
                context=context,
            )
            results.append(result)

        # 返回最后一步的结果
        return results[-1] if results else {"success": False, "error": "无法执行计划"}

    async def _improve_plan(
        self,
        original_plan: Dict[str, Any],
        execution_result: Dict[str, Any],
        review: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        根据审查意见改进计划

        Args:
            original_plan: 原始计划
            execution_result: 执行结果
            review: 审查结果

        Returns:
            改进后的计划
        """
        # 简化处理：更新计划内容
        improved_plan = original_plan.copy()

        # 添加审查意见到计划中
        review_content = review.get("review_content", "")
        improved_plan["previous_review"] = review_content
        improved_plan["needs_improvement"] = True

        return improved_plan

    def _extract_steps(self, plan_text: str) -> List[str]:
        """
        从计划文本中提取步骤

        Args:
            plan_text: 计划文本

        Returns:
            步骤列表
        """
        # 简单的步骤提取逻辑
        # 实际项目中应该用更复杂的解析
        steps = []

        lines = plan_text.split("\n")
        for line in lines:
            line = line.strip()
            # 查找以数字或符号开头的行
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                steps.append(line)

        # 如果没找到，返回整个计划作为一个步骤
        if not steps and plan_text:
            steps.append(plan_text[:200])  # 限制长度

        return steps[:3]  # 最多返回3个步骤

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "tools_count": len(self.tools),
            "agents": {
                "planner": self.planner.__class__.__name__,
                "executor": self.executor.__class__.__name__,
                "critic": self.critic.__class__.__name__,
            },
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return f"CollaborativeAgents(tools={len(self.tools)}, agents=3)"
