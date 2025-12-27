"""执行者模块 - 负责决定并执行工具调用"""

from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, SystemMessage
from reflexion.core.base import BaseExecutor, StepResult


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    output: str
    error: Optional[str] = None
    tool_used: Optional[str] = None
    raw_result: Any = None


# 默认执行者提示词
DEFAULT_EXECUTOR_PROMPT = """你是一个任务执行专家，负责决定下一步要执行的动作。

**当前任务：**
{task}

**可用工具：**
{tools_description}

**上一步观察：**
{observation}

**历史反思建议：**
{reflection}

**历史步骤：**
{history}

**你的职责：**
1. 分析当前状态和任务目标
2. 决定是完成并给出最终答案，还是调用工具继续执行
3. 如果调用工具，选择合适的工具并生成正确的参数

**输出格式（JSON）：**
```json
{{
  "action_type": "tool_call" | "final_answer",
  "tool_name": "工具名称（仅当action_type为tool_call时）",
  "tool_input": {{参数: 值}}（仅当action_type为tool_call时）,
  "reasoning": "你的推理过程",
  "final_answer": "最终答案（仅当action_type为final_answer时）"
}}
```

请根据当前情况，输出JSON格式的决策："""

# 简化的执行者提示词
QUICK_EXECUTOR_PROMPT = """任务: {task}
上次结果: {observation}
建议: {reflection}

可用工具: {tools_list}

决策：
- 如果任务完成，输出 FINAL_ANSWER: 你的答案
- 如果需要继续，输出 TOOL: 工具名 | PARAMS: JSON参数"""


