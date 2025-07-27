"""Mock MCP Server - 提供运维数据的模拟服务"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random
from mcp.server.fastmcp import FastMCP
from cz_agent_simple.models import (
    ServerStatus, ConnectivityStatus, ServerDetails, TopologyInfo,
    SwitchInfo, InstallationLog, HardwareInfo, LocationInfo,
    NetworkPath, ConnectivityInfo, PortInfo, LogEntry
)

mcp = FastMCP("沧竹Mock数据服务")

# 模拟数据存储
MOCK_SERVERS: Dict[str, ServerDetails] = {}
MOCK_TOPOLOGIES: Dict[str, TopologyInfo] = {}
MOCK_SWITCHES: Dict[str, SwitchInfo] = {}
MOCK_INSTALLATION_LOGS: Dict[str, List[InstallationLog]] = {}


def init_mock_data():
    """初始化模拟数据"""
    regions = ["cn-north", "cn-south"]
    azs = ["az1", "az2"]
    rooms = ["room-01", "room-02", "room-03"]
    racks = ["rack-A01", "rack-A02", "rack-B01", "rack-B02"]
    
    # 创建交换机
    switch_id = 1
    for region in regions:
        for az in azs:
            for room in rooms:
                for rack in racks:
                    # ToR 交换机
                    tor_switch_id = f"sw-tor-{switch_id:03d}"
                    location = LocationInfo(
                        region=region,
                        availability_zone=az,
                        room=room,
                        rack_id=rack,
                        rack_position=0
                    )
                    
                    ports = []
                    for port_num in range(1, 49):  # 48 端口交换机
                        port = PortInfo(
                            port_id=f"{tor_switch_id}-port-{port_num}",
                            port_number=port_num,
                            status="up" if port_num <= 20 else "down",
                            speed_gbps=10
                        )
                        ports.append(port)
                    
                    switch = SwitchInfo(
                        switch_id=tor_switch_id,
                        name=f"ToR-{region}-{az}-{room}-{rack}",
                        model="Cisco Nexus 9300",
                        status="active",
                        location=location,
                        ports=ports,
                        connected_servers=[],
                        uplink_switch=f"sw-agg-{region}-{az}-{room}"
                    )
                    MOCK_SWITCHES[tor_switch_id] = switch
                    switch_id += 1
    
    # 创建服务器
    server_id = 1
    for region in regions:
        for az in azs:
            for room in rooms:
                for rack in racks:
                    for position in range(1, 11):  # 每个机柜10台服务器
                        srv_id = f"srv-{server_id:04d}"
                        
                        # 设置不同的状态
                        if server_id % 15 == 0:
                            status = ServerStatus.OFFLINE
                        elif server_id % 20 == 0:
                            status = ServerStatus.INSTALL_FAILED
                        elif server_id % 25 == 0:
                            status = ServerStatus.MAINTENANCE
                        else:
                            status = ServerStatus.ONLINE
                        
                        hardware = HardwareInfo(
                            cpu_model="Intel Xeon Gold 6248R",
                            cpu_cores=48,
                            memory_gb=256,
                            disk_gb=2000,
                            network_cards=["eth0", "eth1", "eth2", "eth3"]
                        )
                        
                        location = LocationInfo(
                            region=region,
                            availability_zone=az,
                            room=room,
                            rack_id=rack,
                            rack_position=position
                        )
                        
                        server = ServerDetails(
                            server_id=srv_id,
                            hostname=f"server-{region}-{az}-{room}-{server_id:04d}",
                            status=status,
                            ip_address=f"10.{ord(region[-1]) % 256}.{server_id // 256}.{server_id % 256}",
                            hardware=hardware,
                            location=location,
                            created_at=datetime.now() - timedelta(days=random.randint(1, 365)),
                            updated_at=datetime.now() - timedelta(hours=random.randint(1, 72)),
                            tags={"env": "prod", "tier": "compute"}
                        )
                        MOCK_SERVERS[srv_id] = server
                        
                        # 创建拓扑信息
                        tor_switch = f"sw-tor-{((server_id - 1) // 10 + 1):03d}"
                        
                        # 模拟网络故障场景
                        if rack == "rack-A02" and room == "room-01":
                            # 整个机柜带外网络故障
                            oob_status = ConnectivityStatus.DISCONNECTED
                            oob_connected = False
                            oob_failure = "机柜上联交换机端口故障"
                        elif server_id % 30 == 0:
                            # 个别服务器网络问题
                            oob_status = ConnectivityStatus.DISCONNECTED
                            oob_connected = False
                            oob_failure = "BMC网卡故障"
                        else:
                            oob_status = ConnectivityStatus.CONNECTED
                            oob_connected = True
                            oob_failure = None
                        
                        topology = TopologyInfo(
                            server_id=srv_id,
                            region=region,
                            availability_zone=az,
                            room=room,
                            rack_id=rack,
                            rack_position=position,
                            in_band_network=NetworkPath(
                                path=[srv_id, tor_switch, f"sw-agg-{region}-{az}", f"sw-core-{region}"],
                                status=ConnectivityStatus.CONNECTED
                            ),
                            out_of_band_network=NetworkPath(
                                path=[f"{srv_id}-bmc", f"{tor_switch}-oob", f"sw-oob-{room}", f"sw-oob-core"],
                                status=oob_status,
                                last_hop_reachable=f"{tor_switch}-oob" if not oob_connected else None
                            ),
                            uplink_switches=[tor_switch],
                            in_band_connectivity=ConnectivityInfo(
                                is_connected=True,
                                last_check_time=datetime.now()
                            ),
                            out_of_band_connectivity=ConnectivityInfo(
                                is_connected=oob_connected,
                                last_check_time=datetime.now(),
                                failure_reason=oob_failure
                            )
                        )
                        MOCK_TOPOLOGIES[srv_id] = topology
                        
                        # 为装机失败的服务器创建日志
                        if status == ServerStatus.INSTALL_FAILED:
                            logs = []
                            start_time = datetime.now() - timedelta(hours=2)
                            
                            # 根据不同场景生成不同的错误日志
                            if server_id % 40 == 0:
                                # 硬件故障
                                logs.extend([
                                    LogEntry(
                                        timestamp=start_time,
                                        level="INFO",
                                        message="开始服务器安装流程",
                                        component="installer"
                                    ),
                                    LogEntry(
                                        timestamp=start_time + timedelta(minutes=5),
                                        level="ERROR",
                                        message="磁盘检测失败: /dev/sda not found",
                                        component="disk-check",
                                        details={"expected_disks": 4, "found_disks": 3}
                                    ),
                                    LogEntry(
                                        timestamp=start_time + timedelta(minutes=6),
                                        level="ERROR",
                                        message="硬件检查未通过，终止安装",
                                        component="installer"
                                    )
                                ])
                                error_summary = "硬件故障：磁盘缺失"
                            elif server_id % 60 == 0:
                                # 网络配置错误
                                logs.extend([
                                    LogEntry(
                                        timestamp=start_time,
                                        level="INFO",
                                        message="开始服务器安装流程",
                                        component="installer"
                                    ),
                                    LogEntry(
                                        timestamp=start_time + timedelta(minutes=10),
                                        level="ERROR",
                                        message="网络配置失败: DHCP请求超时",
                                        component="network-setup",
                                        details={"interface": "eth0", "timeout": 30}
                                    ),
                                    LogEntry(
                                        timestamp=start_time + timedelta(minutes=11),
                                        level="ERROR",
                                        message="无法获取IP地址，安装失败",
                                        component="installer"
                                    )
                                ])
                                error_summary = "网络配置错误：DHCP失败"
                            else:
                                # 软件包错误
                                logs.extend([
                                    LogEntry(
                                        timestamp=start_time,
                                        level="INFO",
                                        message="开始服务器安装流程",
                                        component="installer"
                                    ),
                                    LogEntry(
                                        timestamp=start_time + timedelta(minutes=20),
                                        level="ERROR",
                                        message="软件包安装失败: 依赖冲突",
                                        component="package-installer",
                                        details={"package": "kernel-5.10", "conflict": "kernel-headers"}
                                    )
                                ])
                                error_summary = "软件配置错误：包依赖冲突"
                            
                            install_log = InstallationLog(
                                server_id=srv_id,
                                start_time=start_time,
                                end_time=start_time + timedelta(minutes=30),
                                status="failed",
                                logs=logs,
                                error_summary=error_summary
                            )
                            MOCK_INSTALLATION_LOGS[srv_id] = [install_log]
                        
                        # 更新交换机的连接服务器列表
                        if tor_switch in MOCK_SWITCHES:
                            MOCK_SWITCHES[tor_switch].connected_servers.append(srv_id)
                            # 更新端口连接信息
                            port_idx = (position - 1) % 48
                            if port_idx < len(MOCK_SWITCHES[tor_switch].ports):
                                MOCK_SWITCHES[tor_switch].ports[port_idx].connected_device = srv_id
                        
                        server_id += 1


# 初始化数据
init_mock_data()


@mcp.tool()
async def list_servers(
    status: Optional[str] = None,
    datacenter: Optional[str] = None,
    region: Optional[str] = None,
    room: Optional[str] = None,
    rack: Optional[str] = None
) -> Dict[str, Any]:
    """查询服务器列表
    
    Args:
        status: 服务器状态筛选 (online/offline/maintenance/installing/install_failed)
        datacenter: 数据中心筛选
        region: 区域筛选
        room: 机房筛选
        rack: 机柜筛选
    
    Returns:
        服务器列表信息
    """
    servers = []
    
    for srv_id, server in MOCK_SERVERS.items():
        # 应用筛选条件
        if status and server.status.value != status:
            continue
        if region and server.location.region != region:
            continue
        if room and server.location.room != room:
            continue
        if rack and server.location.rack_id != rack:
            continue
        
        servers.append({
            "server_id": server.server_id,
            "hostname": server.hostname,
            "status": server.status.value,
            "ip_address": server.ip_address,
            "location": {
                "region": server.location.region,
                "az": server.location.availability_zone,
                "room": server.location.room,
                "rack": server.location.rack_id,
                "position": server.location.rack_position
            }
        })
    
    return {
        "total": len(servers),
        "servers": servers
    }


@mcp.tool()
async def get_server_details(server_id: str) -> Dict[str, Any]:
    """获取服务器详细信息
    
    Args:
        server_id: 服务器ID
    
    Returns:
        服务器详细信息
    """
    if server_id not in MOCK_SERVERS:
        return {
            "error": f"服务器 {server_id} 不存在",
            "available_ids": list(MOCK_SERVERS.keys())[:5]
        }
    
    server = MOCK_SERVERS[server_id]
    return {
        "server_id": server.server_id,
        "hostname": server.hostname,
        "status": server.status.value,
        "ip_address": server.ip_address,
        "hardware": {
            "cpu_model": server.hardware.cpu_model,
            "cpu_cores": server.hardware.cpu_cores,
            "memory_gb": server.hardware.memory_gb,
            "disk_gb": server.hardware.disk_gb,
            "network_cards": server.hardware.network_cards
        },
        "location": {
            "region": server.location.region,
            "availability_zone": server.location.availability_zone,
            "room": server.location.room,
            "rack_id": server.location.rack_id,
            "rack_position": server.location.rack_position
        },
        "created_at": server.created_at.isoformat(),
        "updated_at": server.updated_at.isoformat(),
        "tags": server.tags
    }


@mcp.tool()
async def get_server_topology(server_id: str) -> Dict[str, Any]:
    """获取服务器网络拓扑信息
    
    Args:
        server_id: 服务器ID
    
    Returns:
        服务器的网络拓扑信息，包括带内/带外网络路径和连通性
    """
    if server_id not in MOCK_TOPOLOGIES:
        return {
            "error": f"服务器 {server_id} 的拓扑信息不存在",
            "available_ids": list(MOCK_TOPOLOGIES.keys())[:5]
        }
    
    topology = MOCK_TOPOLOGIES[server_id]
    return {
        "server_id": topology.server_id,
        "location": {
            "region": topology.region,
            "availability_zone": topology.availability_zone,
            "room": topology.room,
            "rack_id": topology.rack_id,
            "rack_position": topology.rack_position
        },
        "in_band_network": {
            "path": topology.in_band_network.path,
            "status": topology.in_band_network.status.value,
            "connectivity": {
                "is_connected": topology.in_band_connectivity.is_connected,
                "last_check": topology.in_band_connectivity.last_check_time.isoformat()
            }
        },
        "out_of_band_network": {
            "path": topology.out_of_band_network.path,
            "status": topology.out_of_band_network.status.value,
            "last_hop_reachable": topology.out_of_band_network.last_hop_reachable,
            "connectivity": {
                "is_connected": topology.out_of_band_connectivity.is_connected,
                "last_check": topology.out_of_band_connectivity.last_check_time.isoformat(),
                "failure_reason": topology.out_of_band_connectivity.failure_reason
            }
        },
        "uplink_switches": topology.uplink_switches
    }


@mcp.tool()
async def get_rack_topology(rack_id: str) -> Dict[str, Any]:
    """获取整个机柜的拓扑信息
    
    Args:
        rack_id: 机柜ID
    
    Returns:
        机柜内所有服务器的拓扑汇总信息
    """
    rack_servers = []
    oob_connected_count = 0
    ib_connected_count = 0
    
    for srv_id, topology in MOCK_TOPOLOGIES.items():
        if topology.rack_id == rack_id:
            server_info = {
                "server_id": srv_id,
                "position": topology.rack_position,
                "in_band_connected": topology.in_band_connectivity.is_connected,
                "out_of_band_connected": topology.out_of_band_connectivity.is_connected
            }
            rack_servers.append(server_info)
            
            if topology.in_band_connectivity.is_connected:
                ib_connected_count += 1
            if topology.out_of_band_connectivity.is_connected:
                oob_connected_count += 1
    
    if not rack_servers:
        return {
            "error": f"机柜 {rack_id} 不存在或没有服务器",
            "available_racks": list(set(t.rack_id for t in MOCK_TOPOLOGIES.values()))[:5]
        }
    
    # 分析整体连通性
    total_servers = len(rack_servers)
    oob_failure_rate = 1 - (oob_connected_count / total_servers)
    
    analysis = {
        "rack_id": rack_id,
        "total_servers": total_servers,
        "in_band_connected": ib_connected_count,
        "out_of_band_connected": oob_connected_count,
        "servers": sorted(rack_servers, key=lambda x: x["position"])
    }
    
    # 如果带外网络大面积故障，可能是上联交换机问题
    if oob_failure_rate > 0.8:
        analysis["alert"] = "机柜带外网络大面积故障，可能是上联交换机问题"
        analysis["recommended_action"] = "检查机柜带外网络上联交换机"
    
    return analysis


@mcp.tool()
async def get_switch_info(switch_id: str) -> Dict[str, Any]:
    """获取交换机信息
    
    Args:
        switch_id: 交换机ID
    
    Returns:
        交换机详细信息
    """
    if switch_id not in MOCK_SWITCHES:
        return {
            "error": f"交换机 {switch_id} 不存在",
            "available_ids": list(MOCK_SWITCHES.keys())[:5]
        }
    
    switch = MOCK_SWITCHES[switch_id]
    
    # 统计端口状态
    ports_up = sum(1 for p in switch.ports if p.status == "up")
    ports_down = sum(1 for p in switch.ports if p.status == "down")
    
    return {
        "switch_id": switch.switch_id,
        "name": switch.name,
        "model": switch.model,
        "status": switch.status,
        "location": {
            "region": switch.location.region,
            "availability_zone": switch.location.availability_zone,
            "room": switch.location.room,
            "rack_id": switch.location.rack_id
        },
        "port_summary": {
            "total": len(switch.ports),
            "up": ports_up,
            "down": ports_down
        },
        "connected_servers": switch.connected_servers,
        "uplink_switch": switch.uplink_switch
    }


@mcp.tool()
async def get_installation_logs(
    server_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Dict[str, Any]:
    """获取服务器安装日志
    
    Args:
        server_id: 服务器ID
        start_time: 开始时间（ISO格式）
        end_time: 结束时间（ISO格式）
    
    Returns:
        安装日志信息
    """
    if server_id not in MOCK_INSTALLATION_LOGS:
        # 检查服务器是否存在
        if server_id not in MOCK_SERVERS:
            return {
                "error": f"服务器 {server_id} 不存在"
            }
        else:
            return {
                "server_id": server_id,
                "message": "该服务器没有安装日志",
                "server_status": MOCK_SERVERS[server_id].status.value
            }
    
    logs = MOCK_INSTALLATION_LOGS[server_id]
    
    # 返回最新的安装日志
    if logs:
        latest_log = logs[-1]
        return {
            "server_id": server_id,
            "installation": {
                "start_time": latest_log.start_time.isoformat(),
                "end_time": latest_log.end_time.isoformat() if latest_log.end_time else None,
                "status": latest_log.status,
                "error_summary": latest_log.error_summary,
                "logs": [
                    {
                        "timestamp": log.timestamp.isoformat(),
                        "level": log.level,
                        "message": log.message,
                        "component": log.component,
                        "details": log.details
                    }
                    for log in latest_log.logs
                ]
            }
        }
    
    return {
        "server_id": server_id,
        "message": "没有找到安装日志"
    }


@mcp.tool()
async def analyze_installation_failure(server_id: str) -> Dict[str, Any]:
    """分析服务器安装失败原因
    
    综合分析服务器的安装日志、网络拓扑和交换机状态，提供故障诊断和建议
    
    Args:
        server_id: 服务器ID
    
    Returns:
        故障分析结果和修复建议
    """
    analysis = {
        "server_id": server_id,
        "analysis_time": datetime.now().isoformat()
    }
    
    # 1. 检查服务器状态
    if server_id not in MOCK_SERVERS:
        return {
            "error": f"服务器 {server_id} 不存在"
        }
    
    server = MOCK_SERVERS[server_id]
    analysis["server_status"] = server.status.value
    
    if server.status != ServerStatus.INSTALL_FAILED:
        return {
            "server_id": server_id,
            "message": f"服务器当前状态为 {server.status.value}，不是安装失败状态"
        }
    
    # 2. 获取安装日志
    install_logs = MOCK_INSTALLATION_LOGS.get(server_id)
    if install_logs:
        latest_log = install_logs[-1]
        analysis["error_summary"] = latest_log.error_summary
        
        # 提取错误信息
        error_logs = [log for log in latest_log.logs if log.level == "ERROR"]
        analysis["error_count"] = len(error_logs)
        analysis["first_error"] = error_logs[0].message if error_logs else None
    
    # 3. 检查网络拓扑
    topology = MOCK_TOPOLOGIES.get(server_id)
    if topology:
        analysis["network_status"] = {
            "in_band": "connected" if topology.in_band_connectivity.is_connected else "disconnected",
            "out_of_band": "connected" if topology.out_of_band_connectivity.is_connected else "disconnected"
        }
        
        if topology.out_of_band_connectivity.failure_reason:
            analysis["oob_failure_reason"] = topology.out_of_band_connectivity.failure_reason
    
    # 4. 检查相关交换机
    if topology and topology.uplink_switches:
        switch_id = topology.uplink_switches[0]
        switch = MOCK_SWITCHES.get(switch_id)
        if switch:
            analysis["uplink_switch"] = {
                "switch_id": switch_id,
                "status": switch.status
            }
    
    # 5. 生成诊断结果和建议
    recommendations = []
    root_cause = "未知"
    
    if "error_summary" in analysis:
        if "硬件故障" in analysis["error_summary"]:
            root_cause = "硬件故障"
            recommendations.extend([
                "联系硬件供应商更换故障部件",
                "执行硬件诊断测试确认具体故障组件",
                "检查服务器硬件兼容性列表"
            ])
        elif "网络配置错误" in analysis["error_summary"]:
            root_cause = "网络配置问题"
            recommendations.extend([
                "检查DHCP服务器配置和可用性",
                "验证网络VLAN配置是否正确",
                "检查交换机端口配置",
                "确认网线连接正常"
            ])
        elif "软件配置错误" in analysis["error_summary"]:
            root_cause = "软件依赖问题"
            recommendations.extend([
                "更新软件仓库源",
                "检查软件包版本兼容性",
                "清理软件包缓存后重试",
                "使用备用软件源"
            ])
    
    # 检查是否是批量故障
    if topology:
        rack_analysis = await get_rack_topology(topology.rack_id)
        if "alert" in rack_analysis:
            recommendations.insert(0, f"注意：{rack_analysis['alert']}")
            recommendations.insert(1, rack_analysis["recommended_action"])
            root_cause = "可能是基础设施问题"
    
    analysis["diagnosis"] = {
        "root_cause": root_cause,
        "confidence": "high" if recommendations else "low",
        "recommendations": recommendations,
        "next_steps": [
            "执行建议的修复操作",
            "重新尝试安装",
            "如果问题持续，联系技术支持"
        ]
    }
    
    return analysis


# 主函数
if __name__ == "__main__":
    import sys
    print(f"沧竹Mock MCP服务器启动中...")
    print(f"服务器总数: {len(MOCK_SERVERS)}")
    print(f"交换机总数: {len(MOCK_SWITCHES)}")
    print(f"故障服务器数: {sum(1 for s in MOCK_SERVERS.values() if s.status == ServerStatus.INSTALL_FAILED)}")
    
    # 运行服务器
    mcp.run()