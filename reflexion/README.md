# Reflexion - LLM驱动的自我反思工具调用框架

基于 LangChain 实现的 LLM 自我反思工具调用框架，实现 **行动 -> 观察 -> 反思 -> 纠正 -> 再行动** 的智能循环。

## 核心特性

- **自我反思机制**: 执行后自动分析结果，识别错误并生成改进建议
- **智能工具调用**: 基于上下文自动选择合适的工具和参数
- **反思库**: 存储和复用历史反思经验，提高效率
- **防止死循环**: 智能检测并防止陷入无限循环
- **上下文管理**: 完整的执行历史追踪和管理
- **可观测性**: 详细的执行日志和统计信息
- **高度可配置**: 支持自定义反思者、执行者和工具
- **多智能体协作**: 支持规划者-执行者-批判者协作模式，可使用不同模型优化成本

## 架构设计

```
┌─────────────┐
│  用户输入    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  上下文管理器    │ ◄────┐
└────────┬────────┘      │
         │               │
         ▼               │
┌─────────────────┐      │
│  执行者 Agent    │ ────►│ 工具调用
└────────┬────────┘      │
         │               │
         ▼               │
    ┌─────────┐          │
    │ 工具执行 │ ─────────┘
    └────┬────┘
         │
         ▼
┌─────────────────┐
│  观察结果        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  反思者 Reflector│ ────► 反思库 (历史经验)
└────────┬────────┘
         │
         ▼
   ┌─────────┐
   │ 任务完成?│
   └────┬────┘
        │
   No   │   Yes
   ┌────┴────┐
   │         │
   ▼         ▼
继续执行   返回结果
```

## 安装

```bash
pip install langchain langchain-openai pydantic
```

## 快速开始

### 基础使用

```python
import asyncio
from langchain_openai import ChatOpenAI
from reflexion import ReflexionOrchestrator
from reflexion.examples.example_tools import create_example_tools

async def main():
    # 1. 初始化 LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    # 2. 准备工具
    tools = create_example_tools()

    # 3. 创建编排器
    orchestrator = ReflexionOrchestrator(
        llm=llm,
        tools=tools,
        max_steps=10,
        verbose=True,
    )

    # 4. 运行任务
    task = "计算 25 加 18，然后搜索关于 python 的信息"
    summary = await orchestrator.run(task)

    # 5. 查看结果
    print(f"成功: {summary.success}")
    print(f"最终答案: {summary.final_answer}")

asyncio.run(main())
```

### 自定义工具

```python
from reflexion.tools.base_tool import ReflexionTool
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    """工具输入Schema"""
    text: str = Field(description="要处理的文本")

class MyTool(ReflexionTool):
    """自定义工具"""
    name = "my_tool"
    description = "这是一个自定义工具示例"
    args_schema = MyToolInput

    def _run(self, text: str) -> str:
        return f"处理结果: {text.upper()}"

# 注册工具
tools = {
    "my_tool": MyTool(),
}
```

### 使用反思库

```python
from reflexion.memory import ReflectionLibrary, ErrorType

# 创建反思库
library = ReflectionLibrary()

# 添加反思经验
library.add_reflection(
    error_pattern="json decode",
    error_type=ErrorType.PARAMETER_ERROR,
    reflection="JSON解析失败，检查格式",
    suggested_actions=["验证JSON格式", "检查引号闭合"],
)

# 在编排器中使用
orchestrator = ReflexionOrchestrator(
    llm=llm,
    tools=tools,
    reflection_library=library,
)
```

## 核心模块

### 1. Reflector (反思者)

分析执行结果并生成改进建议

```python
from reflexion.core import Reflector

reflector = Reflector(llm=llm, mode="full")

reflection = await reflector.reflect(
    task="计算任务",
    action="调用计算器",
    observation="结果: 42",
    history=[],
)
```

### 2. ExecutorAgent (执行者)

决定下一步行动并执行工具

```python
from reflexion.core import ExecutorAgent

executor = ExecutorAgent(
    llm=llm,
    tools=tools,
    verbose=True,
)

action_type, tool_name, tool_input = await executor.decide_action(
    task="任务描述",
    observation="上一次观察",
    reflection="上一次反思",
    history=[],
)
```

### 3. ContextManager (上下文管理器)

管理执行历史和上下文

```python
from reflexion.memory import ContextManager

context = ContextManager(max_steps=20)
context.start_task("任务描述")

context.add_step(
    action="执行动作",
    observation="观察结果",
    tool_name="工具名",
    status=StepStatus.SUCCESS,
)
```

### 4. ReflectionLibrary (反思库)

存储和检索历史反思经验

