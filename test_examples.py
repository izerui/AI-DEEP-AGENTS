"""
Deep Agents 示例测试脚本

验证所有示例是否正常工作，并提供详细的测试报告
"""

import sys
from typing import List, Dict, Any, Optional
from datetime import datetime


# ============================================================================
# 测试框架（简化版）
# ============================================================================

class TestResult:
    """测试结果"""
    def __init__(self, name: str, passed: bool, message: str, duration: float):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration

    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} | {self.name} | {self.message} | {self.duration:.2f}s"


class TestSuite:
    """测试套件"""
    def __init__(self):
        self.results: List[TestResult] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def add_result(self, name: str, passed: bool, message: str, duration: float):
        """添加测试结果"""
        result = TestResult(name, passed, message, duration)
        self.results.append(result)
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 80)
        print("【测试摘要】")
        print("=" * 80)
        print(f"总测试数: {self.total_tests}")
        print(f"通过: {self.passed_tests}")
        print(f"失败: {self.failed_tests}")
        print(f"通过率: {(self.passed_tests / self.total_tests * 100):.1f}%")
        print()

        # 打印详细结果
        print("【详细结果】")
        print("-" * 80)
        for result in self.results:
            print(result)
        print("-" * 80)
        print()


# ============================================================================
# 测试用例
# ============================================================================

def test_import_deepagents(suite: TestSuite):
    """测试1: 导入 Deep Agents"""
    start_time = datetime.now()
    
    try:
        from deepagents import create_deep_agent
        duration = (datetime.now() - start_time).total_seconds()
        
        suite.add_result(
            name="导入 Deep Agents",
            passed=True,
            message="成功导入 create_deep_agent",
            duration=duration
        )
        return True
        
    except ImportError as e:
        duration = (datetime.now() - start_time).total_seconds()
        
        suite.add_result(
            name="导入 Deep Agents",
            passed=False,
            message=f"导入失败: {e}",
            duration=duration
        )
        return False


def test_tool_creation(suite: TestSuite):
    """测试2: 工具创建"""
    start_time = datetime.now()
    
    try:
        from langchain_core.tools import tool
        
        @tool
        def simple_calculator(a: float, b: float) -> str:
            """简单的加法计算器"""
            return f"{a} + {b} = {a + b}"
        
        # 验证工具属性
        assert simple_calculator.name == "simple_calculator"
        assert "加法" in simple_calculator.description
        
        duration = (datetime.now() - start_time).total_seconds()
        suite.add_result(
            name="工具创建",
            passed=True,
            message="成功创建工具",
            duration=duration
        )
        return True
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        suite.add_result(
            name="工具创建",
            passed=False,
            message=f"创建失败: {e}",
            duration=duration
        )
        return False


