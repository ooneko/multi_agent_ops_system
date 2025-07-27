# AI Agent 开发技术栈

## 虚拟环境管理 (uv)
### 创建和激活虚拟环境
```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境 (macOS/Linux)
source .venv/bin/activate

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 退出虚拟环境
deactivate
```

### 管理依赖
```bash
# 安装单个包
uv pip install package-name

# 从 requirements.txt 安装
uv pip install -r requirements.txt

# 安装项目依赖（如果有 pyproject.toml）
uv pip install -e .

# 生成依赖列表
uv pip freeze > requirements.txt

# 同步依赖（确保环境与 requirements.txt 完全一致）
uv pip sync requirements.txt
```

### uv 的优势
- **极速安装**: 比 pip 快 10-100 倍
- **智能缓存**: 自动缓存下载的包，避免重复下载
- **内存安全**: 用 Rust 编写，避免了内存相关的问题
- **兼容性好**: 完全兼容 pip 命令，可以无缝切换

### 在项目中使用 uv
```bash
# 进入项目目录
cd /path/to/project

# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate

# 安装项目依赖
uv pip install -r requirements.txt

# 开始开发
python your_script.py
```

### 常用 uv 命令
```bash
# 查看已安装的包
uv pip list

# 查看包信息
uv pip show package-name

# 卸载包
uv pip uninstall package-name

# 升级包
uv pip install --upgrade package-name

# 清理缓存
uv cache clean
```

## Google ADK (Agent Development Kit)

### 概述
Google ADK 是 Google 在 2025 年推出的开源框架，专门用于简化 AI Agent 和多智能体系统的端到端开发。它是 Google 产品（如 Agentspace 和 Google Customer Engagement Suite）中使用的同一框架。

### 核心特性
- **多智能体架构**：原生支持多智能体系统，支持智能体间协作、任务委派和通信
- **模型无关性**：虽然针对 Gemini 优化，但通过 LiteLLM 支持多种 LLM（GPT-4、Claude、Mistral 等）
- **代码优先开发**：直接在 Python 中定义智能体逻辑、工具和编排
- **内置流式传输**：支持双向音频和视频流，实现多模态对话

### 快速开始
```python
from google.adk.agents import Agent, LlmAgent
from google.adk.tools import google_search

# 单个智能体
root_agent = Agent(
    name="search_assistant",
    model="gemini-2.0-flash",
    instruction="你是一个有用的助手。",
    tools=[google_search]
)

# 多智能体系统
billing_agent = LlmAgent(name="Billing", description="处理账单查询")
support_agent = LlmAgent(name="Support", description="技术支持")
coordinator = LlmAgent(
    name="Coordinator",
    sub_agents=[billing_agent, support_agent]
)
```

## Google A2A (Agent-to-Agent Protocol)

### 概述
Google A2A 是 2025 年 4 月发布的开放协议，被设计为"AI 智能体的 HTTP 协议"，实现不同框架、不同公司开发的 AI 智能体之间的标准化通信。

### 核心组件
- **Agent Card**：智能体能力声明（/.well-known/agent.json）
- **通信协议**：基于 JSON-RPC 2.0 over HTTPS
- **任务状态**：submitted → working → input-required → completed/failed

### 安全特性
- 企业级认证（OAuth、API Keys）
- 不透明执行（保护内部实现）
- 端到端加密
- 防止提示注入和任务重放攻击

### 示例
```python
from a2a import A2AServer, A2AClient, Task

# 服务端
class MyAgent(A2AServer):
    async def handle_task(self, task: Task):
        return {"result": "processed"}

# 客户端
client = A2AClient()
result = await client.send_task(agent_url, task)
```

## LiteLLM

### 概述
LiteLLM 是一个统一的接口，用于调用 100+ 个不同的 LLM API。它将所有 LLM API 调用映射到 OpenAI 的 ChatCompletion 格式。

### 主要功能
- **统一接口**：一套代码支持 100+ 个 LLM 提供商
- **负载均衡**：智能路由和故障转移
- **成本控制**：详细的成本跟踪和预算管理
- **代理服务器**：支持团队协作和虚拟密钥

