"""LangChain 工具定义"""
from typing import Optional, Dict, Any, List
from langchain.tools import tool
from pydantic import BaseModel, Field
import logging
from cz_agent_simple.mcp_client import MockMCPClient

logger = logging.getLogger(__name__)

# 创建全局 MCP 客户端实例
mcp_client = MockMCPClient()


class ServerQueryInput(BaseModel):
    """服务器查询输入"""
    status: Optional[str] = Field(None, description="服务器状态筛选 (online/offline/maintenance/installing/install_failed)")
    region: Optional[str] = Field(None, description="区域筛选")
    room: Optional[str] = Field(None, description="机房筛选")
    rack: Optional[str] = Field(None, description="机柜筛选")


class ServerDetailsInput(BaseModel):
    """服务器详情输入"""
    server_id: str = Field(..., description="服务器ID")


class TopologyInput(BaseModel):
    """拓扑查询输入"""
    server_id: str = Field(..., description="服务器ID")


class RackTopologyInput(BaseModel):
    """机柜拓扑输入"""
    rack_id: str = Field(..., description="机柜ID")


class SwitchInput(BaseModel):
    """交换机查询输入"""
    switch_id: str = Field(..., description="交换机ID")


class InstallationLogInput(BaseModel):
    """安装日志查询输入"""
    server_id: str = Field(..., description="服务器ID")
    start_time: Optional[str] = Field(None, description="开始时间（ISO格式）")
    end_time: Optional[str] = Field(None, description="结束时间（ISO格式）")


class FailureAnalysisInput(BaseModel):
    """故障分析输入"""
    server_id: str = Field(..., description="服务器ID")


@tool("query_servers", args_schema=ServerQueryInput)
async def query_servers_tool(
    status: Optional[str] = None,
    region: Optional[str] = None,
    room: Optional[str] = None,
    rack: Optional[str] = None
) -> Dict[str, Any]:
    """
    查询服务器列表
    
    可以根据状态、区域、机房、机柜等条件筛选服务器。
    返回符合条件的服务器列表及其基本信息。
    """
    try:
        await mcp_client.start()
        result = await mcp_client.list_servers(
            status=status,
            region=region,
            room=room,
            rack=rack
        )
        return result
    except Exception as e:
        logger.error(f"查询服务器列表失败: {e}")
        return {"error": str(e)}
    finally:
        await mcp_client.stop()


@tool("get_server_details", args_schema=ServerDetailsInput)
async def get_server_details_tool(server_id: str) -> Dict[str, Any]:
    """
    获取服务器详细信息
    
    根据服务器ID获取详细的硬件配置、位置信息、运行状态等。
    """
    try:
        await mcp_client.start()
        result = await mcp_client.get_server_details(server_id)
        return result
    except Exception as e:
        logger.error(f"获取服务器详情失败: {e}")
        return {"error": str(e)}
    finally:
        await mcp_client.stop()


@tool("get_server_topology", args_schema=TopologyInput)
async def get_server_topology_tool(server_id: str) -> Dict[str, Any]:
    """
    获取服务器网络拓扑
    
    获取服务器的带内/带外网络拓扑结构，包括网络路径、连通性状态等。
    可用于诊断网络连接问题。
    """
    try:
        await mcp_client.start()
        result = await mcp_client.get_server_topology(server_id)
        return result
    except Exception as e:
        logger.error(f"获取服务器拓扑失败: {e}")
        return {"error": str(e)}
    finally:
        await mcp_client.stop()


@tool("get_rack_topology", args_schema=RackTopologyInput)
async def get_rack_topology_tool(rack_id: str) -> Dict[str, Any]:
    """
    获取机柜级别的拓扑信息
    
    获取整个机柜内所有服务器的网络连通性汇总，
    可用于识别机柜级别的网络故障（如上联交换机问题）。
    """
    try:
        await mcp_client.start()
        result = await mcp_client.get_rack_topology(rack_id)
        return result
    except Exception as e:
        logger.error(f"获取机柜拓扑失败: {e}")
        return {"error": str(e)}
    finally:
        await mcp_client.stop()


@tool("get_switch_info", args_schema=SwitchInput)
async def get_switch_info_tool(switch_id: str) -> Dict[str, Any]:
    """
    获取交换机信息
    
    获取交换机的详细信息，包括端口状态、连接的服务器等。
    """
    try:
        await mcp_client.start()
        result = await mcp_client.get_switch_info(switch_id)
        return result
    except Exception as e:
        logger.error(f"获取交换机信息失败: {e}")
        return {"error": str(e)}
    finally:
        await mcp_client.stop()


@tool("get_installation_logs", args_schema=InstallationLogInput)
async def get_installation_logs_tool(
    server_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取服务器安装日志
    
    获取服务器的安装过程日志，包括错误信息、警告等。
    可用于分析安装失败的原因。
    """
    try:
        await mcp_client.start()
        result = await mcp_client.get_installation_logs(
            server_id,
            start_time=start_time,
            end_time=end_time
        )
        return result
    except Exception as e:
        logger.error(f"获取安装日志失败: {e}")
        return {"error": str(e)}
    finally:
        await mcp_client.stop()


@tool("analyze_installation_failure", args_schema=FailureAnalysisInput)
async def analyze_installation_failure_tool(server_id: str) -> Dict[str, Any]:
    """
    分析服务器安装失败原因
    
    综合分析服务器的安装日志、网络拓扑、交换机状态等信息，
    提供故障诊断结果和修复建议。
    """
    try:
        await mcp_client.start()
        result = await mcp_client.analyze_installation_failure(server_id)
        return result
    except Exception as e:
        logger.error(f"分析安装失败原因失败: {e}")
        return {"error": str(e)}
    finally:
        await mcp_client.stop()


# 导出所有工具
ALL_TOOLS = [
    query_servers_tool,
    get_server_details_tool,
    get_server_topology_tool,
    get_rack_topology_tool,
    get_switch_info_tool,
    get_installation_logs_tool,
    analyze_installation_failure_tool
]