```python
from reflexion.memory import ReflectionLibrary

library = ReflectionLibrary()
reflection = library.find_reflection(error_message="错误信息")

if reflection:
    print(f"找到历史建议: {reflection.suggested_actions}")
```

## 配置选项

```python
from reflexion.core import OrchestratorConfig

config = OrchestratorConfig(
    max_steps=20,              # 最大执行步数
    max_history=100,           # 最大历史记录数
    verbose=True,              # 详细输出
    enable_reflection_library=True,  # 启用反思库
    enable_persistence=False,  # 启用持久化
    early_stop_threshold=3,    # 连续失败停止阈值
)

orchestrator = ReflexionOrchestrator(
    llm=llm,
    tools=tools,
    config=config,
)
```

## 高级功能

### 回调函数

```python
async def on_step(step):
    print(f"步骤 {step.step_number}: {step.action}")

async def on_complete(summary):
    print(f"完成! 共 {summary.total_steps} 步")

orchestrator.on_step_callback = on_step
orchestrator.on_complete_callback = on_complete
```

### 自定义反思者

```python
class CustomReflector(Reflector):
    async def reflect(self, task, action, observation, history):
        # 自定义反思逻辑
        return "我的反思"

orchestrator = ReflexionOrchestrator(
    llm=llm,
    tools=tools,
    reflector=CustomReflector(llm),
)
```

### 多任务执行

```python
tasks = ["任务1", "任务2", "任务3"]

for task in tasks:
    summary = await orchestrator.run(task)
    print(f"结果: {summary.final_answer}")
    orchestrator.reset()  # 重置状态
```

## 示例

### 计算任务

```python
task = "计算 100 除以 4，然后将结果乘以 3"
summary = await orchestrator.run(task)
```

### 信息搜索

```python
task = "搜索关于 langchain 和 reflexion 的信息"
summary = await orchestrator.run(task)
```

### 文本处理

```python
task = "统计文本 'hello world' 的单词数，然后转换为大写"
summary = await orchestrator.run(task)
```

## API 参考

### ReflexionOrchestrator

主编排器，协调整个执行流程

**参数:**
- `llm`: 语言模型
- `tools`: 工具字典
- `config`: 配置对象
- `reflector`: 自定义反思者
- `executor`: 自定义执行者
- `reflection_library`: 自定义反思库

**方法:**
- `run(task)`: 运行任务
- `add_tool(name, tool)`: 添加工具
- `remove_tool(name)`: 移除工具
- `reset()`: 重置状态
- `export_history()`: 导出历史

### ExecutionSummary

执行摘要对象

**属性:**
- `task`: 任务描述
- `success`: 是否成功
- `total_steps`: 总步骤数
- `successful_steps`: 成功步骤数
- `failed_steps`: 失败步骤数
- `final_answer`: 最终答案
- `history`: 执行历史
- `metadata`: 元数据

## 多智能体协作

框架还支持多智能体协作模式，将任务分解为规划、执行、审查三个阶段：

```python
from reflexion.agents import CollaborativeAgents
from langchain_openai import ChatOpenAI

# 使用不同模型优化成本
planner_llm = ChatOpenAI(model="gpt-4")  # 强大的规划能力
executor_llm = ChatOpenAI(model="gpt-3.5-turbo")  # 快速执行
critic_llm = ChatOpenAI(model="gpt-4")  # 严格审查

agents = CollaborativeAgents(
    llm=executor_llm,
    tools=tools,
    planner_llm=planner_llm,
    executor_llm=executor_llm,
    critic_llm=critic_llm,
    verbose=True,
)

result = await agents.run(
    task="完成一个复杂的多步骤任务",
    max_iterations=3,
    quality_threshold=0.8,
)

print(f"成功: {result.success}")
print(f"迭代次数: {result.iterations}")
```

### 专用智能体

```python
from reflexion.agents import PlannerAgent, ExecutorAgent, CriticAgent

# 独立使用各个智能体
planner = PlannerAgent(llm=llm)
plan = await planner.plan("任务描述", available_tools=["tool1", "tool2"])

executor = ExecutorAgent(llm=llm, tools=tools)
result = await executor.execute_step("步骤描述")

critic = CriticAgent(llm=llm, strictness=0.8)
review = await critic.review("任务", result)
```

## 最佳实践

1. **工具设计**: 为工具提供清晰的描述和参数Schema
2. **错误处理**: 在工具中实现良好的错误处理和消息
3. **反思库**: 为常见错误添加预定义反思
4. **步数限制**: 根据任务复杂度设置合理的最大步数
5. **日志记录**: 使用verbose模式进行调试
6. **成本控制**: 对于简单任务，可以使用quick模式减少token消耗
7. **多智能体**: 利用多智能体协作，用GPT-4做规划和审查，GPT-3.5做执行

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