### 使用示例
```python
from litellm import completion

# 相同的代码调用不同提供商
response = completion(
    model="openai/gpt-4o",  # 或 "anthropic/claude-3-sonnet"
    messages=[{"role": "user", "content": "Hello"}]
)

# 路由器实现负载均衡
from litellm import Router
router = Router(model_list=[...])
response = router.completion(model="gpt-3.5-turbo", messages=messages)
```

### 配置示例
```yaml
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: azure/gpt-35-deployment
      api_base: https://endpoint.openai.azure.com/
      rpm: 100

router_settings:
  routing_strategy: usage-based-routing-v2
  num_retries: 3
  fallbacks: [{"gpt-3.5-turbo": ["gpt-4"]}]
```

## LangChain

### 概述
LangChain 是用于开发基于 LLM 应用程序的开源框架，简化了 LLM 应用程序生命周期的每个阶段。

### 核心组件
- **Chains**：组件调用序列
- **Agents**：使用 LLM 推理的智能决策系统
- **Tools**：与外部世界交互的函数
- **Memory**：保持对话上下文
- **Prompts**：结构化输入模板

### 基础示例
```python
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

# 创建链
prompt = ChatPromptTemplate.from_messages([
    ("system", "Translate to {language}"),
    ("user", "{text}")
])
chain = prompt | ChatAnthropic(model="claude-3-sonnet")

# 执行
result = chain.invoke({
    "language": "Spanish",
    "text": "Hello"
})
```

## LangGraph

### 概述
LangGraph 是 LangChain 的图执行引擎，专门用于构建有状态的多智能体工作流。支持循环图结构，适合复杂的控制流。

### 核心概念
- **Graph**：有向图模型
- **State**：共享状态管理
- **Node**：计算单元
- **Edge**：控制流（直接边、条件边、入口边）

### 多智能体系统示例
```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    next_agent: str

def research_agent(state):
    return {"messages": ["研究完成"], "next_agent": "analysis"}

def analysis_agent(state):
    return {"messages": ["分析完成"], "next_agent": "summary"}

# 构建工作流
workflow = StateGraph(AgentState)
workflow.add_node("research", research_agent)
workflow.add_node("analysis", analysis_agent)

# 添加边
workflow.add_edge(START, "research")
workflow.add_edge("research", "analysis")
workflow.add_edge("analysis", END)

# 编译并运行
app = workflow.compile()
```

### 高级特性
- **条件分支**：基于状态的动态路由
- **并行执行**：Fan-out/Fan-in 模式
- **循环控制**：支持重试和迭代
- **状态持久化**：检查点和恢复

## 技术选型建议

### 场景选择
1. **Google 生态系统 + 多智能体**：Google ADK + A2A
2. **多 LLM 提供商管理**：LiteLLM
3. **简单 LLM 应用**：LangChain
4. **复杂工作流 + 状态管理**：LangGraph
5. **企业级部署**：LiteLLM Proxy + LangGraph + LangSmith

### 集成方案
```python
# LiteLLM + LangChain + LangGraph 集成示例
from langchain_litellm import ChatLiteLLMRouter
from langgraph.graph import StateGraph
from litellm import Router

# 使用 LiteLLM 管理多个 LLM
litellm_router = Router(model_list=[...])
llm = ChatLiteLLMRouter(router=litellm_router)

# 在 LangGraph 中使用
workflow = StateGraph(State)
workflow.add_node("agent", lambda s: llm.invoke(s["messages"]))
```

## 技术栈协同使用方案

### 1. 统一架构设计

#### 分层架构
```
┌─────────────────────────────────────────────┐
│          应用层 (Application Layer)         │
│         业务逻辑、用户界面、API             │
├─────────────────────────────────────────────┤
│       编排层 (Orchestration Layer)          │
│    LangGraph (工作流) + Google ADK (多智能体) │
├─────────────────────────────────────────────┤
│         智能体层 (Agent Layer)              │
│   LangChain Agents + Google ADK Agents      │
├─────────────────────────────────────────────┤
│        通信层 (Communication Layer)         │
│         Google A2A Protocol                 │
├─────────────────────────────────────────────┤
│          模型层 (Model Layer)               │
│      LiteLLM (统一 LLM 接口和路由)          │
└─────────────────────────────────────────────┘
```

### 2. 核心集成模式

#### 模式 A：LiteLLM + LangChain + LangGraph
适用于需要复杂工作流和多模型管理的场景。