class ExecutorAgent(BaseExecutor):
    """
    执行者 - 使用LLM决定并执行工具调用

    特性：
    - 智能工具选择
    - 参数生成和验证
    - 上下文感知决策
    - 支持多种提示模式
    """

    def __init__(
        self,
        llm: BaseChatModel,
        tools: Dict[str, BaseTool],
        prompt_template: Optional[str] = None,
        mode: str = "full",
        max_history: int = 5,
        verbose: bool = False,
    ):
        """
        初始化执行者

        Args:
            llm: 语言模型
            tools: 可用工具字典 {name: tool}
            prompt_template: 自定义提示词
            mode: 执行模式 ("full" 或 "quick")
            max_history: 考虑的历史步数
            verbose: 是否输出详细信息
        """
        self.llm = llm
        self.tools = tools
        self.mode = mode
        self.max_history = max_history
        self.verbose = verbose

        if prompt_template:
            self.prompt_template = prompt_template
        else:
            self.prompt_template = DEFAULT_EXECUTOR_PROMPT if mode == "full" else QUICK_EXECUTOR_PROMPT

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
            action_type: "tool_call" 或 "final_answer"
        """
        # 构建提示词
        prompt = self._build_prompt(task, observation, reflection, history)

        if self.verbose:
            print(f"[Executor] 决策中...\n{prompt}\n")

        # 调用LLM
        response = await self.llm.ainvoke([
            SystemMessage(content="你是一个专业的任务执行助手。"),
            HumanMessage(content=prompt),
        ])

        # 解析决策
        decision = self._parse_decision(response.content)

        if self.verbose:
            print(f"[Executor] 决策: {decision}\n")

        return decision

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
    ) -> ExecutionResult:
        """
        执行工具调用

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数

        Returns:
            ExecutionResult
        """
        if tool_name not in self.tools:
            return ExecutionResult(
                success=False,
                output="",
                error=f"工具 '{tool_name}' 不存在",
            )

        tool = self.tools[tool_name]

        try:
            if self.verbose:
                print(f"[Executor] 调用工具: {tool_name} with {tool_input}")

            # 执行工具
            result = await tool.ainvoke(tool_input)

            # 处理不同类型的返回值
            if isinstance(result, dict):
                output = result.get("output", str(result))
            elif hasattr(result, "content"):
                output = result.content
            else:
                output = str(result)

            if self.verbose:
                print(f"[Executor] 工具返回: {output}\n")

            return ExecutionResult(
                success=True,
                output=output,
                tool_used=tool_name,
                raw_result=result,
            )

        except Exception as e:
            error_msg = f"工具执行错误: {str(e)}"
            if self.verbose:
                print(f"[Executor] {error_msg}\n")

            return ExecutionResult(
                success=False,
                output="",
                error=error_msg,
                tool_used=tool_name,
            )

    def _build_prompt(
        self,
        task: str,
        observation: Optional[str],
        reflection: Optional[str],
        history: List[StepResult],
    ) -> str:
        """构建提示词"""
        # 准备工具描述
        tools_description = self._format_tools()

        # 格式化历史
        history_text = self._format_history(history[-self.max_history:])

        # 构建提示词
        prompt = self.prompt_template.format(
            task=task,
            tools_description=tools_description,
            tools_list=list(self.tools.keys()),
            observation=observation or "无",
            reflection=reflection or "无",
            history=history_text,
        )

        return prompt

    def _format_tools(self) -> str:
        """格式化工具描述"""
        lines = []
        for name, tool in self.tools.items():
            desc = getattr(tool, "description", "无描述")
            lines.append(f"- {name}: {desc}")

        return "\n".join(lines) if lines else "无可用工具"

    def _format_history(self, history: List[StepResult]) -> str:
        """格式化历史步骤"""
        if not history:
            return "无历史记录"

        lines = []
        for step in history:
            status = "✓" if step.is_success else "✗"
            lines.append(
                f"{status} 步骤{step.step_number}: {step.action} -> {step.observation[:80]}..."
            )

        return "\n".join(lines)

    def _parse_decision(self, response: str) -> tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        """解析LLM的决策响应"""
        response = response.strip()

        # 尝试解析JSON
        if "```json" in response or "```" in response:
            # 提取JSON代码块
            import re
            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                json_str = response
        else:
            json_str = response

        try:
            import json
            decision = json.loads(json_str)

            action_type = decision.get("action_type", "tool_call")

            if action_type == "final_answer":
                return ("final_answer", None, None)
            else:
                tool_name = decision.get("tool_name")
                tool_input = decision.get("tool_input", {})
                return ("tool_call", tool_name, tool_input)

        except json.JSONDecodeError:
            # JSON解析失败，使用文本解析
            response_lower = response.lower()

            if "final_answer" in response_lower or "final" in response_lower:
                return ("final_answer", None, None)

            # 提取工具名称
            tool_match = None
            for tool_name in self.tools.keys():
                if tool_name.lower() in response_lower:
                    tool_match = tool_name
                    break

            if tool_match:
                return ("tool_call", tool_match, {})
            else:
                # 默认继续执行
                return ("final_answer", None, None)


class SimpleExecutor:
    """
    简化版执行者 - 不使用LLM，直接执行预定义的工具

    适用于：
    - 确定性任务
    - 低延迟场景
    - 成本敏感场景
    """

    def __init__(
        self,
        tools: Dict[str, Callable],
        verbose: bool = False,
    ):
        """
        初始化简化执行者

        Args:
            tools: 工具字典 {name: callable}
            verbose: 是否输出详细信息
        """
        self.tools = tools
        self.verbose = verbose

    async def execute(
        self,
        tool_name: str,
        **kwargs,
    ) -> ExecutionResult:
        """执行工具"""
        if tool_name not in self.tools:
            return ExecutionResult(
                success=False,
                output="",
                error=f"工具 '{tool_name}' 不存在",
            )

        tool_func = self.tools[tool_name]

        try:
            if self.verbose:
                print(f"[SimpleExecutor] 执行: {tool_name}({kwargs})")

            result = await tool_func(**kwargs) if callable(tool_func) else tool_func

            return ExecutionResult(
                success=True,
                output=str(result),
                tool_used=tool_name,
                raw_result=result,
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                tool_used=tool_name,
            )
