"""基础使用示例"""

import asyncio
from langchain_openai import ChatOpenAI
from reflexion import ReflexionOrchestrator
from reflexion.examples.example_tools import create_example_tools


async def basic_usage_example():
    """
    基础使用示例

    演示如何:
    1. 创建编排器
    2. 定义任务
    3. 运行Reflexion循环
    4. 获取结果
    """
    # 1. 初始化LLM
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
    )

    # 2. 准备工具
    tools = create_example_tools()

    # 3. 创建编排器
    orchestrator = ReflexionOrchestrator(
        llm=llm,
        tools=tools,
        max_steps=10,
        verbose=True,
    )

    # 4. 定义任务
    task = "计算 25 加 18，然后搜索关于 python 的信息"

    # 5. 运行
    print("开始执行任务...\n")
    summary = await orchestrator.run(task)

    # 6. 查看结果
    print("\n" + "="*60)
    print("执行摘要:")
    print(f"  成功: {summary.success}")
    print(f"  总步骤: {summary.total_steps}")
    print(f"  成功步骤: {summary.successful_steps}")
    print(f"  失败步骤: {summary.failed_steps}")
    print(f"  最终答案: {summary.final_answer}")
    print("="*60)


async def single_tool_example():
    """单工具使用示例"""
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    # 只使用计算器工具
    tools = {
        "calculator": create_example_tools()["calculator"],
    }

    orchestrator = ReflexionOrchestrator(
        llm=llm,
        tools=tools,
        max_steps=5,
        verbose=True,
    )

    task = "计算 100 除以 4，然后将结果乘以 3"

    summary = await orchestrator.run(task)

    print(f"\n最终结果: {summary.final_answer}")


async def error_recovery_example():
    """错误恢复示例"""
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    tools = create_example_tools()

    orchestrator = ReflexionOrchestrator(
        llm=llm,
        tools=tools,
        max_steps=15,
        verbose=True,
    )

    # 这个任务会先失败（除零），然后反思并纠正
    task = "计算 100 除以 0，如果失败，则改为计算 100 除以 5"

    summary = await orchestrator.run(task)

    print(f"\n任务{'成功' if summary.success else '失败'}完成")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(basic_usage_example())