```python
from litellm import Router
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolExecutor
from typing import TypedDict, Annotated, List
import operator

# 1. 配置 LiteLLM Router
model_config = [
    {
        "model_name": "gpt-4",
        "litellm_params": {
            "model": "openai/gpt-4",
            "api_key": "your-key",
            "temperature": 0.7
        }
    },
    {
        "model_name": "claude-3",
        "litellm_params": {
            "model": "anthropic/claude-3-sonnet",
            "api_key": "your-key"
        }
    }
]

router = Router(model_list=model_config)

# 2. 创建 LangChain 兼容的 LLM
class LiteLLMChat(BaseChatModel):
    def _generate(self, messages, **kwargs):
        response = router.completion(
            model="gpt-4",
            messages=[{"role": m.type, "content": m.content} for m in messages]
        )
        return response

llm = LiteLLMChat()

# 3. 定义 LangGraph 状态
class WorkflowState(TypedDict):
    messages: Annotated[List[str], operator.add]
    current_task: str
    results: dict

# 4. 创建智能体节点
def research_node(state: WorkflowState):
    messages = [
        SystemMessage(content="You are a research assistant."),
        HumanMessage(content=state["current_task"])
    ]
    response = llm.invoke(messages)
    return {
        "messages": [f"Research: {response.content}"],
        "results": {"research": response.content}
    }

def analysis_node(state: WorkflowState):
    context = state["results"].get("research", "")
    messages = [
        SystemMessage(content="You are a data analyst."),
        HumanMessage(content=f"Analyze this: {context}")
    ]
    response = llm.invoke(messages)
    return {
        "messages": [f"Analysis: {response.content}"],
        "results": {"analysis": response.content}
    }

# 5. 构建工作流
workflow = StateGraph(WorkflowState)
workflow.add_node("research", research_node)
workflow.add_node("analysis", analysis_node)
workflow.add_edge(START, "research")
workflow.add_edge("research", "analysis")
workflow.add_edge("analysis", END)

app = workflow.compile()
```

#### 模式 B：Google ADK + A2A + LiteLLM
适用于需要多智能体协作和跨系统通信的场景。

```python
from google.adk.agents import Agent, LlmAgent
from google.adk.runners import LocalRunner
from a2a import A2AServer, A2AClient
from litellm import completion
import asyncio

# 1. 创建支持 A2A 的 Google ADK Agent
class ResearchAgent(Agent, A2AServer):
    def __init__(self):
        super().__init__(
            name="research_agent",
            model="gemini-2.0-flash",
            instruction="You are a research specialist."
        )
        # A2A 服务器配置
        self.a2a_config = {
            "name": "Research Agent",
            "capabilities": ["research", "web_search"],
            "endpoint": "http://localhost:8001/a2a"
        }
    
    async def handle_task(self, task):
        # 使用 LiteLLM 进行模型调用
        response = completion(
            model=self.model,
            messages=[{"role": "user", "content": task.data["query"]}]
        )
        return {"result": response.choices[0].message.content}

# 2. 创建分析智能体
class AnalysisAgent(Agent, A2AServer):
    def __init__(self):
        super().__init__(
            name="analysis_agent",
            model="openai/gpt-4",  # 通过 LiteLLM 使用不同模型
            instruction="You are a data analyst."
        )
        self.research_client = A2AClient()
    
    async def analyze_with_research(self, query):
        # 通过 A2A 调用研究智能体
        research_task = {
            "type": "research",
            "data": {"query": query}
        }
        research_result = await self.research_client.send_task(
            "http://localhost:8001",
            research_task
        )
        
        # 基于研究结果进行分析
        analysis_response = completion(
            model=self.model,
            messages=[
                {"role": "system", "content": self.instruction},
                {"role": "user", "content": f"Analyze: {research_result['result']}"}
            ]
        )
        return analysis_response.choices[0].message.content

# 3. 创建协调者智能体
coordinator = LlmAgent(
    name="Coordinator",
    model="gemini-2.0-flash",
    instruction="Coordinate between research and analysis agents.",
    sub_agents=[ResearchAgent(), AnalysisAgent()]
)
```

#### 模式 C：完整集成 - 企业级多智能体系统

