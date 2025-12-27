"""
对比示例：Reflexion 自定义实现 vs Deep Agents

展示如何用 Deep Agents 简化相同的功能
"""

import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel, Field

# ========== 第一部分：Reflexion 自定义实现 ==========

print("=" * 80)
print("【方案一】使用 Reflexion 自定义实现")
print("=" * 80)
print("""
需要：
- ~1000+ 行自定义代码
- 手动实现 ReAct 循环
- 手动实现反思机制
- 手动管理上下文
- 手动实现多智能体协作

优点：
- 完全控制
- 自定义反思库
- 细粒度优化

缺点：
- 代码量大
- 维护成本高
- 需要持续更新
""")

async def reflexion_example():
    """Reflexion 实现示例（简化版）"""
    from langchain_openai import ChatOpenAI
    from reflexion import ReflexionOrchestrator
    from reflexion.examples.example_tools import create_example_tools

    # 1. 初始化
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    tools = create_example_tools()

    # 2. 创建编排器
    orchestrator = ReflexionOrchestrator(
        llm=llm,
        tools=tools,
        max_steps=10,
        verbose=False,  # 减少输出
    )

    # 3. 运行任务
    task = "计算 25 加 18，然后搜索关于 python 的信息"
    summary = await orchestrator.run(task)

    # 4. 结果
    print(f"\n✓ 任务: {task}")
    print(f"  成功: {summary.success}")
    print(f"  步骤数: {summary.total_steps}")
    print(f"  结果: {summary.final_answer[:100] if summary.final_answer else 'N/A'}...")
    print(f"  代码量: ~1000+ 行")


# ========== 第二部分：Deep Agents 实现 ==========

print("\n" + "=" * 80)
print("【方案二】使用 Deep Agents")
print("=" * 80)
print("""
需要：
- 安装: pip install deepagents
- 几行代码即可实现

自动提供：
- ✅ 自动规划（内置 write_todos）
- ✅ 自动上下文管理
- ✅ 自动子智能体生成
- ✅ 文件系统工具
- ✅ 防死循环
- ✅ 可观测性

优点：
- 代码量极少
- 官方维护
- 功能完整
- 持续更新

缺点：
- 反思功能需要自定义
- 细粒度控制较少
""")

# Deep Agents 版本
def deepagents_example():
    """Deep Agents 实现示例"""
    # 注意：需要先安装 deepagents
    # pip install deepagents

    # 假设已经安装
    try:
        from deepagents import create_deep_agent
        from langchain_openai import ChatOpenAI

        # 1. 创建工具（相同的工具）
        tools = create_deepagent_tools()

        # 2. 创建智能体（一行代码！）
        agent = create_deep_agent(
            tools=tools,
            system_prompt="""你是一个智能助手，具有自我反思能力。
执行任务时，注意：
1. 先规划任务步骤
2. 逐步执行并观察结果
3. 遇到错误时分析原因
4. 使用合适的工具完成任务
"""
        )

        # 3. 运行任务
        task = "计算 25 加 18，然后搜索关于 python 的信息"
        result = agent.invoke({"messages": [{"role": "user", "content": task}]})

        # 4. 结果
        print(f"\n✓ 任务: {task}")
        print(f"  成功: {'是' if result else '否'}")
        print(f"  代码量: ~50 行")
        print(f"  结果: {result['messages'][-1].content[:100] if result else 'N/A'}...")

    except ImportError:
        print("\n⚠️  Deep Agents 未安装")
        print("安装命令: pip install deepagents")
        print("\n示例代码:")
        print("""
from deepagents import create_deep_agent

agent = create_deep_agent(
    tools=[calculator, search],
    system_prompt="你是一个智能助手..."
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "你的任务"}]
})
        """)


# ========== 第三部分：工具定义（通用） ==========

def create_deepagent_tools():
    """创建 Deep Agents 兼容的工具"""
    from langchain_core.tools import tool

    # 计算器工具
    @tool
    def calculator(a: float, b: float, operation: str) -> str:
        """执行基本数学运算: 加(add)、减(subtract)、乘(multiply)、除(divide)"""
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return "错误: 除数不能为零"
                result = a / b
            else:
                return f"错误: 未知操作 '{operation}'"
            return f"{a} {operation} {b} = {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"

    # 搜索工具
    @tool
    def search(query: str) -> str:
        """模拟网络搜索，返回与查询相关的信息"""
        knowledge_base = {
            "python": "Python是一种高级编程语言，由Guido van Rossum于1991年创建。",
            "langchain": "LangChain是一个用于开发由语言模型驱动的应用程序的框架。",
            "reflexion": "Reflexion是一种让AI系统通过反思和自我纠正来改进的方法。",
            "openai": "OpenAI是一家人工智能研究公司，开发了GPT系列模型。",
            "agent": "AI Agent是能够感知环境并采取行动以实现目标的智能体。",
        }
        results = []
        for key, value in knowledge_base.items():
            if key in query.lower() or query.lower() in key:
                results.append(f"- {key}: {value}")
        if results:
            return "搜索结果:\n" + "\n".join(results)
        else:
            return f"未找到关于 '{query}' 的信息。"

    return [calculator, search]


# ========== 第四部分：混合方案（保留反思库） ==========

