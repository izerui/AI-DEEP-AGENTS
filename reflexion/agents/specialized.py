"""专用智能体 - 将执行者和反思者拆分为独立的智能体"""

from typing import List, Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool


class PlannerAgent:
    """
    规划智能体 - 负责任务分解和计划生成

    专注于：
    - 分析任务需求
    - 分解复杂任务
    - 生成执行计划
    """

    def __init__(
        self,
        llm: BaseChatModel,
        verbose: bool = False,
    ):
        """
        初始化规划智能体

        Args:
            llm: 语言模型
            verbose: 是否输出详细信息
        """
        self.llm = llm
        self.verbose = verbose

        self.system_prompt = """你是一个专业的任务规划专家。你的职责是：
1. 理解用户的任务需求
2. 将复杂任务分解为可执行的步骤
3. 识别每个步骤需要使用的工具
4. 生成清晰的执行计划

请始终保持思考的逻辑性和可执行性。"""

    async def plan(
        self,
        task: str,
        available_tools: List[str],
    ) -> Dict[str, Any]:
        """
        为任务生成执行计划

        Args:
            task: 任务描述
            available_tools: 可用工具列表

        Returns:
            计划字典
        """
        prompt = f"""任务: {task}

可用工具:
{chr(10).join(f'- {tool}' for tool in available_tools)}

请生成一个执行计划，包含以下内容：
1. 任务分析：任务的目标和要求
2. 执行步骤：详细的步骤列表
3. 工具选择：每个步骤使用的工具
4. 预期结果：每个步骤的预期输出

请以结构化的格式输出。"""

        if self.verbose:
            print(f"[Planner] 正在规划任务: {task}\n")

        response = await self.llm.ainvoke([
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ])

        plan = {
            "task": task,
            "analysis": "",
            "steps": [],
            "raw_plan": response.content,
        }

        if self.verbose:
            print(f"[Planner] 生成的计划:\n{response.content}\n")

        return plan


class ExecutorAgent:
    """
    执行智能体 - 专注于执行具体的工具调用

    专注于：
    - 工具调用
    - 参数生成
    - 执行效率
    """

    def __init__(
        self,
        llm: BaseChatModel,
        tools: Dict[str, BaseTool],
        verbose: bool = False,
    ):
        """
        初始化执行智能体

        Args:
            llm: 语言模型
            tools: 工具字典
            verbose: 是否输出详细信息
        """
        self.llm = llm
        self.tools = tools
        self.verbose = verbose

    async def execute_step(
        self,
        step_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行单个步骤

        Args:
            step_description: 步骤描述
            context: 上下文信息

        Returns:
            执行结果
        """
        if self.verbose:
            print(f"[Executor] 执行步骤: {step_description}\n")

        # 这里使用简化的执行逻辑
        # 实际项目中可以集成更复杂的 Agent
        prompt = f"""步骤: {step_description}

上下文: {context or "无"}

可用工具: {list(self.tools.keys())}

请决定：
1. 需要调用哪个工具？
2. 工具的参数是什么？

以 JSON 格式输出：
{{
  "tool_name": "工具名称",
  "tool_input": {{参数: 值}}
}}"""

        response = await self.llm.ainvoke([
            {"role": "system", "content": "你是一个专业的工具执行助手。"},
            {"role": "user", "content": prompt},
        ])

        # 解析并执行
        try:
            import json
            decision = json.loads(response.content)

            tool = self.tools.get(decision["tool_name"])
            if tool:
                result = await tool.ainvoke(decision.get("tool_input", {}))

                return {
                    "success": True,
                    "result": result,
                    "tool_used": decision["tool_name"],
                }
            else:
                return {
                    "success": False,
                    "error": f"工具 {decision['tool_name']} 不存在",
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


class CriticAgent:
    """
    批判智能体 - 专门负责审查和批判

    专注于：
    - 结果验证
    - 错误识别
    - 改进建议
    - 质量评估
    """

    def __init__(
        self,
        llm: BaseChatModel,
        strictness: float = 0.7,
        verbose: bool = False,
    ):
        """
        初始化批判智能体

        Args:
            llm: 语言模型
            strictness: 严格程度 (0-1)
            verbose: 是否输出详细信息
        """
        self.llm = llm
        self.strictness = strictness
        self.verbose = verbose

        self.system_prompt = f"""你是一个专业的批判和审查专家。你的职责是：
1. 客观地评估执行结果的质量
2. 识别潜在的问题和错误
3. 提供具体的改进建议
4. 判断结果是否满足要求

严格程度: {strictness:.1f} (0=非常宽松, 1=非常严格)

请始终保持客观、专业的批判态度。"""

    async def review(
        self,
        task: str,
        execution_result: Dict[str, Any],
        expected_output: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        审查执行结果

        Args:
            task: 原始任务
            execution_result: 执行结果
            expected_output: 期望的输出（可选）

        Returns:
            审查结果
        """
        prompt = f"""任务: {task}

执行结果:
{execution_result}

{f'期望输出: {expected_output}' if expected_output else ''}

请进行审查并输出：
1. 质量评分 (0-1)
2. 是否满足要求 (是/否)
3. 发现的问题 (如果有)
4. 改进建议 (如果有)

请以结构化的格式输出。"""

        if self.verbose:
            print(f"[Critic] 正在审查结果...\n")

        response = await self.llm.ainvoke([
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ])

        review = {
            "review_content": response.content,
            "passed": False,
            "score": 0.0,
            "issues": [],
            "suggestions": [],
        }

        # 简单解析（实际项目中应该用结构化输出）
        content_lower = response.content.lower()
        if "满足" in content_lower or "通过" in content_lower or "pass" in content_lower:
            review["passed"] = True

        if self.verbose:
            print(f"[Critic] 审查结果:\n{response.content}\n")

        return review

    async def criticize(
        self,
        action: str,
        result: Any,
    ) -> str:
        """
        对动作和结果进行批判

        Args:
            action: 执行的动作
            result: 执行结果

        Returns:
            批判意见
        """
        prompt = f"""动作: {action}
结果: {result}

请提供批判性意见：
1. 这个动作是否合适？
2. 结果是否正确？
3. 有什么可以改进的地方？"""

        response = await self.llm.ainvoke([
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ])

        return response.content