```python
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio

# 1. 定义统一的消息格式
@dataclass
class AgentMessage:
    sender: str
    receiver: str
    content: Any
    metadata: Dict[str, Any]

# 2. 创建智能体基类
class UnifiedAgent:
    def __init__(self, name: str, model_config: Dict[str, Any]):
        self.name = name
        self.model_config = model_config
        self.litellm_router = Router(model_list=[model_config])
        self.a2a_server = A2AServer(name=name)
        self.workflow = None
        
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        # 使用 LiteLLM 处理消息
        response = await self.litellm_router.acompletion(
            model=self.model_config["model_name"],
            messages=[{"role": "user", "content": message.content}]
        )
        
        return AgentMessage(
            sender=self.name,
            receiver=message.sender,
            content=response.choices[0].message.content,
            metadata={"model_used": self.model_config["model_name"]}
        )
    
    def create_workflow(self) -> StateGraph:
        # 使用 LangGraph 创建内部工作流
        workflow = StateGraph(WorkflowState)
        return workflow

# 3. 创建智能体管理器
class MultiAgentSystem:
    def __init__(self):
        self.agents: Dict[str, UnifiedAgent] = {}
        self.communication_protocol = "a2a"
        self.orchestrator = None
        
    def register_agent(self, agent: UnifiedAgent):
        self.agents[agent.name] = agent
        
    def create_orchestrator(self):
        # 使用 LangGraph 创建主编排器
        orchestrator = StateGraph(SystemState)
        
        # 添加每个智能体作为节点
        for agent_name, agent in self.agents.items():
            orchestrator.add_node(
                agent_name,
                lambda state, a=agent: self.agent_node(state, a)
            )
        
        # 添加路由逻辑
        orchestrator.add_conditional_edges(
            "router",
            self.route_to_agent,
            {name: name for name in self.agents.keys()}
        )
        
        self.orchestrator = orchestrator.compile()
        
    async def agent_node(self, state: SystemState, agent: UnifiedAgent):
        message = AgentMessage(
            sender="orchestrator",
            receiver=agent.name,
            content=state["current_task"],
            metadata=state.get("metadata", {})
        )
        
        response = await agent.process_message(message)
        
        return {
            "agent_responses": {agent.name: response.content},
            "last_agent": agent.name
        }
    
    def route_to_agent(self, state: SystemState) -> str:
        # 基于任务类型路由到合适的智能体
        task_type = state.get("task_type", "general")
        agent_mapping = {
            "research": "research_agent",
            "analysis": "analysis_agent",
            "summary": "summary_agent"
        }
        return agent_mapping.get(task_type, "research_agent")

# 4. 实际使用示例
async def main():
    # 初始化系统
    system = MultiAgentSystem()
    
    # 配置并注册智能体
    research_agent = UnifiedAgent(
        name="research_agent",
        model_config={
            "model_name": "gpt-4",
            "litellm_params": {
                "model": "openai/gpt-4",
                "api_key": "your-key"
            }
        }
    )
    
    analysis_agent = UnifiedAgent(
        name="analysis_agent",
        model_config={
            "model_name": "claude-3",
            "litellm_params": {
                "model": "anthropic/claude-3-sonnet",
                "api_key": "your-key"
            }
        }
    )
    
    system.register_agent(research_agent)
    system.register_agent(analysis_agent)
    
    # 创建编排器
    system.create_orchestrator()
    
    # 执行任务
    initial_state = {
        "current_task": "Research and analyze market trends for AI agents",
        "task_type": "research",
        "agent_responses": {},
        "metadata": {"priority": "high"}
    }
    
    result = await system.orchestrator.ainvoke(initial_state)
    print(result)

# 运行系统
asyncio.run(main())
```

### 3. 最佳实践建议

#### 3.1 模型管理策略
```yaml
# litellm_config.yaml
models:
  fast:
    - model_name: "fast-model"
      litellm_params:
        model: "openai/gpt-3.5-turbo"
        temperature: 0.7
        max_tokens: 1000
  
  powerful:
    - model_name: "powerful-model"
      litellm_params:
        model: "anthropic/claude-3-opus"
        temperature: 0.3
        max_tokens: 4000
  
  specialized:
    - model_name: "code-model"
      litellm_params:
        model: "openai/gpt-4-turbo"
        temperature: 0.1
        
routing_strategy:
  default: "fast-model"
  complex_tasks: "powerful-model"
  code_generation: "code-model"
```

