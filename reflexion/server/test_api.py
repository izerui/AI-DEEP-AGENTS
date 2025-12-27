#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reflexion API 端点测试

快速测试各个端点是否正常工作
"""

import os
import sys
import asyncio
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(dotenv_path='.env', verbose=True)

# 配置
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
API_KEY = os.getenv("RAG_API_KEYS", "test-key")


def print_section(title):
    """打印分节标题"""
    print("\n" + "="*60)
    print(title)
    print("="*60)


def test_health():
    """测试健康检查端点"""
    print_section("测试健康检查端点")

    headers = {"Authorization": f"Bearer {API_KEY}"}

    try:
        response = requests.get(f"{API_BASE}/reflexion/health", headers=headers)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ 服务状态: {data['status']}")
            print(f"✓ 版本: {data['version']}")
            print(f"✓ 已初始化: {data['initialized']}")
            return True
        else:
            print(f"✗ 错误: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return False


def test_models():
    """测试模型列表端点"""
    print_section("测试模型列表端点")

    headers = {"Authorization": f"Bearer {API_KEY}"}

    try:
        response = requests.get(f"{API_BASE}/reflexion/models", headers=headers)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ 可用模型:")
            for model in data['data']:
                print(f"  - {model['id']}")
            return True
        else:
            print(f"✗ 错误: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False


def test_chat_completions():
    """测试聊天完成端点"""
    print_section("测试聊天完成端点")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "reflexion",
        "messages": [
            {"role": "user", "content": "计算 5 加 3"}
        ],
        "max_steps": 5,
    }

    try:
        print(f"发送请求: {payload['messages'][0]['content']}")
        response = requests.post(
            f"{API_BASE}/reflexion/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,  # 给足够的时间执行
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ 响应 ID: {data['id']}")
            print(f"✓ 模型: {data['model']}")
            print(f"✓ 回复: {data['choices'][0]['message']['content']}")
            print(f"✓ Token 使用: {data['usage']}")
            return True
        else:
            print(f"✗ 错误: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False


def test_task():
    """测试任务执行端点"""
    print_section("测试任务执行端点")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "task": "搜索关于 reflexion 的信息",
        "max_steps": 5,
    }

    try:
        print(f"发送任务: {payload['task']}")
        response = requests.post(
            f"{API_BASE}/reflexion/task",
            headers=headers,
            json=payload,
            timeout=60,
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ 成功: {data['success']}")
            print(f"✓ 总步骤: {data['total_steps']}")
            print(f"✓ 成功步骤: {data['successful_steps']}")
            print(f"✓ 失败步骤: {data['failed_steps']}")
            print(f"✓ 最终答案: {data['final_answer'][:100]}...")
            return True
        else:
            print(f"✗ 错误: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False


def test_stats():
    """测试统计信息端点"""
    print_section("测试统计信息端点")

    headers = {"Authorization": f"Bearer {API_KEY}"}

    try:
        response = requests.get(f"{API_BASE}/reflexion/stats", headers=headers)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ 工具数量: {data['tools_count']}")
            print(f"✓ 编排器统计: {data.get('orchestrator', {})}")
            return True
        else:
            print(f"✗ 错误: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Reflexion API 端点测试")
    print("="*60)
    print(f"API Base: {API_BASE}")
    print(f"API Key: {API_KEY[:8]}...")

    # 检查服务器是否运行
    print("\n检查服务器连接...")
    try:
        response = requests.get(f"{API_BASE}/", timeout=5)
        print(f"✓ 服务器正在运行")
    except:
        print(f"✗ 无法连接到服务器，请先启动: python main.py")
        return

    # 运行测试
    results = []

    results.append(("健康检查", test_health()))
    results.append(("模型列表", test_models()))
    results.append(("聊天完成", test_chat_completions()))
    results.append(("任务执行", test_task()))
    results.append(("统计信息", test_stats()))

    # 汇总结果
    print_section("测试结果汇总")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
