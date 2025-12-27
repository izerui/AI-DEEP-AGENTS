"""
Deep Agents 实际运行示例

演示如何使用 Deep Agents 快速构建智能体
"""

from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool


# ========== 工具定义 ==========

@tool
def calculator(a: float, b: float, operation: str) -> str:
    """
    执行基本数学运算
    
    Args:
        a: 第一个数字
        b: 第二个数字
        operation: 操作类型 (add: 加, subtract: 减, multiply: 乘, divide: 除)
    
    Returns:
        计算结果字符串
    """
    try:
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return f"❌ 错误: 除数不能为零"
            result = a / b
        else:
            return f"❌ 错误: 未知操作 '{operation}'，支持的操作: add, subtract, multiply, divide"
        
        return f"✓ {a} {operation} {b} = {result}"
        
    except Exception as e:
        return f"❌ 计算错误: {str(e)}"


@tool
def search(query: str, max_results: int = 3) -> str:
    """
    模拟网络搜索，返回与查询相关的信息
    
    Args:
        query: 搜索关键词
        max_results: 返回结果的最大数量
    
    Returns:
        搜索结果字符串
    """
    knowledge_base = {
        "python": "Python是一种高级编程语言，由Guido van Rossum于1991年创建。Python以简洁明了的语法著称，广泛应用于数据分析、人工智能、Web开发等领域。",
        "langchain": "LangChain是一个用于开发由语言模型驱动的应用程序的框架。它提供了丰富的工具和组件，帮助开发者快速构建智能体应用。",
        "reflexion": "Reflexion是一种让AI系统通过反思和自我纠正来改进的方法。它模拟人类的反思过程，通过分析错误来优化后续行动。",
        "openai": "OpenAI是一家人工智能研究公司，开发了GPT系列模型。GPT-4是目前最强大的语言模型之一，在多项任务中表现出色。",
        "agent": "AI Agent（人工智能智能体）是能够感知环境、做出决策并采取行动以实现目标的自主系统。",
        "deepagents": "Deep Agents是LangChain推出的智能体框架，提供开箱即用的规划、工具调用和子智能体功能。",
    }
    
    query_lower = query.lower()
    results = []
    
    for key, value in knowledge_base.items():
        if key in query_lower or query_lower in key:
            results.append(f"📖 {key.upper()}: {value}")
    
    if results:
        limited_results = results[:max_results]
        return "🔍 搜索结果:\n" + "\n\n".join(limited_results)
    else:
        available = ", ".join(knowledge_base.keys())
        return f"❌ 未找到关于 '{query}' 的信息。\n💡 建议搜索: {available}"


@tool
def text_analyzer(text: str, operation: Literal["count_words", "count_chars", "to_upper", "to_lower"]) -> str:
    """
    分析和处理文本
    
    Args:
        text: 要分析的文本
        operation: 操作类型 (count_words: 词数, count_chars: 字符数, to_upper: 转大写, to_lower: 转小写)
    
    Returns:
        分析结果字符串
    """
    try:
        if operation == "count_words":
            word_count = len(text.split())
            return f"📝 文本 '{text[:30]}...' 包含 {word_count} 个单词"
        
        elif operation == "count_chars":
            char_count = len(text)
            return f"📏 文本 '{text[:30]}...' 包含 {char_count} 个字符"
        
        elif operation == "to_upper":
            return text.upper()
        
        elif operation == "to_lower":
            return text.lower()
        
        else:
            return f"❌ 错误: 未知操作 '{operation}'"
    
    except Exception as e:
        return f"❌ 文本分析错误: {str(e)}"


# ========== Deep Agents 示例 ==========

def example_1_basic_usage():
    """示例1: 基础使用 - 单任务执行"""
    print("\n" + "="*80)
    print("【示例1】基础使用 - 单任务执行")
    print("="*80)
    
    try:
        from deepagents import create_deep_agent
        
        # 1. 创建工具列表
        tools = [calculator, search]
        
        # 2. 创建 Deep Agent（一行代码！）
        agent = create_deep_agent(
            tools=tools,
            system_prompt="""你是一个智能数学助手，具有计算和信息搜索能力。
        
任务执行原则：
1. 仔细理解用户的需求
2. 使用合适的工具完成任务
3. 清晰地呈现结果
4. 如果遇到错误，友好地提示用户
"""
        )
        
        # 3. 执行任务
        task = "计算 25 加 18，然后搜索关于 python 的信息"
        print(f"\n📋 任务: {task}\n")
        
        result = agent.invoke({
            "messages": [{"role": "user", "content": task}]
        })
        
        # 4. 输出结果
        print("\n✅ 执行结果:")
        print("-" * 80)
        print(result['messages'][-1].content)
        print("-" * 80)
        
        # 5. 显示执行信息
        print(f"\n📊 统计信息:")
        print(f"  - 消息数量: {len(result['messages'])}")
        
    except ImportError:
        print("\n❌ 错误: Deep Agents 未安装")
        print("\n📦 安装命令:")
        print("   pip install deepagents")
        print("\n🔗 文档地址:")
        print("   https://docs.langchain.com/oss/python/deepagents/quickstart")