#### 3.2 智能体通信模式
```python
# 1. 点对点通信（使用 A2A）
async def point_to_point_communication():
    client = A2AClient()
    task = {"type": "analyze", "data": {"content": "..."}}
    result = await client.send_task("http://agent.url", task)

# 2. 发布-订阅模式（使用 LangGraph + A2A）
class EventBus:
    def __init__(self):
        self.subscribers = {}
    
    def subscribe(self, event_type: str, agent: UnifiedAgent):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(agent)
    
    async def publish(self, event_type: str, data: Any):
        if event_type in self.subscribers:
            tasks = []
            for agent in self.subscribers[event_type]:
                task = agent.process_message(AgentMessage(
                    sender="event_bus",
                    receiver=agent.name,
                    content=data,
                    metadata={"event_type": event_type}
                ))
                tasks.append(task)
            await asyncio.gather(*tasks)

# 3. 工作流模式（使用 LangGraph）
def create_pipeline_workflow():
    workflow = StateGraph(PipelineState)
    
    # 串行处理
    workflow.add_edge("extract", "transform")
    workflow.add_edge("transform", "load")
    
    # 并行处理
    workflow.add_edge("start", ["process_a", "process_b", "process_c"])
    workflow.add_edge(["process_a", "process_b", "process_c"], "merge")
    
    return workflow.compile()
```

#### 3.3 错误处理和监控
```python
from functools import wraps
import logging
from datetime import datetime

# 1. 统一错误处理
class AgentError(Exception):
    def __init__(self, agent_name: str, error_type: str, message: str):
        self.agent_name = agent_name
        self.error_type = error_type
        self.message = message
        self.timestamp = datetime.now()

def handle_agent_errors(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Exception as e:
            error = AgentError(
                agent_name=self.name,
                error_type=type(e).__name__,
                message=str(e)
            )
            logging.error(f"Agent {self.name} error: {error}")
            # 使用 LiteLLM 的回退机制
            if hasattr(self, 'litellm_router'):
                return await self.litellm_router.acompletion(
                    model=self.model_config.get("fallback_model"),
                    messages=[{"role": "system", "content": "Handle error gracefully"}]
                )
            raise error
    return wrapper

# 2. 性能监控
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
    
    async def track_agent_performance(self, agent_name: str, operation: str):
        start_time = datetime.now()
        yield
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if agent_name not in self.metrics:
            self.metrics[agent_name] = {}
        
        if operation not in self.metrics[agent_name]:
            self.metrics[agent_name][operation] = []
        
        self.metrics[agent_name][operation].append({
            "duration": duration,
            "timestamp": start_time
        })

# 3. 使用 LangSmith 进行追踪
from langsmith import Client
from langsmith.run_trees import RunTree

client = Client()

async def trace_agent_execution(agent_name: str, task: str):
    run_tree = RunTree(
        name=f"{agent_name}_execution",
        run_type="agent",
        inputs={"task": task}
    )
    
    # 执行并追踪
    result = await execute_agent_task(agent_name, task)
    
    run_tree.end(outputs={"result": result})
    run_tree.post()
```

### 4. 部署架构

#### 4.1 微服务架构
```yaml
# docker-compose.yml
version: '3.8'

services:
  # LiteLLM 代理服务
  litellm-proxy:
    image: ghcr.io/berriai/litellm:main
    ports:
      - "4000:4000"
    environment:
      - LITELLM_MASTER_KEY=${LITELLM_KEY}
    volumes:
      - ./litellm_config.yaml:/app/config.yaml
    command: --config /app/config.yaml
  
  # 研究智能体
  research-agent:
    build: ./agents/research
    ports:
      - "8001:8001"
    environment:
      - LITELLM_PROXY_URL=http://litellm-proxy:4000
      - A2A_PORT=8001
    depends_on:
      - litellm-proxy
  
  # 分析智能体
  analysis-agent:
    build: ./agents/analysis
    ports:
      - "8002:8002"
    environment:
      - LITELLM_PROXY_URL=http://litellm-proxy:4000
      - A2A_PORT=8002
    depends_on:
      - litellm-proxy
  
  # LangGraph 编排服务
  orchestrator:
    build: ./orchestrator
    ports:
      - "8000:8000"
    environment:
      - AGENTS_CONFIG=/app/agents.yaml
    depends_on:
      - research-agent
      - analysis-agent
  
  # 监控服务
  monitoring:
    image: langchain/langsmith
    ports:
      - "9000:9000"
    environment:
      - LANGSMITH_API_KEY=${LANGSMITH_KEY}
```

