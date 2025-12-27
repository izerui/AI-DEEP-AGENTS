"""工具注册器 - 管理所有可用工具"""

from typing import Dict, List, Optional, Type, Any
from langchain_core.tools import BaseTool
from reflexion.tools.base_tool import ReflexionTool, create_tool


class ToolRegistry:
    """
    工具注册器 - 管理和注册所有工具

    特性：
    - 工具注册和检索
    - 工具分类管理
    - 工具依赖检查
    - 工具元数据管理
    """

    def __init__(self):
        """初始化工具注册器"""
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        tool: BaseTool,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        注册工具

        Args:
            tool: 工具实例
            category: 工具分类
            metadata: 元数据

        Raises:
            ValueError: 工具名称已存在
        """
        name = tool.name

        if name in self._tools:
            raise ValueError(f"工具 '{name}' 已存在")

        self._tools[name] = tool

        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(name)

        self._metadata[name] = metadata or {}

    def register_function(
        self,
        name: str,
        func: callable,
        description: str,
        category: str = "general",
        args_schema: Optional[Type] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        注册函数为工具

        Args:
            name: 工具名称
            func: 函数
            description: 描述
            category: 分类
            args_schema: 参数Schema
            metadata: 元数据
        """
        tool = create_tool(
            name=name,
            description=description,
            func=func,
            args_schema=args_schema,
        )

        self.register(tool, category, metadata)

    def get(self, name: str) -> Optional[BaseTool]:
        """
        获取工具

        Args:
            name: 工具名称

        Returns:
            工具实例或None
        """
        return self._tools.get(name)

    def get_all(self) -> Dict[str, BaseTool]:
        """获取所有工具"""
        return self._tools.copy()

    def get_by_category(self, category: str) -> List[BaseTool]:
        """
        获取指定分类的工具

        Args:
            category: 分类名称

        Returns:
            工具列表
        """
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def list_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self._categories.keys())

    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """
        列出工具名称

        Args:
            category: 可选，筛选分类

        Returns:
            工具名称列表
        """
        if category:
            return self._categories.get(category, []).copy()
        return list(self._tools.keys())

    def unregister(self, name: str) -> bool:
        """
        注销工具

        Args:
            name: 工具名称

        Returns:
            是否成功
        """
        if name not in self._tools:
            return False

        # 从分类中移除
        for category_tools in self._categories.values():
            if name in category_tools:
                category_tools.remove(name)

        # 从注册器中移除
        del self._tools[name]
        del self._metadata[name]

        return True

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """
        获取工具元数据

        Args:
            name: 工具名称

        Returns:
            元数据字典
        """
        return self._metadata.get(name, {}).copy()

    def update_metadata(self, name: str, metadata: Dict[str, Any]) -> bool:
        """
        更新工具元数据

        Args:
            name: 工具名称
            metadata: 新的元数据

        Returns:
            是否成功
        """
        if name not in self._tools:
            return False

        self._metadata[name].update(metadata)
        return True

    def get_description(self, name: str) -> str:
        """
        获取工具描述

        Args:
            name: 工具名称

        Returns:
            工具描述
        """
        tool = self._tools.get(name)
        if tool:
            return getattr(tool, "description", "")
        return ""

    def format_for_llm(self, category: Optional[str] = None) -> str:
        """
        格式化工具列表供LLM使用

        Args:
            category: 可选，筛选分类

        Returns:
            格式化的工具列表字符串
        """
        lines = ["可用工具：\n"]

        tools = self.get_by_category(category) if category else self._tools.values()

        for tool in tools:
            name = tool.name
            desc = getattr(tool, "description", "无描述")
            lines.append(f"- {name}: {desc}")

        return "\n".join(lines)

    def check_dependencies(self, name: str) -> Dict[str, bool]:
        """
        检查工具依赖

        Args:
            name: 工具名称

        Returns:
            依赖检查结果 {dependency_name: available}
        """
        metadata = self._metadata.get(name, {})
        dependencies = metadata.get("dependencies", {})

        results = {}
        for dep_name, dep_check_func in dependencies.items():
            try:
                results[dep_name] = dep_check_func()
            except:
                results[dep_name] = False

        return results

    def __len__(self) -> int:
        """返回工具数量"""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools

    def __repr__(self) -> str:
        """字符串表示"""
        return f"ToolRegistry(tools={len(self._tools)}, categories={list(self._categories.keys())})"


# 全局工具注册器实例
_global_registry = ToolRegistry()


def get_global_registry() -> ToolRegistry:
    """获取全局工具注册器"""
    return _global_registry


def register_tool(
    tool: BaseTool,
    category: str = "general",
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    注册工具到全局注册器

    Args:
        tool: 工具实例
        category: 分类
        metadata: 元数据
    """
    _global_registry.register(tool, category, metadata)


def register_function(
    name: str,
    func: callable,
    description: str,
    category: str = "general",
    args_schema: Optional[Type] = None,
) -> None:
    """
    注册函数到全局注册器

    Args:
        name: 工具名称
        func: 函数
        description: 描述
        category: 分类
        args_schema: 参数Schema
    """
    _global_registry.register_function(
        name=name,
        func=func,
        description=description,
        category=category,
        args_schema=args_schema,
    )
