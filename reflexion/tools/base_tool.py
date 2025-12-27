"""基础工具类"""

from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool as LangchainBaseTool


class ToolInputSchema(BaseModel):
    """工具输入Schema基类"""
    pass


class ReflexionTool(LangchainBaseTool):
    """
    Reflexion框架的基础工具类

    继承自 LangChain 的 BaseTool，提供：
    - 标准化的输入验证
    - 统一的错误处理
    - 详细的执行日志
    - 结果格式化
    """

    name: str = ""
    description: str = ""
    args_schema: Type[BaseModel] = ToolInputSchema

    class Config:
        arbitrary_types_allowed = True

    def _run(self, **kwargs) -> Any:
        """同步执行（可选实现）"""
        raise NotImplementedError("请实现 _run 或 _arun 方法")

    async def _arun(self, **kwargs) -> Any:
        """异步执行"""
        # 默认调用同步方法
        return self._run(**kwargs)

    def validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证输入参数

        Args:
            input_data: 输入参数字典

        Returns:
            验证后的参数字典

        Raises:
            ValidationError: 验证失败
        """
        if self.args_schema != ToolInputSchema:
            schema = self.args_schema(**input_data)
            return schema.dict()
        return input_data

    def format_output(self, result: Any) -> str:
        """
        格式化输出结果

        Args:
            result: 原始结果

        Returns:
            格式化后的字符串
        """
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            return "\n".join([f"{k}: {v}" for k, v in result.items()])
        else:
            return str(result)


def create_tool(
    name: str,
    description: str,
    func: callable,
    args_schema: Optional[Type[BaseModel]] = None,
) -> ReflexionTool:
    """
    快速创建工具的工厂函数

    Args:
        name: 工具名称
        description: 工具描述
        func: 执行函数
        args_schema: 参数Schema

    Returns:
        ReflexionTool 实例

    Example:
        ```python
        def my_calculator(a: int, b: int) -> int:
            return a + b

        calculator_tool = create_tool(
            name="calculator",
            description="加法计算器",
            func=my_calculator,
        )
        ```
    """
    # 动态创建工具类
    class DynamicTool(ReflexionTool):
        name = name
        description = description

        if args_schema:
            args_schema = args_schema

        def _run(self, **kwargs):
            return func(**kwargs)

        async def _arun(self, **kwargs):
            # 如果函数是协程，则await
            import inspect
            if inspect.iscoroutinefunction(func):
                return await func(**kwargs)
            return func(**kwargs)

    return DynamicTool()
