"""多智能体协作使用示例"""

import asyncio
from langchain_openai import ChatOpenAI
from reflexion import CollaborativeAgents
from reflexion.examples.example_tools import create_example_tools


async def basic_collaboration_example():
    """
    基础协作示例

    演示规划者、执行者、批判者三个智能体的协作
    """
    print("\n" + "="*60)
    print("多智能体协作示例")
    print("="*60 + "\n")

    # 初始化 LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    # 准备工具
    tools = create_example_tools()

    # 创建协作智能体
    agents = CollaborativeAgents(
        llm=llm,
        tools=tools,
        verbose=True,
    )

    # 定义任务
    task = "计算 25 加 18，然后搜索关于 python 的信息"

    # 运行协作
    result = await agents.run(
        task=task,
        max_iterations=3,
        quality_threshold=0.7,
    )

    # 查看结果
    print("\n" + "="*60)
    print("协作结果:")
    print(f"  成功: {result.success}")
    print(f"  迭代次数: {result.iterations}")
    print(f"  最终结果: {result.final_result}")
    print("="*60 + "\n")


async def multi_model_collaboration_example():
    """
    多模型协作示例

    演示使用不同的 LLM 来优化成本和质量
    - GPT-4 用于规划和审查（高质量要求）
    - GPT-3.5 用于执行（快速高效）
    """
    print("\n" + "="*60)
    print("多模型协作示例 - 成本优化")
    print("="*60 + "\n")

    # 使用不同模型
    planner_llm = ChatOpenAI(model="gpt-4", temperature=0)
    executor_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    critic_llm = ChatOpenAI(model="gpt-4", temperature=0)

    tools = create_example_tools()

    # 创建使用不同模型的协作智能体
    agents = CollaborativeAgents(
        llm=executor_llm,  # 默认模型
        tools=tools,
        planner_llm=planner_llm,  # 强大的规划
        executor_llm=executor_llm,  # 快速执行
        critic_llm=critic_llm,  # 严格审查
        verbose=True,
    )

    task = "完成一个复杂的任务：计算 100 除以 4，然后将结果乘以 3"

    result = await agents.run(
        task=task,
        max_iterations=2,
        quality_threshold=0.8,
    )

    print(f"\n任务完成，迭代 {result.iterations} 次")


async def with_callbacks_example():
    """
    使用回调函数的协作示例
    """
    print("\n" + "="*60)
    print("协作 + 回调示例")
    print("="*60 + "\n")

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    tools = create_example_tools()

    agents = CollaborativeAgents(
        llm=llm,
        tools=tools,
        verbose=False,
    )

    # 定义回调
    async def on_plan(plan):
        print(f"[规划] 计划已生成")

    async def on_execute(result):
        status = "✓" if result.get("success") else "✗"
        print(f"[执行] {status} {result.get('tool_used', 'N/A')}")

    async def on_review(review):
        status = "✓ 通过" if review.get("passed") else "✗ 未通过"
        print(f"[审查] {status}")

    # 设置回调
    agents.on_plan_callback = on_plan
    agents.on_execute_callback = on_execute
    agents.on_review_callback = on_review

    task = "计算 15 乘以 7"
    result = await agents.run(task, max_iterations=2)

    print(f"\n最终: {'成功' if result.success else '失败'}")


async def independent_agents_example():
    """
    独立使用各个智能体的示例
    """
    from reflexion import PlannerAgent, ExecutorAgent, CriticAgent

    print("\n" + "="*60)
    print("独立使用智能体示例")
    print("="*60 + "\n")

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    tools = create_example_tools()

    # 1. 规划者
    print("[1] 规划阶段")
    planner = PlannerAgent(llm=llm)
    plan = await planner.plan(
        task="完成数据分析和报告生成",
        available_tools=list(tools.keys()),
    )
    print(f"计划: {plan['raw_plan'][:100]}...\n")

    # 2. 执行者
    print("[2] 执行阶段")
    executor = ExecutorAgent(llm=llm, tools=tools)
    result = await executor.execute_step(
        step_description="计算 25 加 18",
        context={},
    )
    print(f"执行结果: {result}\n")

    # 3. 批判者
    print("[3] 审查阶段")
    critic = CriticAgent(llm=llm, strictness=0.7)
    review = await critic.review(
        task="计算任务",
        execution_result=result,
    )
    print(f"审查: {review['review_content'][:100]}...\n")


async def quality_control_example():
    """
    质量控制示例 - 严格的质量阈值
    """
    print("\n" + "="*60)
    print("质量控制示例")
    print("="*60 + "\n")

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    tools = create_example_tools()

    # 创建严格的批判者
    from reflexion.agents.specialized import CriticAgent
    strict_critic = CriticAgent(llm=llm, strictness=0.9)

    agents = CollaborativeAgents(
        llm=llm,
        tools=tools,
        critic_llm=llm,
        verbose=False,
    )

    agents.critic = strict_critic

    task = "执行一个需要高质量输出的任务"
    result = await agents.run(
        task=task,
        max_iterations=5,  # 允许更多迭代
        quality_threshold=0.9,  # 高质量要求
    )

    print(f"质量检查: 迭代了 {result.iterations} 次达到质量要求")


async def main():
    """运行所有示例"""
    # 示例1: 基础协作
    await basic_collaboration_example()

    # 示例2: 多模型协作
    # await multi_model_collaboration_example()

    # 示例3: 使用回调
    # await with_callbacks_example()

    # 示例4: 独立智能体
    # await independent_agents_example()

    # 示例5: 质量控制
    # await quality_control_example()


if __name__ == "__main__":
    asyncio.run(main())
