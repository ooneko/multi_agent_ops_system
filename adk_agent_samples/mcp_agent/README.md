# Command Executor MCP Agent

使用 Google ADK 和 Desktop Commander MCP 服务器构建的专业命令执行智能体。

## 功能特性

Command Executor Agent 专注于命令和脚本执行：

1. **执行本地命令**
   - 运行 shell 命令（ls、pwd、echo 等）
   - 执行脚本文件（.sh、.py、.js 等）
   - 支持命令组合和管道操作

2. **SSH 远程执行**
   - 通过 SSH 连接到远程服务器
   - 在远程服务器上执行命令
   - 管理 SSH 会话

3. **脚本运行**
   - 运行 Python 脚本
   - 执行 Shell 脚本
   - 运行 Node.js 脚本
   - 支持脚本参数传递

## 使用场景

- **日常命令执行**：运行各种系统命令和工具
- **脚本自动化**：执行部署脚本、构建脚本等
- **远程管理**：通过 SSH 在远程服务器上执行命令
- **开发任务**：运行测试、构建、部署等开发相关命令

## 快速开始

### 1. 设置环境

```bash
# 克隆或进入项目目录
cd /Users/huabinhong/Code/multi_agent_ops_system/adk_agent_samples/mcp_agent

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置你的 DeepSeek API 密钥
# DEEPSEEK_API_KEY=your_api_key_here
```

### 2. 运行 Agent

```bash
# 激活虚拟环境
source .venv/bin/activate

# 使用 ADK Web 界面运行（推荐）
adk web

# 或直接运行脚本
python agent.py
```

ADK Web 界面会在浏览器中打开，你可以在其中与 Agent 进行交互。

## 使用示例

Agent 启动后会自动演示以下功能：
- 查看当前工作目录
- 列出文件详细信息
- 执行简单命令
- 查看系统信息
- 创建和运行脚本

之后进入交互模式，你可以执行各种命令。

### 示例命令

```bash
# 基本命令执行
"运行 ls -la 命令"
"执行 pwd 查看当前目录"
"运行 echo 'Hello World'"
"执行 date 命令"

# 脚本执行
"运行 python script.py"
"执行 ./deploy.sh 脚本"
"运行 node app.js"
"执行 bash install.sh --verbose"

# SSH 远程执行
"SSH 连接到 user@192.168.1.100 执行 uptime"
"通过 SSH 在服务器上运行 df -h"
"SSH 执行远程备份脚本"

# 命令组合
"运行 ps aux | grep python"
"执行 find . -name '*.log' | xargs rm"
```

## 配置说明

### 环境变量

- `DEEPSEEK_API_KEY`: DeepSeek API 密钥（必需）
- `DESKTOP_COMMANDER_WORKSPACE`: 自定义工作目录（可选）

### MCP 服务器

Desktop Commander MCP 服务器会在首次运行时自动下载和配置。

## 安全提醒

- Agent 具有强大的系统控制能力，请谨慎使用
- 避免执行危险的系统命令
- 建议在隔离环境中测试

## 技术栈

- Google ADK: AI Agent 开发框架
- Desktop Commander MCP: 系统控制服务器
- LiteLLM: 统一 LLM 接口
- DeepSeek: 默认 LLM 模型

## 故障排除

1. **API 密钥错误**
   - 确保 .env 文件中设置了正确的 DEEPSEEK_API_KEY

2. **依赖安装失败**
   - 使用 `uv pip install -r requirements.txt` 手动安装

3. **MCP 服务器启动失败**
   - 确保已安装 Node.js 和 npx
   - 检查网络连接