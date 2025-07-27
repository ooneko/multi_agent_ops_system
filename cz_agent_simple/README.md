# 沧竹Agent（CZ-Agent）- 智能运维助手

## 项目简介

沧竹Agent是一个基于LangChain + LangGraph构建的智能运维助手，专注于数据中心服务器的监控、诊断和故障排查。当服务器安装失败时，能够综合分析多维度信息并提供具体的解决建议。

## 核心功能

- 🔍 **服务器信息查询**：查询服务器列表、状态和详细配置
- 🌐 **网络拓扑分析**：展示带内/带外网络连通性，支持机柜级别分析
- 🔧 **交换机信息管理**：查看交换机状态、端口信息和连接关系
- 📋 **安装日志分析**：获取和分析服务器安装过程日志
- 🎯 **智能故障诊断**：综合分析多维度数据，提供故障原因和修复建议

## 技术架构

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│                 │     │                  │     │                │
│   用户界面      │────▶│   CZ-Agent       │────▶│  Mock MCP      │
│                 │     │  (LangChain +    │     │   Server       │
│                 │     │   LangGraph)     │     │                │
└─────────────────┘     └──────────────────┘     └────────────────┘
```

- **LangChain**: 提供Agent框架和工具系统
- **LangGraph**: 实现复杂的状态管理和工作流编排
- **MCP协议**: 用于数据通信和工具集成
- **LiteLLM**: 支持多种LLM模型（DeepSeek、GPT等）

## 快速开始

### 1. 安装 uv（如果尚未安装）

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

### 2. 安装依赖

```bash
# 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装项目依赖
uv pip install -e .

# 安装开发依赖
uv pip install -e ".[dev]"
```

### 2. 配置环境变量

复制环境变量示例文件并配置您的 API 密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件，添加您的 API 密钥：

```bash
# DeepSeek API Configuration
DEEPSEEK_API_KEY=your_actual_api_key_here
```

支持的 LLM 提供商：
- **DeepSeek** (推荐): 设置 `DEEPSEEK_API_KEY`
- **OpenAI**: 设置 `OPENAI_API_KEY`
- **Google AI**: 设置 `GOOGLE_API_KEY`
- **Anthropic**: 设置 `ANTHROPIC_API_KEY`

### 3. 启动Mock MCP服务器

```bash
python -m cz_agent_simple.mock_mcp_server
```

### 3. 运行Agent

```python
from cz_agent_simple.agent import CZAgent

# 创建Agent实例
agent = CZAgent(model="deepseek/deepseek-chat")

# 处理查询
response = await agent.process_query("查看所有在线的服务器")
print(response)
```

### 4. 交互式使用

```bash
python -m cz_agent_simple.agent
```

## 使用示例

### 查询服务器信息
```python
# 查看所有服务器
"查看所有服务器列表"

# 查看特定状态的服务器
"显示所有离线的服务器"

# 查看服务器详情
"srv-001的详细信息是什么"
```

### 分析网络拓扑
```python
# 服务器网络拓扑
"显示srv-001的网络拓扑"

# 机柜级别分析
"分析rack-A01的网络连通性"
```

### 故障诊断
```python
# 分析安装失败
"分析srv-020安装失败的原因"

# 查看安装日志
"查看srv-020的安装日志"
```

## 项目结构

```
cz_agent_simple/
├── __init__.py          # 包初始化
├── agent.py             # 主Agent实现
├── state.py             # LangGraph状态定义
├── workflow.py          # 工作流实现
├── tools.py             # LangChain工具定义
├── mcp_client.py        # MCP客户端封装
├── models.py            # 数据模型
├── mock_mcp_server.py   # Mock MCP服务器
├── pyproject.toml       # 项目配置和依赖
└── README.md           # 项目文档
```

## 工作流程

1. **查询分析**：分析用户意图，提取关键实体
2. **数据获取**：根据意图调用相应的MCP工具
3. **故障分析**：如需要，进行综合故障诊断
4. **响应生成**：生成结构化的响应结果

## Mock数据说明

Mock MCP服务器提供了丰富的测试数据：

- **正常场景**：大部分服务器正常运行
- **故障场景**：
  - 硬件故障（磁盘缺失）
  - 网络配置错误（DHCP失败）
  - 软件包冲突
  - 机柜级网络故障（rack-A02）

## 开发指南

### 添加新工具

1. 在 `tools.py` 中定义新工具：
```python
@tool("tool_name", args_schema=ToolInput)
async def new_tool(param: str) -> Dict[str, Any]:
    """工具描述"""
    # 实现逻辑
    pass
```

2. 将工具添加到 `ALL_TOOLS` 列表

### 扩展工作流

1. 在 `state.py` 中添加新的状态字段
2. 在 `workflow.py` 中添加新的处理节点
3. 更新工作流的边和条件

### 自定义诊断规则

在 `workflow.py` 的 `analyze_fault` 函数中添加新的诊断逻辑。

## 测试

运行所有测试：
```bash
python -m pytest cz_agent_simple/
```

运行特定测试：
```bash
python -m pytest cz_agent_simple/test_agent.py
```

## 注意事项

1. Mock数据仅供开发和测试使用
2. 生产环境需要实现真实的MCP服务器
3. 建议配置适当的LLM模型和API密钥
4. 注意处理网络超时和错误情况

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License