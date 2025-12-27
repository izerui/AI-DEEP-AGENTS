"""
Reflexion API 客户端使用示例

演示如何使用 OpenAI SDK 或标准 HTTP 客户端调用 Reflexion API
"""

import os
from openai import OpenAI
import requests


# ========== 配置 ==========

API_BASE = "http://localhost:8000"
API_KEY = os.getenv("RAG_API_KEYS", "your-api-key")


# ========== 使用 OpenAI SDK ==========

def use_openai_sdk():
    """
    使用 OpenAI SDK 调用 Reflexion API

    这是最简单的方式，完全兼容 OpenAI 的调用方式
    """
    print("="*60)
    print("使用 OpenAI SDK 调用 Reflexion")
    print("="*60 + "\n")

    client = OpenAI(
        base_url=f"{API_BASE}/reflexion",
        api_key=API_KEY,
    )

    # 示例 1: 标准聊天
    print("示例 1: 标准聊天")
    response = client.chat.completions.create(
        model="reflexion",
        messages=[
            {"role": "system", "content": "你是一个有帮助的助手"},
            {"role": "user", "content": "计算 25 加 18，然后搜索关于 python 的信息"},
        ],
        max_steps=10,
    )

    print(f"回复: {response.choices[0].message.content}\n")

    # 示例 2: 使用多智能体协作
    print("示例 2: 多智能体协作")
    response = client.chat.completions.create(
        model="reflexion-collaboration",
        messages=[
            {"role": "user", "content": "完成一个复杂的多步骤任务：计算 100 除以 4"}
        ],
        use_collaboration=True,
        max_steps=5,
    )

    print(f"回复: {response.choices[0].message.content}\n")

    # 示例 3: 列出可用模型
    print("示例 3: 列出可用模型")
    models = client.models.list()
    print("可用模型:")
    for model in models.data:
        print(f"  - {model.id}")
    print()


# ========== 使用 HTTP 客户端 ==========

def use_http_client():
    """
    使用标准 HTTP 客户端调用 Reflexion API
    """
    print("="*60)
    print("使用 HTTP 客户端调用 Reflexion")
    print("="*60 + "\n")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    # 示例 1: 聊天完成
    print("示例 1: 聊天完成")
    response = requests.post(
        f"{API_BASE}/reflexion/chat/completions",
        headers=headers,
        json={
            "model": "reflexion",
            "messages": [
                {"role": "user", "content": "计算 15 乘以 7"}
            ],
            "max_steps": 10,
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"回复: {data['choices'][0]['message']['content']}\n")
    else:
        print(f"错误: {response.status_code} - {response.text}\n")

    # 示例 2: 直接任务执行
    print("示例 2: 直接任务执行")
    response = requests.post(
        f"{API_BASE}/reflexion/task",
        headers=headers,
        json={
            "task": "搜索关于 langchain 的信息",
            "max_steps": 10,
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"成功: {data['success']}")
        print(f"总步骤: {data['total_steps']}")
        print(f"成功步骤: {data['successful_steps']}")
        print(f"最终答案: {data['final_answer']}\n")
    else:
        print(f"错误: {response.status_code} - {response.text}\n")

    # 示例 3: 列出模型
    print("示例 3: 列出模型")
    response = requests.get(f"{API_BASE}/reflexion/models", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print("可用模型:")
        for model in data['data']:
            print(f"  - {model['id']}")
    print()

    # 示例 4: 健康检查
    print("示例 4: 健康检查")
    response = requests.get(f"{API_BASE}/reflexion/health", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"服务状态: {data['status']}")
        print(f"版本: {data['version']}\n")


# ========== 高级用法 ==========

def advanced_usage():
    """
    高级用法示例
    """
    print("="*60)
    print("高级用法示例")
    print("="*60 + "\n")

    client = OpenAI(
        base_url=f"{API_BASE}/reflexion",
        api_key=API_KEY,
    )

    # 流式输出（如果支持）
    print("示例: 流式输出")
    try:
        stream = client.chat.completions.create(
            model="reflexion",
            messages=[{"role": "user", "content": "统计文本 'hello world' 的单词数"}],
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="")
        print("\n")

    except Exception as e:
        print(f"流式输出暂不支持: {e}\n")


# ========== Python 集成示例 ==========

def integrate_with_code():
    """
    在 Python 代码中集成 Reflexion
    """
    print("="*60)
    print("Python 代码集成示例")
    print("="*60 + "\n")

    from openai import OpenAI

    client = OpenAI(
        base_url=f"{API_BASE}/reflexion",
        api_key=API_KEY,
    )

    def reflexion_task(task: str) -> str:
        """
        封装的 Reflexion 任务函数

        Args:
            task: 任务描述

        Returns:
            执行结果
        """
        response = client.chat.completions.create(
            model="reflexion",
            messages=[{"role": "user", "content": task}],
            max_steps=15,
        )
        return response.choices[0].message.content

    # 使用示例
    result = reflexion_task("计算 25 乘以 4，然后除以 2")
    print(f"结果: {result}\n")


# ========== 主函数 ==========

def main():
    """运行所有示例"""
    print("\n" + "="*60)
    print("Reflexion API 客户端示例")
    print("="*60 + "\n")

    try:
        # OpenAI SDK 方式
        use_openai_sdk()

        # HTTP 客户端方式
        use_http_client()

        # 高级用法
        advanced_usage()

        # 代码集成
        integrate_with_code()

    except Exception as e:
        print(f"\n错误: {e}")
        print("请确保:")
        print("1. 服务器正在运行 (python main.py)")
        print("2. API_KEY 配置正确")
        print("3. 安装了必要的库: pip install openai requests")


if __name__ == "__main__":
    main()