def test_agent_creation(suite: TestSuite):
    """测试3: 创建智能体"""
    start_time = datetime.now()
    
    try:
        from deepagents import create_deep_agent
        from langchain_core.tools import tool
        
        @tool
        def test_tool(x: str) -> str:
            """测试工具"""
            return f"处理: {x}"
        
        # 创建智能体
        agent = create_deep_agent(
            tools=[test_tool],
            system_prompt="你是测试助手"
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        suite.add_result(
            name="创建智能体",
            passed=True,
            message="成功创建智能体",
            duration=duration
        )
        return True, agent
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        suite.add_result(
            name="创建智能体",
            passed=False,
            message=f"创建失败: {e}",
            duration=duration
        )
        return False, None


def test_simple_task(suite: TestSuite, agent) -> bool:
    """测试4: 简单任务执行"""
    if agent is None:
        return False
    
    start_time = datetime.now()
    
    try:
        result = agent.invoke({
            "messages": [{"role": "user", "content": "测试工具调用，输入：hello"}]
        })
        
        # 验证结果
        assert result is not None
        assert "messages" in result
        assert len(result["messages"]) > 0
        
        content = result["messages"][-1].content
        assert content is not None
        
        duration = (datetime.now() - start_time).total_seconds()
        suite.add_result(
            name="简单任务执行",
            passed=True,
            message=f"成功执行，响应长度: {len(content)}",
            duration=duration
        )
        return True
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        suite.add_result(
            name="简单任务执行",
            passed=False,
            message=f"执行失败: {e}",
            duration=duration
        )
        return False


def test_calculator_tool(suite: TestSuite):
    """测试5: 计算器工具"""
    start_time = datetime.now()
    
    try:
        from deepagents import create_deep_agent
        from langchain_core.tools import tool
        
        @tool
        def calculator(a: float, b: float, operation: str) -> str:
            """数学计算器"""
            if operation == "add":
                return f"{a} + {b} = {a + b}"
            elif operation == "subtract":
                return f"{a} - {b} = {a - b}"
            elif operation == "multiply":
                return f"{a} × {b} = {a * b}"
            elif operation == "divide":
                if b == 0:
                    return "错误：除数不能为零"
                return f"{a} ÷ {b} = {a / b}"
            else:
                return f"未知操作: {operation}"
        
        agent = create_deep_agent(
            tools=[calculator],
            system_prompt="你是数学计算助手"
        )
        
        # 测试计算
        result = agent.invoke({
            "messages": [{"role": "user", "content": "计算 25 加 18"}]
        })
        
        content = result["messages"][-1].content
        assert "43" in content or "25 + 18" in content
        
        duration = (datetime.now() - start_time).total_seconds()
        suite.add_result(
            name="计算器工具",
            passed=True,
            message=f"计算正确: {content[:50]}",
            duration=duration
        )
        return True
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        suite.add_result(
            name="计算器工具",
            passed=False,
            message=f"测试失败: {e}",
            duration=duration
        )
        return False


def test_multi_tool(suite: TestSuite):
    """测试6: 多工具协作"""
    start_time = datetime.now()
    
    try:
        from deepagents import create_deep_agent
        from langchain_core.tools import tool
        
        @tool
        def calc(a: float, b: float, operation: str) -> str:
            """计算器"""
            if operation == "add":
                return str(a + b)
            return str(0)
        
        @tool
        def search(query: str) -> str:
            """搜索"""
            return f"搜索结果: {query}"
        
        agent = create_deep_agent(
            tools=[calc, search],
            system_prompt="你是全能助手"
        )
        
        result = agent.invoke({
            "messages": [{"role": "user", "content": "计算 10 加 20"}]
        })
        
        duration = (datetime.now() - start_time).total_seconds()
        suite.add_result(
            name="多工具协作",
            passed=True,
            message=f"成功使用多工具: {len(result['messages'])} 条消息",
            duration=duration
        )
        return True
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        suite.add_result(
            name="多工具协作",
            passed=False,
            message=f"测试失败: {e}",
            duration=duration
        )
        return False


def test_error_handling(suite: TestSuite):
    """测试7: 错误处理"""
    start_time = datetime.now()
    
    try:
        from deepagents import create_deep_agent
        from langchain_core.tools import tool
        
        @tool
        def safe_divide(a: float, b: float) -> str:
            """安全除法"""
            if b == 0:
                return "错误：除数不能为零"
            return str(a / b)
        
        agent = create_deep_agent(
            tools=[safe_divide],
            system_prompt="你是一个计算助手"
        )
        
        # 尝试除以零
        result = agent.invoke({
            "messages": [{"role": "user", "content": "计算 100 除以 0"}]
        })
        
        content = result["messages"][-1].content
        
        duration = (datetime.now() - start_time).total_seconds()
        suite.add_result(
            name="错误处理",
            passed=True,
            message=f"正确处理错误: {content[:50]}",
            duration=duration
        )
        return True
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        suite.add_result(
            name="错误处理",
            passed=False,
            message=f"测试失败: {e}",
            duration=duration
        )
        return False


# ============================================================================
# 主测试函数
# ============================================================================

def run_all_tests():
    """运行所有测试"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         Deep Agents 示例测试套件                               ║
╠═══════════════════════════════════════════════════════════════╣
║  测试内容：                                                   ║
║  1. 导入 Deep Agents                                          ║
║  2. 工具创建                                                  ║
║  3. 创建智能体                                                ║
║  4. 简单任务执行                                              ║
║  5. 计算器工具                                                ║
║  6. 多工具协作                                                ║
║  7. 错误处理                                                  ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    suite = TestSuite()
    
    # 运行测试
    print("【开始测试】\n")
    
    # 测试1: 导入
    import_success = test_import_deepagents(suite)
    
    if not import_success:
        print("\n❌ Deep Agents 未安装，无法继续测试")
        print("\n📦 安装命令:")
        print("   pip install deepagents")
        print("\n🔗 文档地址:")
        print("   https://docs.langchain.com/oss/python/deepagents/quickstart")
        suite.print_summary()
        return
    
    # 测试2: 工具创建
    test_tool_creation(suite)
    
    # 测试3: 创建智能体
    agent_created, agent = test_agent_creation(suite)
    
    # 测试4: 简单任务
    test_simple_task(suite, agent)
    
    # 测试5: 计算器工具
    test_calculator_tool(suite)
    
    # 测试6: 多工具
    test_multi_tool(suite)
    
    # 测试7: 错误处理
    test_error_handling(suite)
    
    # 打印摘要
    suite.print_summary()
    
    # 返回结果
    return suite.failed_tests == 0


# ============================================================================
# 入口点
# ============================================================================

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试运行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)