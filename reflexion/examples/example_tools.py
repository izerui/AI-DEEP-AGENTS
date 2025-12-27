"""示例工具集"""

from typing import Optional
from pydantic import BaseModel, Field
from reflexion.tools.base_tool import ReflexionTool


# ========== 工具输入Schema ==========

class CalculatorInput(BaseModel):
    """计算器输入"""
    a: float = Field(description="第一个数字")
    b: float = Field(description="第二个数字")
    operation: str = Field(description="操作: add, subtract, multiply, divide")


class SearchInput(BaseModel):
    """搜索输入"""
    query: str = Field(description="搜索查询")


class TextAnalyzerInput(BaseModel):
    """文本分析输入"""
    text: str = Field(description="要分析的文本")
    operation: str = Field(description="操作: count_words, count_chars, to_upper, to_lower")


# ========== 示例工具 ==========

class CalculatorTool(ReflexionTool):
    """计算器工具 - 执行基本数学运算"""

    name: str = "calculator"
    description:  str = "执行基本数学运算: 加(add)、减(subtract)、乘(multiply)、除(divide)"
    args_schema: CalculatorInput = CalculatorInput

    def _run(self, a: float, b: float, operation: str) -> str:
        """执行计算"""
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


class SearchTool(ReflexionTool):
    """搜索工具 - 模拟网络搜索"""

    name: str = "search"
    description: str = "模拟网络搜索，返回与查询相关的信息"
    args_schema: SearchInput = SearchInput

    # 模拟数据库
    knowledge_base = {
        "python": "Python是一种高级编程语言，由Guido van Rossum于1991年创建。",
        "langchain": "LangChain是一个用于开发由语言模型驱动的应用程序的框架。",
        "reflexion": "Reflexion是一种让AI系统通过反思和自我纠正来改进的方法。",
        "openai": "OpenAI是一家人工智能研究公司，开发了GPT系列模型。",
        "agent": "AI Agent是能够感知环境并采取行动以实现目标的智能体。",
    }

    def _run(self, query: str) -> str:
        """执行搜索"""
        query_lower = query.lower()

        # 查找匹配的知识
        results = []
        for key, value in self.knowledge_base.items():
            if key in query_lower or query_lower in key:
                results.append(f"- {key}: {value}")

        if results:
            return "搜索结果:\n" + "\n".join(results)
        else:
            return f"未找到关于 '{query}' 的信息。尝试搜索: python, langchain, reflexion, openai, agent"


class TextAnalyzerTool(ReflexionTool):
    """文本分析工具"""

    name: str = "text_analyzer"
    description: str = "分析文本: count_words(词数), count_chars(字符数), to_upper(转大写), to_lower(转小写)"
    args_schema: TextAnalyzerInput = TextAnalyzerInput

    def _run(self, text: str, operation: str) -> str:
        """执行文本分析"""
        try:
            if operation == "count_words":
                word_count = len(text.split())
                return f"文本 '{text[:30]}...' 包含 {word_count} 个单词"

            elif operation == "count_chars":
                char_count = len(text)
                return f"文本 '{text[:30]}...' 包含 {char_count} 个字符"

            elif operation == "to_upper":
                return text.upper()

            elif operation == "to_lower":
                return text.lower()

            else:
                return f"错误: 未知操作 '{operation}'"

        except Exception as e:
            return f"文本分析错误: {str(e)}"


class FileTool(ReflexionTool):
    """文件操作工具"""

    name: str = "file_operations"
    description: str = "文件操作: read_file(读取文件), write_file(写入文件), list_files(列出文件)"
    args_schema: str = TextAnalyzerInput  # 复用schema

    def _run(self, text: str, operation: str) -> str:
        """执行文件操作（模拟）"""
        if operation == "read_file":
            return f"[模拟] 读取文件内容: {text}"

        elif operation == "write_file":
            return f"[模拟] 写入文件: {text}"

        elif operation == "list_files":
            return "[模拟] 文件列表:\n- file1.txt\n- file2.txt\n- document.docx"

        else:
            return f"错误: 未知操作 '{operation}'"


class APITool(ReflexionTool):
    """API调用工具（模拟）"""

    name: str = "api_call"
    description: str = "模拟API调用: get_weather(天气), get_stock(股票), get_news(新闻)"
    args_schema: str = SearchInput

    def _run(self, query: str) -> str:
        """执行API调用"""
        query_lower = query.lower()

        if "weather" in query_lower or "天气" in query_lower:
            return "天气查询: 今天晴朗，温度25°C，适合户外活动。"

        elif "stock" in query_lower or "股票" in query_lower:
            return "股票查询: AAPL $178.32 (+1.2%), MSFT $378.91 (+0.8%)"

        elif "news" in query_lower or "新闻" in query_lower:
            return "新闻: AI技术持续突破，多模态模型应用前景广阔。"

        else:
            return f"未知API查询: {query}. 可用: weather, stock, news"


# 工具工厂函数
def create_example_tools() -> dict:
    """创建所有示例工具"""
    return {
        "calculator": CalculatorTool(),
        "search": SearchTool(),
        "text_analyzer": TextAnalyzerTool(),
        "file_operations": FileTool(),
        "api_call": APITool(),
    }
