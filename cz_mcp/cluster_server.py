#!/usr/bin/env python
"""
MCP Server for Cluster Management
提供集群物理机查询功能
"""

from typing import List, Dict, Any
from datetime import datetime
from mcp.server.fastmcp import FastMCP
import json

# 创建 MCP server 实例
mcp = FastMCP("cluster-management")

# 模拟的物理机数据
MOCK_SERVERS = [
    {
        "id": "server-001",
        "hostname": "prod-server-001",
        "ip": "192.168.1.101",
        "cpu": "Intel Xeon E5-2680 v4 @ 2.40GHz",
        "cpu_cores": 28,
        "memory_gb": 128,
        "disk_tb": 4,
        "status": "online",
        "datacenter": "DC-Beijing",
        "rack": "A-12",
        "os": "Ubuntu 22.04 LTS",
        "uptime_days": 45,
        "load_average": [0.5, 0.6, 0.4],
        "last_update": "2025-01-24T10:30:00Z"
    },
    {
        "id": "server-002",
        "hostname": "prod-server-002",
        "ip": "192.168.1.102",
        "cpu": "Intel Xeon E5-2680 v4 @ 2.40GHz",
        "cpu_cores": 28,
        "memory_gb": 64,
        "disk_tb": 8,
        "status": "online",
        "datacenter": "DC-Beijing",
        "rack": "A-12",
        "os": "Ubuntu 22.04 LTS",
        "uptime_days": 120,
        "load_average": [1.2, 1.5, 1.3],
        "last_update": "2025-01-24T10:30:00Z"
    },
    {
        "id": "server-003",
        "hostname": "prod-server-003",
        "ip": "192.168.1.103",
        "cpu": "AMD EPYC 7742 64-Core Processor",
        "cpu_cores": 64,
        "memory_gb": 512,
        "disk_tb": 16,
        "status": "online",
        "datacenter": "DC-Beijing",
        "rack": "B-08",
        "os": "Rocky Linux 8.5",
        "uptime_days": 30,
        "load_average": [2.1, 2.3, 2.0],
        "last_update": "2025-01-24T10:30:00Z"
    },
    {
        "id": "server-004",
        "hostname": "dev-server-001",
        "ip": "192.168.2.101",
        "cpu": "Intel Xeon E5-2650 v3 @ 2.30GHz",
        "cpu_cores": 20,
        "memory_gb": 64,
        "disk_tb": 2,
        "status": "maintenance",
        "datacenter": "DC-Shanghai",
        "rack": "C-05",
        "os": "CentOS 7.9",
        "uptime_days": 0,
        "load_average": [0, 0, 0],
        "last_update": "2025-01-24T10:30:00Z"
    },
    {
        "id": "server-005",
        "hostname": "test-server-001",
        "ip": "192.168.3.101",
        "cpu": "Intel Core i9-9900K @ 3.60GHz",
        "cpu_cores": 8,
        "memory_gb": 32,
        "disk_tb": 1,
        "status": "offline",
        "datacenter": "DC-Shenzhen",
        "rack": "D-02",
        "os": "Debian 11",
        "uptime_days": 0,
        "load_average": [0, 0, 0],
        "last_update": "2025-01-24T08:00:00Z"
    }
]

@mcp.tool()
async def list_servers(
    status: str = None,
    datacenter: str = None,
    min_memory_gb: int = None,
    min_cpu_cores: int = None
) -> List[Dict[str, Any]]:
    """
    查询集群中的物理机列表
    
    参数:
    - status: 筛选特定状态的服务器 (online/offline/maintenance)
    - datacenter: 筛选特定数据中心的服务器
    - min_memory_gb: 筛选内存大于等于指定值的服务器
    - min_cpu_cores: 筛选CPU核心数大于等于指定值的服务器
    
    返回物理机的详细信息列表
    """
    servers = MOCK_SERVERS.copy()
    
    # 应用筛选条件
    if status:
        servers = [s for s in servers if s["status"] == status]
    
    if datacenter:
        servers = [s for s in servers if s["datacenter"] == datacenter]
    
    if min_memory_gb is not None:
        servers = [s for s in servers if s["memory_gb"] >= min_memory_gb]
    
    if min_cpu_cores is not None:
        servers = [s for s in servers if s["cpu_cores"] >= min_cpu_cores]
    
    return servers

