"""反思者模块 - 负责分析执行结果并提供改进建议"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
from reflexion.core.base import BaseReflector, StepResult


@dataclass
class ReflectionResult:
    """反思结果"""
    content: str
    should_continue: bool
    success_probability: float
    suggested_actions: List[str]
    error_type: Optional[str] = None


# 默认反思提示词模板
DEFAULT_REFLECTOR_PROMPT = """你是一个专业的反思专家，负责分析AI系统的执行结果并提供改进建议。

**你的任务：**
分析以下执行步骤的结果，判断是否成功，如果失败则提供具体的改进建议。

**分析维度：**
1. 是否完成了用户的目标？
2. 如果失败，失败的原因是什么？
   - 参数错误（类型、范围、格式）
   - 工具选择错误
   - 逻辑错误
   - 环境问题
3. 下一步应该如何改进？

**输出格式：**
请按照以下格式输出：

```
成功判断: [成功/失败/部分成功]
成功概率: [0-1之间的数字]

失败原因: [如果成功则填"无"]
[具体分析失败原因]

改进建议:
1. [具体的改进建议1]
2. [具体的改进建议2]
...

下一步行动: [具体的下一步行动建议]
```

**历史步骤：**
{history}

**当前步骤：**
- 任务: {task}
- 动作: {action}
- 观察: {observation}
"""

# 简化的反思提示词（用于快速迭代）
QUICK_REFLECTOR_PROMPT = """分析以下执行结果，判断是否需要继续：

任务: {task}
动作: {action}
结果: {observation}

输出格式：
- 继续执行: [是/否]
- 原因: [简短说明]
- 建议: [下一步建议]"""


class Reflector(BaseReflector):
    """
    反思者 - 使用LLM分析执行结果并生成反思

    特性：
    - 支持多种反思模式（完整/快速）
    - 可配置的反思深度
    - 错误类型识别
    - 历史上下文分析
    """

    def __init__(
        self,
        llm: BaseChatModel,
        prompt_template: Optional[str] = None,
        mode: str = "full",  # "full" or "quick"
        max_history: int = 5,
    ):
        """
        初始化反思者

        Args:
            llm: 语言模型
            prompt_template: 自定义反思提示词
            mode: 反思模式 ("full" 或 "quick")
            max_history: 考虑的历史步数
        """
        self.llm = llm
        self.mode = mode
        self.max_history = max_history

        if prompt_template:
            self.prompt_template = prompt_template
        else:
            self.prompt_template = DEFAULT_REFLECTOR_PROMPT if mode == "full" else QUICK_REFLECTOR_PROMPT

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
            反思内容
        """
        # 格式化历史（只保留最近N步）
        history_text = self._format_history(history[-self.max_history:])

        # 构建提示词
        prompt = ChatPromptTemplate.from_template(self.prompt_template)
        messages = await prompt.ainvoke({
            "task": task,
            "action": action,
            "observation": observation,
            "history": history_text,
        })

        # 调用LLM
        response = await self.llm.ainvoke(messages)

        return response.content

    async def reflect_detailed(
        self,
        task: str,
        action: str,
        observation: str,
        history: List[StepResult],
    ) -> ReflectionResult:
        """
        详细的反思分析

        Returns:
            ReflectionResult 对象
        """
        reflection_text = await self.reflect(task, action, observation, history)

        # 解析反思结果
        return self._parse_reflection(reflection_text)

    async def should_continue(self, reflection: str, observation: str) -> bool:
        """
        判断是否应该继续执行

        Args:
            reflection: 反思内容
            observation: 观察结果

        Returns:
            是否继续
        """
        # 使用简单的关键词匹配
        stop_keywords = [
            "任务完成", "成功完成", "已完成", "目标达成",
            "task completed", "successfully completed",
        ]

        continue_keywords = [
            "继续", "重试", "改进", "修正", "需要",
            "continue", "retry", "improve", "fix",
        ]

        reflection_lower = reflection.lower()
        observation_lower = observation.lower()

        # 检查停止信号
        for keyword in stop_keywords:
            if keyword in reflection_lower or keyword in observation_lower:
                return False

        # 检查继续信号
        for keyword in continue_keywords:
            if keyword in reflection_lower:
                return True

        # 默认：如果观察包含错误信息，则继续
        error_indicators = ["error", "错误", "失败", "exception", "failed"]
        for indicator in error_indicators:
            if indicator in observation_lower:
                return True

        return False

    def _format_history(self, history: List[StepResult]) -> str:
        """格式化历史步骤"""
        if not history:
            return "无历史记录"

        lines = []
        for step in history:
            lines.append(f"步骤 {step.step_number}:")
            lines.append(f"  动作: {step.action}")
            if step.tool_name:
                lines.append(f"  工具: {step.tool_name}")
                lines.append(f"  输入: {step.tool_input}")
            lines.append(f"  观察: {step.observation}")
            if step.reflection:
                lines.append(f"  反思: {step.reflection}")
            lines.append("")

        return "\n".join(lines)

    def _parse_reflection(self, reflection_text: str) -> ReflectionResult:
        """解析反思文本为结构化结果"""
        # 简单解析（实际项目中可能需要更复杂的解析逻辑）
        success_probability = 0.5
        should_continue = True
        error_type = None
        suggested_actions = []

        lines = reflection_text.split("\n")
        for line in lines:
            line_lower = line.lower()

            if "成功概率" in line or "probability" in line_lower:
                # 提取概率
                try:
                    import re
                    match = re.search(r"[\d.]+", line)
                    if match:
                        success_probability = float(match.group())
                except:
                    pass

            if "继续执行" in line or "continue" in line_lower:
                should_continue = "否" not in line and "no" not in line_lower

            if "错误类型" in line or "error type" in line_lower:
                error_type = line.split(":", 1)[-1].strip()

            if "建议" in line or "suggestion" in line_lower:
                action = line.split("-", 1)[-1].strip() if "-" in line else line.split(":", 1)[-1].strip()
                if action:
                    suggested_actions.append(action)

        return ReflectionResult(
            content=reflection_text,
            should_continue=should_continue,
            success_probability=success_probability,
            suggested_actions=suggested_actions,
            error_type=error_type,
        )