def example_2_multi_step_task():
    """示例2: 多步骤任务 - 自动规划和执行"""
    print("\n" + "="*80)
    print("【示例2】多步骤任务 - 自动规划和执行")
    print("="*80)
    
    try:
        from deepagents import create_deep_agent
        
        # 1. 创建更多工具
        tools = [calculator, search, text_analyzer]
        
        # 2. 创建 Deep Agent
        agent = create_deep_agent(
            tools=tools,
            system_prompt="""你是一个全能助手，擅长：
1. 数学计算
2. 信息搜索
3. 文本分析

对于复杂任务，请：
1. 先将任务分解为多个步骤
2. 逐步执行每个步骤
3. 综合所有步骤的结果
4. 给出清晰的最终答案
"""
        )
        
        # 3. 执行复杂任务
        task = """帮我完成以下任务：
1. 计算 100 除以 4 的结果
2. 搜索关于 langchain 的信息
3. 统计搜索结果中的字符数
4. 总结以上所有信息
"""
        print(f"\n📋 任务:\n{task}\n")
        
        result = agent.invoke({
            "messages": [{"role": "user", "content": task}]
        })
        
        # 4. 输出结果
        print("\n✅ 执行结果:")
        print("-" * 80)
        print(result['messages'][-1].content)
        print("-" * 80)
        
    except ImportError:
        print("\n❌ 错误: Deep Agents 未安装")
        print("请先安装: pip install deepagents")


def example_3_error_recovery():
    """示例3: 错误恢复 - 智能处理失败"""
    print("\n" + "="*80)
    print("【示例3】错误恢复 - 智能处理失败")
    print("="*80)
    
    try:
        from deepagents import create_deep_agent
        
        tools = [calculator]
        
        agent = create_deep_agent(
            tools=tools,
            system_prompt="""你是一个计算助手，负责数学运算。

遇到错误时：
1. 识别错误原因
2. 尝试纠正错误
3. 给出清晰的错误说明
4. 提供可行的替代方案
"""
        )
        
        # 故意制造错误：除以零
        task = "计算 100 除以 0 的结果，如果失败，则计算 100 除以 5"
        print(f"\n📋 任务: {task}\n")
        
        result = agent.invoke({
            "messages": [{"role": "user", "content": task}]
        })
        
        print("\n✅ 执行结果:")
        print("-" * 80)
        print(result['messages'][-1].content)
        print("-" * 80)
        
    except ImportError:
        print("\n❌ 错误: Deep Agents 未安装")
        print("请先安装: pip install deepagents")


def example_4_custom_llm():
    """示例4: 自定义 LLM 配置"""
    print("\n" + "="*80)
    print("【示例4】自定义 LLM 配置")
    print("="*80)
    
    try:
        from deepagents import create_deep_agent
        
        # 1. 配置自定义 LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",  # 使用更便宜的模型
            temperature=0,
            timeout=60,
        )
        
        # 2. 使用自定义 LLM 创建 Agent
        agent = create_deep_agent(
            tools=[search],
            llm=llm,  # 传入自定义 LLM
            system_prompt="你是一个信息搜索专家，擅长快速找到准确信息。"
        )
        
        task = "搜索关于 deepagents 的信息"
        print(f"\n📋 任务: {task}\n")
        
        result = agent.invoke({
            "messages": [{"role": "user", "content": task}]
        })
        
        print("\n✅ 执行结果:")
        print("-" * 80)
        print(result['messages'][-1].content)
        print("-" * 80)
        
        print("\n💡 提示: 使用 GPT-4o-mini 可以降低成本")
        
    except ImportError:
        print("\n❌ 错误: Deep Agents 未安装")
        print("请先安装: pip install deepagents")


# ========== 主程序 ==========

def main():
    """运行所有示例"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         Deep Agents 实际运行示例                                ║
╠═══════════════════════════════════════════════════════════════╣
║  本示例展示如何使用 Deep Agents 快速构建智能体应用              ║
║                                                                 ║
║  Deep Agents 提供的自动功能：                                   ║
║  ✅ 自动任务规划（内置 write_todos）                            ║
║  ✅ 自动上下文管理                                              ║
║  ✅ 自动子智能体生成                                            ║
║  ✅ 文件系统工具                                                ║
║  ✅ 防死循环                                                    ║
║  ✅ 可观测性                                                    ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # 运行各个示例
    example_1_basic_usage()
    example_2_multi_step_task()
    example_3_error_recovery()
    example_4_custom_llm()
    
    # 总结
    print("\n" + "="*80)
    print("【总结】")
    print("="*80)
    print("""
Deep Agents vs Reflexion 对比：

📊 代码量：
   - Reflexion: ~1000+ 行自定义代码
   - Deep Agents: ~50 行即可实现相同功能

⚡ 开发速度：
   - Reflexion: 需要实现循环、反思、上下文等
   - Deep Agents: 开箱即用，几行代码

🔧 功能完整性：
   - Reflexion: 需要手动实现所有功能
   - Deep Agents: 内置规划、文件系统、子智能体等

💰 成本优化：
   - Reflexion: 可精确控制每个环节的模型选择
   - Deep Agents: 可通过自定义 LLM 实现成本控制

🎯 推荐使用场景：
   1. 快速开发 → Deep Agents
   2. 需要反思库 → Deep Agents + 自定义包装器
   3. 完全控制 → 保留 Reflexion

📦 安装命令：
   pip install deepagents

🔗 官方文档：
   https://docs.langchain.com/oss/python/deepagents/quickstart
    """)


if __name__ == "__main__":
    main()