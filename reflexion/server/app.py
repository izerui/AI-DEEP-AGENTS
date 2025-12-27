"""
FastAPI 服务器 - 将 Reflexion 暴露为 API

支持两种协议:
1. 标准 REST API
2. 兼容 OpenAI Chat Completions API
"""

from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from reflexion import ReflexionOrchestrator, CollaborativeAgents
from reflexion.examples.example_tools import create_example_tools
from langchain_openai import ChatOpenAI


# ========== 请求/响应模型 ==========

class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(description="消息角色: system, user, assistant")
    content: str = Field(description="消息内容")


class ChatCompletionRequest(BaseModel):
    """OpenAI 兼容的聊天完成请求"""
    model: str = Field(default="reflexion", description="模型名称")
    messages: List[ChatMessage] = Field(description="消息列表")
    temperature: Optional[float] = Field(default=0.7, description="温度参数")
    max_tokens: Optional[int] = Field(default=1000, description="最大token数")
    stream: Optional[bool] = Field(default=False, description="是否流式输出")
    tools: Optional[bool] = Field(default=True, description="是否启用工具")
    max_steps: Optional[int] = Field(default=10, description="最大执行步数")
    use_collaboration: Optional[bool] = Field(default=False, description="是否使用多智能体协作")


class ChatCompletionResponse(BaseModel):
    """OpenAI 兼容的聊天完成响应"""
    id: str = Field(description="响应ID")
    object: str = Field(default="chat.completion", description="对象类型")
    created: int = Field(description="创建时间戳")
    model: str = Field(description="模型名称")
    choices: List[Dict[str, Any]] = Field(description="选择列表")
    usage: Optional[Dict[str, int]] = Field(default=None, description="token使用统计")


class ReflexionTaskRequest(BaseModel):
    """Reflexion 任务请求"""
    task: str = Field(description="任务描述")
    max_steps: int = Field(default=10, description="最大步数")
    verbose: bool = Field(default=False, description="详细输出")
    use_reflection_library: bool = Field(default=True, description="使用反思库")


class ReflexionTaskResponse(BaseModel):
    """Reflexion 任务响应"""
    success: bool = Field(description="是否成功")
    task: str = Field(description="任务描述")
    total_steps: int = Field(description="总步骤数")
    successful_steps: int = Field(description="成功步骤数")
    failed_steps: int = Field(description="失败步骤数")
    final_answer: Optional[str] = Field(description="最终答案")
    history: List[Dict[str, Any]] = Field(description="执行历史")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(description="服务状态")
    version: str = Field(description="版本号")


# ========== 全局状态 ==========

class ServerState:
    """服务器状态"""
    def __init__(self):
        self.orchestrator: Optional[ReflexionOrchestrator] = None
        self.collaborative_agents: Optional[CollaborativeAgents] = None
        self.llm: Optional[ChatOpenAI] = None

    def initialize(self, api_key: Optional[str] = None):
        """初始化组件"""
        # 初始化 LLM
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            api_key=api_key,
        )

        # 准备工具
        tools = create_example_tools()

        # 初始化编排器
        self.orchestrator = ReflexionOrchestrator(
            llm=self.llm,
            tools=tools,
            max_steps=20,
            verbose=False,
        )

        # 初始化协作智能体
        self.collaborative_agents = CollaborativeAgents(
            llm=self.llm,
            tools=tools,
            verbose=False,
        )


state = ServerState()


# ========== 生命周期管理 ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    state.initialize(api_key)
    print("✓ Reflexion 服务已启动")
    yield
    # 关闭时
    print("✗ Reflexion 服务已关闭")


# ========== 创建应用 ==========

def create_app() -> FastAPI:
    """
    创建 FastAPI 应用

    Returns:
        FastAPI 应用实例
    """
    app = FastAPI(
        title="Reflexion API",
        description="LLM驱动的自我反思工具调用框架",
        version="0.1.0",
        lifespan=lifespan,
    )

    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    from reflexion.server.routes import router
    app.include_router(router)

    return app


# ========== 主入口 ==========

def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
):
    """
    运行服务器

    Args:
        host: 主机地址
        port: 端口
        reload: 是否自动重载
    """
    app = create_app()
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    run_server()
