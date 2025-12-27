"""高级使用示例"""

import asyncio
from typing import Optional
from langchain_openai import ChatOpenAI
from reflexion import ReflexionOrchestrator
from reflexion.core import OrchestratorConfig, Reflector
from reflexion.memory import ReflectionLibrary
from reflexion.examples.example_tools import create_example_tools


async def custom_config_example():
    """自定义配置示例"""
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    # 自定义配置
    config = OrchestratorConfig(
        max_steps=5,
        verbose=True,
        enable_reflection_library=True,
        early_stop_threshold=2,
    )

    tools = create_example_tools()

    orchestrator = ReflexionOrchestrator(
        llm=llm,
        tools=tools,
        config=config,
    )

    task = "搜索关于 langchain 的信息"
    summary = await orchestrator.run(task)

    print(f"结果: {summary.final_answer}")


async def with_callbacks_example():
    """使用回调函数示例"""
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    tools = create_example_tools()

    orchestrator = ReflexionOrchestrator(
        llm=llm,
        tools=tools,
        verbose=False,
    )

    # 定义回调
    async def on_step(step):
        print(f"步骤 {step.step_number}: {step.action}")

    async def on_complete(summary):
        print(f"\n完成! 共 {summary.total_steps} 步")
        print(f"成功: {summary.successful_steps}, 失败: {summary.failed_steps}")

    orchestrator.on_step_callback = on_step
    orchestrator.on_complete_callback = on_complete

    task = "计算 15 加 27"
    await orchestrator.run(task)


async def multi_task_example():
    """多任务顺序执行示例"""
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    tools = create_example_tools()

    orchestrator = ReflexionOrchestrator(
        llm=llm,
        tools=tools,
        max_steps=10,
        verbose=False,
    )

    tasks = [
        "计算 25 乘以 4",
        "搜索关于 reflexion 的信息",
        "将文本 'hello world' 转换为大写",
    ]

    print("执行多个任务...\n")

    for i, task in enumerate(tasks, 1):
        print(f"任务 {i}: {task}")
        summary = await orchestrator.run(task)
        print(f"  结果: {summary.final_answer}\n")

        # 重置状态以执行下一个任务
        orchestrator.reset()


async def with_reflection_library_example():
    """使用反思库示例"""
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    tools = create_example_tools()

    # 创建反思库
    reflection_library = ReflectionLibrary()

    # 添加自定义反思
    from reflexion.memory.reflection_library import ErrorType
    reflection_library.add_reflection(
        error_pattern="除数不能为零",
        error_type=ErrorType.PARAMETER_ERROR,
        reflection="检测到除零错误，应该检查除数并使用非零值",
        suggested_actions=[
            "将除数改为非零值",
            "添加除数验证逻辑",
        ],
    )

    # 创建编排器
    orchestrator = ReflexionOrchestrator(
        llm=llm,
        tools=tools,
        reflection_library=reflection_library,
        verbose=True,
    )

    # 这个任务会触发除零错误，反思库会提供帮助
    task = "计算 50 除以 0，然后根据错误信息纠正并计算 50 除以 5"

    summary = await orchestrator.run(task)

    print(f"\n反思库统计: {reflection_library.get_stats()}")


async def parallel_tools_example():
    """并行工具调用概念示例"""
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    tools = create_example_tools()

    orchestrator = ReflexionOrchestrator(
        llm=llm,
        tools=tools,
        max_steps=15,
        verbose=True,
    )

    # 任务需要使用多个工具
    task = """
    请依次完成以下操作:
    1. 计算 123 加 456
    2. 搜索关于 agent 的信息
    3. 统计文本 'artificial intelligence' 的单词数
    """

    summary = await orchestrator.run(task)

    print(f"\n最终答案: {summary.final_answer}")


async def export_and_analyze_example():
    """导出和分析历史示例"""
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    tools = create_example_tools()

    orchestrator = ReflexionOrchestrator(
        llm=llm,
        tools=tools,
        verbose=False,
    )

    # 执行任务
    task = "计算 100 除以 4"
    summary = await orchestrator.run(task)

    # 导出历史
    history = orchestrator.export_history()

    print("执行历史:")
    print(f"  任务: {history['task']}")
    print(f"  总步骤: {history['current_step']}")
    print(f"  统计: {history['stats']}")

    # 分析工具使用
    print("\n工具使用:")
    for tool, count in history['stats']['tool_usage'].items():
        print(f"  {tool}: {count} 次")


async def advanced_usage_example():
    """综合高级示例"""
    """高级使用示例 - 演示各种高级功能"""
    print("\n" + "="*60)
    print("高级使用示例")
    print("="*60 + "\n")

    # 示例1: 自定义配置
    print("1. 自定义配置示例")
    print("-" * 40)
    await custom_config_example()

    print("\n" + "="*60 + "\n")

    # 示例2: 使用回调
    print("2. 使用回调示例")
    print("-" * 40)
    await with_callbacks_example()

    print("\n" + "="*60 + "\n")

    # 示例3: 使用反思库
    print("3. 使用反思库示例")
    print("-" * 40)
    await with_reflection_library_example()

    print("\n" + "="*60 + "\n")

    # 示例4: 导出和分析
    print("4. 导出和分析示例")
    print("-" * 40)
    await export_and_analyze_example()


if __name__ == "__main__":
    # 运行高级示例
    asyncio.run(advanced_usage_example())
