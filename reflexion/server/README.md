# Reflexion API 服务器

将 Reflexion 框架暴露为兼容 OpenAI 协议的 REST API。

## 快速开始

### 1. 启动服务器

```bash
# 设置环境变量
export RAG_API_KEYS=your-secret-key
export OPENAI_API_KEY=your-openai-key

# 启动服务器
python main.py
```

服务器将在 `http://localhost:8000` 启动。

### 2. 访问 API 文档

打开浏览器访问:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API 端点

### 聊天完成 (兼容 OpenAI)

**端点**: `POST /reflexion/chat/completions`

完全兼容 OpenAI Chat Completions API 格式。

```bash
curl -X POST http://localhost:8000/reflexion/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "reflexion",
    "messages": [
      {"role": "user", "content": "计算 25 加 18"}
    ],
    "max_steps": 10
  }'
```

### 直接任务执行

**端点**: `POST /reflexion/task`

直接使用 Reflexion 框架执行任务，返回详细的执行信息。

```bash
curl -X POST http://localhost:8000/reflexion/task \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "搜索关于 python 的信息",
    "max_steps": 10
  }'
```

响应:
```json
{
  "success": true,
  "task": "搜索关于 python 的信息",
  "total_steps": 3,
  "successful_steps": 3,
  "failed_steps": 0,
  "final_answer": "搜索结果: ...",
  "history": [...]
}
```

### 列出模型

**端点**: `GET /reflexion/models`

```bash
curl http://localhost:8000/reflexion/models \
  -H "Authorization: Bearer your-api-key"
```

### 健康检查

**端点**: `GET /reflexion/health`

```bash
curl http://localhost:8000/reflexion/health \
  -H "Authorization: Bearer your-api-key"
```

## 使用 OpenAI SDK

最简单的方式是使用 OpenAI 的 Python SDK：

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/reflexion",
    api_key="your-api-key",
)

response = client.chat.completions.create(
    model="reflexion",
    messages=[
        {"role": "user", "content": "计算 25 加 18"}
    ],
    max_steps=10,
)

print(response.choices[0].message.content)
```

## 使用多智能体协作

启用多智能体协作模式（规划者-执行者-批判者）：

```python
response = client.chat.completions.create(
    model="reflexion-collaboration",
    messages=[
        {"role": "user", "content": "完成复杂的多步骤任务"}
    ],
    use_collaboration=True,
    max_steps=5,
)

print(response.choices[0].message.content)
```

## 请求参数

### ChatCompletions 请求

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| model | string | "reflexion" | 模型名称 |
| messages | array | 必需 | 消息列表 |
| temperature | float | 0.7 | 温度参数 |
| max_tokens | int | 1000 | 最大token数 |
| stream | bool | false | 是否流式输出 |
| max_steps | int | 10 | 最大执行步数 |
| use_collaboration | bool | false | 是否使用多智能体协作 |

### Task 请求

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| task | string | 必需 | 任务描述 |
| max_steps | int | 10 | 最大步数 |
| verbose | bool | false | 详细输出 |

## 认证

所有端点都需要 Bearer Token 认证：

```bash
export RAG_API_KEYS=your-secret-key
```

在请求中添加:
```
Authorization: Bearer your-secret-key
```

## 配置

环境变量:

| 变量 | 描述 | 默认值 |
|------|------|--------|
| RAG_API_KEYS | API 密钥（逗号分隔多个） | 无 |
| OPENAI_API_KEY | OpenAI API 密钥 | 从 .env 读取 |
| OPENAI_REFLEXION_MODEL | 使用的模型 | gpt-3.5-turbo |

## 示例

查看完整示例:

```bash
python reflexion/server/client_example.py
```

## 与 OpenAI API 的差异

1. **额外参数**: `max_steps`, `use_collaboration`
2. **响应格式**: 兼容 OpenAI 格式，额外包含执行步数信息
3. **工具调用**: 自动处理工具调用和反思循环

## 错误处理

API 返回标准 HTTP 状态码:

- 200: 成功
- 400: 请求错误
- 403: 认证失败
- 500: 服务器错误

错误响应格式:
```json
{
  "detail": "错误描述"
}
```

## 性能考虑

- Reflexion 循环可能需要多次 LLM 调用
- 建议设置合理的 `max_steps` 限制
- 使用 `use_collaboration=true` 可能增加成本但提高质量

## 扩展

自定义工具可以通过修改 `reflexion/examples/example_tools.py` 添加。

更多文档: [Reflexion README](../README.md)