class ReflectorAgent:
    """
    使用 LangChain Agent 模式的反思者

    更高级的反思实现，支持：
    - 工具调用（例如调用验证工具）
    - 多轮推理
    - 结构化输出
    """

    def __init__(
        self,
        llm: BaseChatModel,
        tools: Optional[List[Any]] = None,
        verbose: bool = False,
    ):
        """
        初始化反思者Agent

        Args:
            llm: 语言模型
            tools: 可用的工具列表
            verbose: 是否输出详细信息
        """
        self.llm = llm
        self.tools = tools or []
        self.verbose = verbose

    async def analyze_and_reflect(
        self,
        context: Dict[str, Any],
    ) -> ReflectionResult:
        """
        分析并反思

        Args:
            context: 包含 task, action, observation, history 等信息

        Returns:
            ReflectionResult
        """
        prompt = self._build_reflection_prompt(context)

        if self.verbose:
            print(f"[Reflector] 分析中...\n{prompt}")

        response = await self.llm.ainvoke([
            SystemMessage(content=self._get_system_message()),
            HumanMessage(content=prompt),
        ])

        reflection_result = self._parse_reflection(response.content)

        if self.verbose:
            print(f"[Reflector] 分析完成:\n{reflection_result}")

        return reflection_result

    def _get_system_message(self) -> str:
        """获取系统消息"""
        return """你是一个专业的反思专家。你的职责是：
1. 分析执行结果是否成功
2. 识别失败原因
3. 提供具体的改进建议
4. 判断是否需要继续执行

请始终保持客观、准确的分析。"""

    def _build_reflection_prompt(self, context: Dict[str, Any]) -> str:
        """构建反思提示词"""
        return f"""任务: {context.get('task', '')}
动作: {context.get('action', '')}
观察: {context.get('observation', '')}

历史步骤:
{self._format_history(context.get('history', []))}

请分析执行结果并提供反思。"""

    def _format_history(self, history: List[StepResult]) -> str:
        """格式化历史"""
        if not history:
            return "无"

        return "\n".join([
            f"- 步骤{i+1}: {h.action} -> {h.observation[:50]}..."
            for i, h in enumerate(history[-3:])  # 只显示最近3步
        ])

    def _parse_reflection(self, text: str) -> ReflectionResult:
        """解析反思结果"""
        # 使用与 Reflector 相同的解析逻辑
        return Reflector(llm=self.llm)._parse_reflection(text)