#### 4.2 Kubernetes 部署
```yaml
# agent-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multi-agent-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent-system
  template:
    metadata:
      labels:
        app: agent-system
    spec:
      containers:
      - name: agent
        image: agent-system:latest
        env:
        - name: LITELLM_PROXY_URL
          value: "http://litellm-service:4000"
        - name: A2A_ENABLED
          value: "true"
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: agent-service
spec:
  selector:
    app: agent-system
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 5. 性能优化建议

1. **模型选择优化**
   - 使用 LiteLLM 的路由策略，为不同任务选择合适的模型
   - 简单任务用快速模型，复杂任务用强大模型

2. **并发处理**
   - 利用 LangGraph 的并行节点处理独立任务
   - 使用 asyncio 进行异步操作

3. **缓存策略**
   - 实现 LLM 响应缓存
   - 使用 Redis 存储中间结果

4. **资源管理**
   - 设置合理的超时时间
   - 实现熔断机制防止级联故障

这个协同使用方案展示了如何将这些技术栈有机结合，构建一个强大、灵活且可扩展的多智能体系统。

## Google ADK 评估框架 (Evaluate)

### 概述
Google ADK 提供了专门的评估框架，用于测试和评估 AI Agent 的性能。与传统软件测试不同，AI Agent 评估需要考虑其概率性特征，不能简单使用"通过/失败"的断言。

### 核心概念
1. **评估内容**
   - 最终输出质量
   - Agent 执行路径 (trajectory)
   - 工具使用策略
   - 推理过程的合理性

2. **测试用例格式**
   - **单一测试文件** (test.json): 适合简单交互
   - **评估集文件** (evalset.json): 适合复杂多轮对话

3. **主要评估指标**
   - `tool_trajectory_avg_score`: 评估工具使用准确性
   - `response_match_score`: 使用 ROUGE 度量响应相似度

### 在运维 Agent 系统中的应用

#### 1. 评估策略
- **工具使用准确性**: Agent 是否选择了正确的工具和参数
- **任务完成质量**: 运维操作的结果是否符合预期
- **执行路径合理性**: Agent 的决策过程是否高效合理
- **错误处理能力**: 面对异常情况的处理是否恰当

#### 2. 评估数据集示例
```json
{
  "test_name": "health_check_evaluation",
  "cases": [
    {
      "name": "正常服务器健康检查",
      "input": "检查生产环境服务器健康状态",
      "expected_tool_trajectory": [
        {
          "tool_name": "get_server_list",
          "parameters": {"filter": {"tags": ["production"]}}
        },
        {
          "tool_name": "execute_health_check",
          "parameters": {"server_ids": ["server-001", "server-002"]}
        }
      ],
      "expected_response": {
        "contains": ["健康度", "CPU使用率", "内存使用率", "服务状态"]
      }
    }
  ]
}
```

#### 3. 评估实现示例
```python
import pytest
from google.adk.evaluation import AgentEvaluator

@pytest.mark.asyncio
async def test_health_check_scenarios():
    """评估健康检查场景"""
    await AgentEvaluator.evaluate(
        agent_module="cz_agent_with_op_agent",
        eval_dataset_file_path_or_dir="tests/evaluation/datasets/health_check.evalset.json",
        config={
            "tool_trajectory_match_threshold": 0.9,
            "response_match_threshold": 0.85
        }
    )
```

#### 4. 评估指标体系
1. **功能性指标**
   - 工具调用准确率: ≥ 0.9
   - 任务完成率: ≥ 0.95
   - 响应相关性: ≥ 0.85

2. **性能指标**
   - 平均响应时间: < 30s
   - 并发处理能力: ≥ 10 servers

3. **可靠性指标**
   - 错误处理覆盖率: 100%
   - 故障恢复成功率: ≥ 0.9

#### 5. 持续改进流程
1. 建立初始性能基准
2. 定期运行完整评估套件
3. 识别低分区域和改进点
4. 基于评估结果优化 Agent 行为
5. 确保新改动不影响现有功能

### 最佳实践
- 为每个主要功能场景创建评估数据集
- 设置合理的阈值，允许 AI 的创造性响应
- 定期更新评估数据集以覆盖新场景
- 将评估集成到 CI/CD 流程中