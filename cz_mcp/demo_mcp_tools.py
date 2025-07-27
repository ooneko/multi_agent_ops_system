#!/usr/bin/env python
"""
MCP Server 工具测试脚本
用于验证 MCP server 的各个工具功能
"""

import asyncio
import json
from cluster_server import mcp, list_servers, get_server_details, get_cluster_summary, check_server_health


async def test_all_tools():
    """测试所有 MCP 工具"""
    print("=== MCP Server 工具测试 ===\n")
    
    # 1. 测试列出所有服务器
    print("1. 获取所有服务器列表:")
    servers = await list_servers()
    print(f"   找到 {len(servers)} 台服务器")
    for server in servers:
        print(f"   - {server['hostname']} ({server['ip']}) - 状态: {server['status']}")
    print()
    
    # 2. 测试按状态筛选
    print("2. 筛选在线服务器:")
    online_servers = await list_servers(status="online")
    print(f"   找到 {len(online_servers)} 台在线服务器")
    for server in online_servers:
        print(f"   - {server['hostname']} - CPU: {server['cpu_cores']} 核, 内存: {server['memory_gb']} GB")
    print()
    
    # 3. 测试按资源筛选
    print("3. 筛选高配置服务器 (内存 >= 128GB):")
    high_mem_servers = await list_servers(min_memory_gb=128)
    print(f"   找到 {len(high_mem_servers)} 台高配置服务器")
    for server in high_mem_servers:
        print(f"   - {server['hostname']} - 内存: {server['memory_gb']} GB, CPU: {server['cpu_cores']} 核")
    print()
    
    # 4. 测试获取服务器详情
    print("4. 获取特定服务器详情 (server-001):")
    details = await get_server_details("server-001")
    if "error" not in details:
        print(f"   主机名: {details['hostname']}")
        print(f"   CPU: {details['cpu']}")
        print(f"   内存: {details['memory_gb']} GB")
        print(f"   磁盘: {details['disk_tb']} TB")
        print(f"   运行时间: {details['uptime_days']} 天")
        print(f"   负载: {details['load_average']}")
    print()
    
    # 5. 测试集群概况
    print("5. 获取集群概况统计:")
    summary = await get_cluster_summary()
    print(f"   总服务器数: {summary['total_servers']}")
    print(f"   状态分布: {json.dumps(summary['status_distribution'], ensure_ascii=False)}")
    print(f"   数据中心分布: {json.dumps(summary['datacenter_distribution'], ensure_ascii=False)}")
    print(f"   总资源:")
    print(f"     - CPU 核心数: {summary['total_resources']['cpu_cores']}")
    print(f"     - 内存总量: {summary['total_resources']['memory_gb']} GB")
    print(f"     - 磁盘总量: {summary['total_resources']['disk_tb']} TB")
    print(f"   在线服务器平均负载: {summary['average_load']}")
    print()
    
    # 6. 测试健康检查
    print("6. 检查服务器健康状态:")
    for server_id in ["server-001", "server-004", "server-005"]:
        health = await check_server_health(server_id)
        if "error" not in health:
            print(f"   {health['hostname']}:")
            print(f"     - 整体健康状态: {health['overall_health']}")
            print(f"     - 连接状态: {'正常' if health['checks']['connectivity'] else '异常'}")
            print(f"     - CPU 使用: {health['checks']['cpu_usage']}")
            if "maintenance_note" in health:
                print(f"     - 维护说明: {health['maintenance_note']}")
            if "offline_reason" in health:
                print(f"     - 离线原因: {health['offline_reason']}")
    print()
    
    # 7. 测试组合筛选
    print("7. 组合筛选 (北京数据中心的在线高配服务器):")
    filtered_servers = await list_servers(
        status="online",
        datacenter="DC-Beijing",
        min_memory_gb=128
    )
    print(f"   找到 {len(filtered_servers)} 台符合条件的服务器")
    for server in filtered_servers:
        print(f"   - {server['hostname']} - {server['datacenter']}, {server['memory_gb']} GB")
    print()
    
    print("=== 测试完成 ===")


def list_available_tools():
    """列出所有可用的 MCP 工具"""
    print("\n=== 可用的 MCP 工具 ===\n")
    
    tools = [
        {
            "name": "list_servers",
            "description": "查询集群中的物理机列表",
            "parameters": [
                "status: 筛选特定状态 (online/offline/maintenance)",
                "datacenter: 筛选特定数据中心",
                "min_memory_gb: 筛选内存大于等于指定值的服务器",
                "min_cpu_cores: 筛选CPU核心数大于等于指定值的服务器"
            ]
        },
        {
            "name": "get_server_details",
            "description": "获取指定物理机的详细信息",
            "parameters": [
                "server_id: 服务器ID"
            ]
        },
        {
            "name": "get_cluster_summary",
            "description": "获取集群概况统计信息",
            "parameters": []
        },
        {
            "name": "check_server_health",
            "description": "检查指定服务器的健康状态",
            "parameters": [
                "server_id: 服务器ID"
            ]
        }
    ]
    
    for tool in tools:
        print(f"📌 {tool['name']}")
        print(f"   描述: {tool['description']}")
        if tool['parameters']:
            print("   参数:")
            for param in tool['parameters']:
                print(f"     - {param}")
        else:
            print("   参数: 无")
        print()


if __name__ == "__main__":
    print("Cluster Management MCP Server 测试工具\n")
    print("选择操作:")
    print("1. 运行完整测试")
    print("2. 列出可用工具")
    
    choice = input("\n请输入选项 (1 或 2): ").strip()
    
    if choice == "1":
        asyncio.run(test_all_tools())
    elif choice == "2":
        list_available_tools()
    else:
        print("无效选项，请输入 1 或 2")