@mcp.tool()
async def get_server_details(server_id: str) -> Dict[str, Any]:
    """
    获取指定物理机的详细信息
    
    参数:
    - server_id: 服务器ID
    
    返回服务器的完整信息，如果找不到则返回错误信息
    """
    for server in MOCK_SERVERS:
        if server["id"] == server_id:
            return server
    
    return {
        "error": f"Server with ID '{server_id}' not found",
        "available_ids": [s["id"] for s in MOCK_SERVERS]
    }

@mcp.tool()
async def get_cluster_summary() -> Dict[str, Any]:
    """
    获取集群概况统计信息
    
    返回集群的整体统计数据，包括总服务器数、状态分布、资源统计等
    """
    total_servers = len(MOCK_SERVERS)
    
    # 状态统计
    status_count = {}
    for server in MOCK_SERVERS:
        status = server["status"]
        status_count[status] = status_count.get(status, 0) + 1
    
    # 数据中心分布
    datacenter_count = {}
    for server in MOCK_SERVERS:
        dc = server["datacenter"]
        datacenter_count[dc] = datacenter_count.get(dc, 0) + 1
    
    # 资源统计
    total_cpu_cores = sum(s["cpu_cores"] for s in MOCK_SERVERS)
    total_memory_gb = sum(s["memory_gb"] for s in MOCK_SERVERS)
    total_disk_tb = sum(s["disk_tb"] for s in MOCK_SERVERS)
    
    # 在线服务器的平均负载
    online_servers = [s for s in MOCK_SERVERS if s["status"] == "online"]
    avg_load = 0
    if online_servers:
        avg_load = sum(s["load_average"][0] for s in online_servers) / len(online_servers)
    
    return {
        "total_servers": total_servers,
        "status_distribution": status_count,
        "datacenter_distribution": datacenter_count,
        "total_resources": {
            "cpu_cores": total_cpu_cores,
            "memory_gb": total_memory_gb,
            "disk_tb": total_disk_tb
        },
        "online_servers": len(online_servers),
        "average_load": round(avg_load, 2),
        "last_update": datetime.now().isoformat()
    }

@mcp.tool()
async def check_server_health(server_id: str) -> Dict[str, Any]:
    """
    检查指定服务器的健康状态
    
    参数:
    - server_id: 服务器ID
    
    返回服务器的健康检查结果
    """
    server = None
    for s in MOCK_SERVERS:
        if s["id"] == server_id:
            server = s
            break
    
    if not server:
        return {
            "error": f"Server with ID '{server_id}' not found"
        }
    
    # 模拟健康检查
    health_status = {
        "server_id": server_id,
        "hostname": server["hostname"],
        "overall_health": "healthy" if server["status"] == "online" else "unhealthy",
        "checks": {
            "connectivity": server["status"] == "online",
            "cpu_usage": "normal" if server["load_average"][0] < server["cpu_cores"] * 0.8 else "high",
            "memory_pressure": "normal",  # 模拟值
            "disk_space": "adequate",  # 模拟值
            "uptime": f"{server['uptime_days']} days",
        },
        "timestamp": datetime.now().isoformat()
    }
    
    if server["status"] == "maintenance":
        health_status["maintenance_note"] = "Server is under scheduled maintenance"
    elif server["status"] == "offline":
        health_status["offline_reason"] = "Connection lost - requires investigation"
    
    return health_status

# 启动 MCP server
if __name__ == "__main__":
    print("Starting Cluster Management MCP Server...", flush=True)
    mcp.run()