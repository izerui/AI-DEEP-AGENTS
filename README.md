# Deep Agents 对比示例

本目录展示了如何使用 LangChain 的 Deep Agents 框架来简化 ReAct 智能体的实现，并与项目中的 `reflexion` 自定义实现进行对比。

## 📋 目录内容

### 1. `comparison.py` - 完整对比示例
展示三种实现方案的详细对比：
- **方案一**: Reflexion 自定义实现（当前项目）
- **方案二**: Deep Agents 实现
- **方案三**: 混合方案（Deep Agents + 反思库）

包含：
- 代码量对比
- 功能对比表格
- 推荐方案说明

### 2. `deepagents_simple.py` - Deep Agents 实际运行示例
提供 4 个可直接运行的示例：
- **示例1**: 基础使用 - 单任务执行
- **示例2**: 多步骤任务 - 自动规划和执行
- **示例3**: 错误恢复 - 智能处理失败
- **示例4**: 自定义 LLM 配置

## 🚀 快速开始

### 安装 Deep Agents

```bash
pip install deepagents
```

### 运行示例

```bash
# 运行对比分析
python deepagents_demo/comparison.py

# 运行实际示例（需要先安装 deepagents）
python deepagents_demo/deepagents_simple.py
```

## 📊 核心对比

### Reflexion 自定义实现

**优点：**
- ✅ 完全控制每个细节
- ✅ 自定义反思库（存储和复用历史经验）
- ✅ 细粒度成本优化
- ✅ 独特的防死循环机制

**缺点：**
- ❌ 代码量大（~1000+ 行）
- ❌ 维护成本高
- ❌ 需要手动实现所有功能
- ❌ 学习曲线陡峭

**代码示例：**
```python
from reflexion import ReflexionOrchestrator

orchestrator = ReflexionOrchestrator(
    llm=llm,
    tools=tools,
    max_steps=10,
    verbose=True,
)

summary = await orchestrator.run(task)
```

### Deep Agents 实现

**优点：**
- ✅ 代码量极少（~50 行）
- ✅ 官方维护，持续更新
- ✅ 内置自动规划
- ✅ 内置文件系统工具
- ✅ 内置子智能体生成
- ✅ 学习曲线平缓

**缺点：**
- ❌ 无内置反思库
- ❌ 细粒度控制较少
- ❌ 可能消耗更多 tokens

**代码示例：**
```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    tools=tools,
    system_prompt="你是一个智能助手..."
)

result = agent.invoke({"messages": [{"role": "user", "content": task}]})
```

### 混合方案（推荐）

结合两者优势：
- ✅ 使用 Deep Agents 的强大功能
- ✅ 保留反思库作为特色
- ✅ 代码量大幅减少
- ✅ 既有稳定性又有定制能力

**代码示例：**
```python
class ReflexionDeepAgent:
    def __init__(self, agent, reflection_library=None):
        self.agent = agent
        self.library = reflection_library or ReflectionLibrary()
    
    def invoke(self, input_data):
        result = self.agent.invoke(input_data)
        
        # 分析结果，添加反思
        if self._has_error(result):
            reflection = self._analyze_error(result)
            self.library.add_reflection(reflection)
        
        return result

# 使用
agent = create_deep_agent(tools=tools)
hybrid_agent = ReflexionDeepAgent(agent, library)
result = hybrid_agent.invoke({"messages": task})
```

## 📈 详细对比表

| 特性 | Reflexion 自定义 | Deep Agents | 混合方案 |
|------|------------------|-------------|----------|
| **代码量** | ~1000+ 行 | ~50 行 | ~100 行 |
| **自动规划** | ❌ 手动实现 | ✅ 内置 | ✅ 内置 |
| **文件系统** | ❌ 无 | ✅ 内置 | ✅ 内置 |
| **子智能体** | ✅ 自定义协作 | ✅ 内置 | ✅ 内置 |
| **反思库** | ✅ 独特特色 | ❌ 需要自定义 | ✅ 保留 |
| **防死循环** | ✅ 自定义 | ✅ 内置 | ✅ 内置 |
| **可观测性** | ✅ 详细日志 | ✅ 支持 | ✅ 支持 |
| **维护成本** | 高（自己维护） | 低（官方维护） | 中 |
| **学习曲线** | 陡峭 | 平缓 | 平缓 |
| **扩展性** | 灵活 | 灵活 | 灵活 |
| **成本优化** | ✅ 可精确控制 | ⚠️ 需自定义 | ✅ 可控制 |

