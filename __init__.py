"""
Deep Agents 对比示例包

本包展示了如何使用 LangChain 的 Deep Agents 框架来简化 ReAct 智能体的实现。

包内容：
- comparison.py: Reflexion vs Deep Agents 的完整对比
- deepagents_simple.py: Deep Agents 的实际运行示例
- quickstart.py: 从零开始的快速入门指南
- test_examples.py: 示例测试脚本

主要功能：
1. 展示 Deep Agents 的简化代码实现
2. 与自定义 Reflexion 实现进行对比
3. 提供混合方案（Deep Agents + 反思库）
4. 提供完整的测试和验证脚本

快速开始：
    # 1. 安装依赖
    pip install deepagents

    # 2. 运行对比示例
    python -m deepagents_demo.comparison

    # 3. 运行实际示例
    python -m deepagents_demo.deepagents_simple

    # 4. 学习快速入门
    python -m deepagents_demo.quickstart

    # 5. 运行测试
    python -m deepagents_demo.test_examples

相关资源：
- 官方文档: https://docs.langchain.com/oss/python/deepagents/quickstart
- 项目文档: README.md
"""

__version__ = "0.1.0"
__author__ = "Paper RAG Team"

# 导出主要内容（方便用户直接使用）
from . import (
    comparison,
    deepagents_simple,
    quickstart,
    test_examples,
)

__all__ = [
    # 模块
    "comparison",
    "deepagents_simple",
    "quickstart",
    "test_examples",
    # 版本
    "__version__",
]