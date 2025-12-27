#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reflexion API 路由 - 兼容 OpenAI Chat Completions 协议
"""

import asyncio
import json
import logging
import os
import time
import uuid
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from sse_starlette.sse import EventSourceResponse

from reflexion import ReflexionOrchestrator, CollaborativeAgents
from reflexion.examples.example_tools import create_example_tools

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 APIRouter 实例
router = APIRouter(
    prefix="/reflexion",
    tags=["reflexion"],
)

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
    max_steps: Optional[int] = Field(default=10, description="最大执行步数")
    use_collaboration: Optional[bool] = Field(default=False, description="是否使用多智能体协作")


class ChatCompletionChoice(BaseModel):
    """聊天完成选择"""
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    """OpenAI 兼容的聊天完成响应"""
    id: str = Field(description="响应ID")
    object: str = Field(default="chat.completion", description="对象类型")
    created: int = Field(description="创建时间戳")
    model: str = Field(description="模型名称")
    choices: List[ChatCompletionChoice] = Field(description="选择列表")
    usage: Optional[Dict[str, int]] = Field(default=None, description="token使用统计")


class ReflexionTaskRequest(BaseModel):
    """Reflexion 任务请求"""
    task: str = Field(description="任务描述")
    max_steps: int = Field(default=10, description="最大步数")
    verbose: bool = Field(default=False, description="详细输出")


class ReflexionTaskResponse(BaseModel):
    """Reflexion 任务响应"""
    success: bool = Field(description="是否成功")
    task: str = Field(description="任务描述")
    total_steps: int = Field(description="总步骤数")
    successful_steps: int = Field(description="成功步骤数")
    failed_steps: int = Field(description="失败步骤数")
    final_answer: Optional[str] = Field(description="最终答案")
    history: List[Dict[str, Any]] = Field(description="执行历史")


class ModelInfo(BaseModel):
    """模型信息"""
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "reflexion"


class ModelListResponse(BaseModel):
    """模型列表响应"""
    object: str = "list"
    data: List[ModelInfo]


# ========== 全局状态 ==========

class ReflexionState:
    """Reflexion 服务状态"""
    def __init__(self):
        self.orchestrator: Optional[ReflexionOrchestrator] = None
        self.collaborative_agents: Optional[CollaborativeAgents] = None
        self.llm: Optional[ChatOpenAI] = None
        self._initialized = False

    def initialize(self):
        """初始化 Reflexion 组件"""
        if self._initialized:
            return

        try:
            # 初始化 LLM
            self.llm = ChatOpenAI(
                model=os.getenv("OPENAI_REFLEXION_MODEL", "gpt-3.5-turbo"),
                temperature=0,
                api_key=os.getenv("OPENAI_API_KEY"),
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

            self._initialized = True
            logger.info("✓ Reflexion 服务初始化成功")

        except Exception as e:
            logger.error(f"✗ Reflexion 服务初始化失败: {e}")
            raise


# 全局状态实例
state = ReflexionState()


# ========== 辅助函数 ==========

def ensure_initialized():
    """确保服务已初始化"""
    if not state._initialized:
        state.initialize()


def extract_task_from_messages(messages: List[ChatMessage]) -> str:
    """从消息列表中提取任务"""
    # 获取最后一条用户消息
    user_messages = [msg for msg in messages if msg.role == "user"]
    if user_messages:
        return user_messages[-1].content

    # 如果没有用户消息，使用最后一条消息
    if messages:
        return messages[-1].content

    return ""


# ========== 端点定义 ==========

@router.get("/models")
async def list_models():
    """
    列出可用模型 (兼容 OpenAI /v1/models)
    """
    ensure_initialized()

    models = [
        ModelInfo(id="reflexion"),
        ModelInfo(id="reflexion-collaboration"),
    ]

    return ModelListResponse(data=models)


@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    聊天完成端点 (兼容 OpenAI /v1/chat/completions)

    支持:
    - 标准聊天完成
    - Reflexion 自我反思循环
    - 多智能体协作
    """
    ensure_initialized()

    # 提取任务
    task = extract_task_from_messages(request.messages)

    if not task:
        raise HTTPException(status_code=400, detail="未找到有效的任务描述")

    logger.info(f"收到任务: {task[:100]}...")

    # 选择执行模式
    if request.use_collaboration:
        summary = await state.collaborative_agents.run(
            task=task,
            max_iterations=request.max_steps,
        )
        result_text = summary.final_result or "任务执行完成"
        steps_taken = summary.iterations
    else:
        summary = await state.orchestrator.run(
            task=task,
        )
        result_text = summary.final_answer or "任务执行完成"
        steps_taken = summary.total_steps

    # 构建响应
    response_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    created = int(time.time())

    choice = ChatCompletionChoice(
        index=0,
        message=ChatMessage(
            role="assistant",
            content=f"{result_text}\n\n(执行步数: {steps_taken}, 成功: {summary.success})"
        ),
        finish_reason="stop",
    )

    response = ChatCompletionResponse(
        id=response_id,
        created=created,
        model=request.model,
        choices=[choice],
        usage={
            "prompt_tokens": len(task),
            "completion_tokens": len(result_text),
            "total_tokens": len(task) + len(result_text),
        },
    )

    return response


@router.post("/task", response_model=ReflexionTaskResponse)
async def execute_task(request: ReflexionTaskRequest):
    """
    执行 Reflexion 任务

    直接使用 Reflexion 框架执行任务，返回完整的执行信息
    """
    ensure_initialized()

    logger.info(f"执行任务: {request.task[:100]}...")

    try:
        # 执行任务
        summary = await state.orchestrator.run(
            task=request.task,
        )

        # 转换历史
        history = [
            {
                "step": h.step_number,
                "action": h.action,
                "tool": h.tool_name,
                "observation": h.observation[:200],  # 限制长度
                "reflection": h.reflection[:200] if h.reflection else None,
            }
            for h in summary.history
        ]

        return ReflexionTaskResponse(
            success=summary.success,
            task=summary.task,
            total_steps=summary.total_steps,
            successful_steps=summary.successful_steps,
            failed_steps=summary.failed_steps,
            final_answer=summary.final_answer,
            history=history,
        )

    except Exception as e:
        logger.error(f"任务执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    ensure_initialized()

    return {
        "status": "healthy",
        "service": "reflexion",
        "initialized": state._initialized,
        "version": "0.1.0",
    }


@router.get("/stats")
async def get_stats():
    """
    获取服务统计信息
    """
    ensure_initialized()

    return {
        "orchestrator": state.orchestrator.get_stats(),
        "tools_count": len(state.orchestrator.tools),
    }