## 🎯 推荐方案

### 场景 1: 快速开发 / 原型验证
**推荐**: Deep Agents
```python
from deepagents import create_deep_agent

agent = create_deep_agent(tools=tools)
result = agent.invoke({"messages": task})
```

**理由**: 几行代码即可运行，快速验证想法

---

### 场景 2: 生产环境 / 需要特色功能
**推荐**: 混合方案（Deep Agents + 反思库）
```python
# Deep Agents + 自定义反思库
agent = create_deep_agent(tools=tools)
hybrid_agent = ReflexionDeepAgent(agent, library)
result = hybrid_agent.invoke({"messages": task})
```

**理由**: 既有官方框架的稳定性，又有自定义特色

---

### 场景 3: 研究项目 / 需要完全控制
**推荐**: 保留 Reflexion 自定义实现
```python
from reflexion import ReflexionOrchestrator

orchestrator = ReflexionOrchestrator(llm=llm, tools=tools)
summary = await orchestrator.run(task)
```

**理由**: 可以精确控制每个细节，适合研究和优化

---

### 场景 4: 成本敏感场景
**推荐**: 混合方案 + 成本优化
```python
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent

# 不同环节用不同模型
planner_llm = ChatOpenAI(model="gpt-4")  # 强大规划
executor_llm = ChatOpenAI(model="gpt-4o-mini")  # 便宜执行

agent = create_deep_agent(
    tools=tools,
    llm=executor_llm  # 执行用便宜模型
)
```

**理由**: 用不同模型优化成本

## 📝 实施步骤

### 第一步: 安装 Deep Agents
```bash
pip install deepagents
```

### 第二步: 创建工具
使用 `@tool` 装饰器定义工具：
```python
from langchain_core.tools import tool

@tool
def my_tool(param: str) -> str:
    """工具描述"""
    return f"结果: {param}"
```

### 第三步: 创建智能体
```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    tools=[my_tool],
    system_prompt="你是一个智能助手..."
)
```

### 第四步: 运行任务
```python
result = agent.invoke({
    "messages": [{"role": "user", "content": "你的任务"}]
})
```

### 第五步: 添加反思库（可选）
```python
class ReflectionLibrary:
    def add_reflection(self, error, suggestion):
        # 添加反思记录
        pass

# 包装智能体
hybrid_agent = ReflexionDeepAgent(agent, library)
```

### 第六步: 对比测试
在相同任务下对比：
- 执行效果
- Token 消耗
- 响应时间
- 成本

### 第七步: 根据结果调整
- 如果 Deep Agents 满足需求 → 完全迁移
- 如果需要反思库 → 使用混合方案
- 如果需要完全控制 → 保留 Reflexion

## 🔗 相关资源

- [Deep Agents 官方文档](https://docs.langchain.com/oss/python/deepagents/quickstart)
- [LangChain 文档](https://python.langchain.com/)
- [Reflexion 论文](https://arxiv.org/abs/2303.11366)
- [项目 Reflexion 实现](../reflexion/README.md)

## 💡 常见问题

### Q: Deep Agents 完全替代 Reflexion 吗？
A: 不一定。取决于你的需求：
- 如果需要反思库特色功能 → 建议混合使用
- 如果需要完全控制 → 保留 Reflexion
- 如果只是基础功能 → Deep Agents 更好

### Q: 如何迁移现有代码？
A: 建议：
1. 先用 Deep Agents 实现新功能
2. 逐步迁移不依赖反思库的旧功能
3. 保留需要反思库的核心功能

### Q: 混合方案会增加复杂性吗？
A: 只会增加少量代码（约50行），但大大减少整体维护成本

### Q: Deep Agents 支持哪些 LLM？
A: 支持所有 LangChain 兼容的 LLM，包括：
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- 其他兼容模型

## 📞 反馈

如有问题或建议，欢迎：
- 提交 Issue
- 发起 Pull Request
- 参与讨论

## 📄 许可证

MIT License