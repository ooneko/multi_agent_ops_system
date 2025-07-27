# Cluster Management MCP Server

一个模拟的集群管理 MCP Server，提供物理机查询功能。

## 功能特性

- 查询集群中的物理机列表
- 按状态、数据中心、资源筛选服务器
- 获取特定服务器的详细信息
- 获取集群整体统计信息
- 检查服务器健康状态

## 可用工具

### 1. list_servers
查询集群中的物理机列表

**参数：**
- `status` (可选): 筛选特定状态的服务器 (online/offline/maintenance)
- `datacenter` (可选): 筛选特定数据中心的服务器
- `min_memory_gb` (可选): 筛选内存大于等于指定值的服务器
- `min_cpu_cores` (可选): 筛选CPU核心数大于等于指定值的服务器

### 2. get_server_details
获取指定物理机的详细信息

**参数：**
- `server_id` (必需): 服务器ID

### 3. get_cluster_summary
获取集群概况统计信息，无需参数

### 4. check_server_health
检查指定服务器的健康状态

**参数：**
- `server_id` (必需): 服务器ID

## 安装和配置

### 1. 安装依赖
```bash
pip install "mcp[cli]" fastmcp
```

### 2. 配置 Claude Desktop

在 Claude Desktop 配置文件中添加以下配置：

**macOS/Linux:**
`~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows:**
`%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "cluster-management": {
      "command": "python",
      "args": [
        "-m",
        "cluster_server"
      ],
      "cwd": "/Users/huabinhong/Code/multi_agent_ops_system/cz_mcp"
    }
  }
}
```

注意：请将 `cwd` 路径替换为您的实际项目路径。

### 3. 重启 Claude Desktop

配置完成后，重启 Claude Desktop 以加载 MCP server。

## 测试和验证

### 运行单元测试
```bash
cd cz_mcp
python test_cluster_server.py
```

### 运行交互式测试
```bash
cd cz_mcp
python demo_mcp_tools.py
```

选择 1 运行完整测试，选择 2 查看可用工具列表。

### 开发模式测试
```bash
cd cz_mcp
mcp dev cluster_server.py
```

## 示例数据

服务器包含5台模拟的物理机：
- 3台在线服务器 (北京数据中心)
- 1台维护中服务器 (上海数据中心)
- 1台离线服务器 (深圳数据中心)

每台服务器都有详细的配置信息，包括CPU、内存、磁盘、运行状态等。

## 在 Claude 中使用

配置完成后，在 Claude Desktop 中可以这样使用：

1. "查询当前集群有哪些物理机"
2. "显示所有在线的服务器"
3. "查找内存大于128GB的服务器"
4. "检查 server-001 的健康状态"
5. "显示集群的整体统计信息"