print("\n" + "=" * 80)
print("【方案三】混合方案：Deep Agents + 自定义反思库")
print("=" * 80)
print("""
结合两者的优势：
- 使用 Deep Agents 的强大功能
- 保留反思库作为特色功能
- 大幅减少代码量
""")

class ReflectionLibrary:
    """简化的反思库"""
    def __init__(self):
        self.reflections = []

    def add_reflection(self, error: str, suggestion: str):
        """添加反思"""
        self.reflections.append({"error": error, "suggestion": suggestion})

    def get_suggestion(self, error: str) -> str:
        """获取建议"""
        for ref in self.reflections:
            if ref["error"].lower() in error.lower():
                return ref["suggestion"]
        return None

class ReflexionDeepAgent:
    """Deep Agents 包装器，添加反思库功能"""
    def __init__(self, agent, reflection_library=None):
        self.agent = agent
        self.library = reflection_library or ReflectionLibrary()

    def invoke(self, input_data):
        """调用智能体，添加反思"""
        result = self.agent.invoke(input_data)

        # 分析结果，如果失败则添加反思
        content = result['messages'][-1].content
        if "错误" in content or "失败" in content or "Error" in content:
            suggestion = self._generate_suggestion(content)
            self.library.add_reflection(content, suggestion)

        return result

    def _generate_suggestion(self, error: str) -> str:
        """生成改进建议"""
        if "除数不能为零" in error:
            return "避免除以零，检查除数是否为0"
        elif "未知操作" in error:
            return "检查操作类型是否正确，支持: add, subtract, multiply, divide"
        else:
            return "检查输入参数是否正确"

def hybrid_example():
    """混合方案示例"""
    try:
        from deepagents import create_deep_agent

        # 1. 创建基础智能体
        tools = create_deepagent_tools()
        agent = create_deep_agent(
            tools=tools,
            system_prompt="你是一个智能助手..."
        )

        # 2. 添加反思库包装
        hybrid_agent = ReflexionDeepAgent(agent)

        # 3. 运行任务
        task = "计算 100 除以 0，然后搜索关于 python 的信息"
        result = hybrid_agent.invoke({
            "messages": [{"role": "user", "content": task}]
        })

        print(f"\n✓ 任务: {task}")
        print(f"  执行了")
        print(f"  反思库记录: {len(hybrid_agent.library.reflections)} 条")
        print(f"  代码量: ~100 行（包括反思库）")

    except ImportError:
        print("\n⚠️  Deep Agents 未安装")


# ========== 第五部分：详细对比表格 ==========

print("\n" + "=" * 80)
print("【详细对比】")
print("=" * 80)

comparison_table = """
┌──────────────────┬──────────────────────┬─────────────────────┐
│      特性         │   Reflexion 自定义     │     Deep Agents     │
├──────────────────┼──────────────────────┼─────────────────────┤
│ 代码量            │  ~1000+ 行           │  ~50 行             │
│ 自动规划          │  ❌ 手动实现          │  ✅ 内置            │
│ 文件系统          │  ❌ 无               │  ✅ 内置            │
│ 子智能体          │  ✅ 自定义协作        │  ✅ 内置            │
│ 反思库            │  ✅ 独特特色          │  ❌ 需要自定义       │
│ 防死循环          │  ✅ 自定义            │  ✅ 内置            │
│ 可观测性          │  ✅ 详细日志          │  ✅ 支持            │
│ 维护成本          │  高（自己维护）       │  低（官方维护）      │
│ 学习曲线          │  陡峭                │  平缓               │
│ 扩展性            │  灵活                │  灵活               │
│ 成本优化          │  ✅ 可精确控制        │  ⚠️  可能较高        │
└──────────────────┴──────────────────────┴─────────────────────┘
"""
print(comparison_table)


# ========== 第六部分：推荐方案 ==========

print("=" * 80)
print("【推荐方案】")
print("=" * 80)
print("""
根据不同场景选择：

1. 快速开发/原型验证
   → 推荐使用 Deep Agents
   → 理由：几行代码即可运行，快速验证想法

2. 生产环境/需要特色功能
   → 推荐混合方案：Deep Agents + 反思库
   → 理由：既有官方框架的稳定性，又有自定义特色

3. 研究项目/需要完全控制
   → 保留 Reflexion 自定义实现
   → 理由：可以精确控制每个细节

4. 成本敏感场景
   → 混合方案 + 成本优化
   → 理由：用不同模型（GPT-4规划 + GPT-3.5执行）

建议行动步骤：
1. 安装 Deep Agents: pip install deepagents
2. 用 Deep Agents 重构基础功能
3. 保留反思库作为包装器
4. 对比测试效果和成本
5. 根据结果调整方案
""")


# ========== 主程序 ==========

async def main():
    """运行所有对比示例"""

    # 方案一：Reflexion
    try:
        await reflexion_example()
    except Exception as e:
        print(f"\n⚠️  Reflexion 示例执行出错: {e}")

    # 方案二：Deep Agents
    deepagents_example()

    # 方案三：混合
    hybrid_example()


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     Reflexion vs Deep Agents 完整对比示例                     ║
╚═══════════════════════════════════════════════════════════════╝

本示例展示：
1. Reflexion 自定义实现的完整代码
2. Deep Agents 的简化版本
3. 混合方案（结合两者优势）
4. 详细对比表格
5. 推荐方案

""")
    asyncio.run(main())