"""MCP 客户端封装"""
import json
import asyncio
import subprocess
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP 客户端，用于与 Mock MCP 服务器通信"""
    
    def __init__(self, server_command: List[str], timeout: int = 30):
        """
        初始化 MCP 客户端
        
        Args:
            server_command: 启动 MCP 服务器的命令
            timeout: 请求超时时间（秒）
        """
        self.server_command = server_command
        self.timeout = timeout
        self.process = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop()
    
    async def start(self):
        """启动 MCP 服务器进程"""
        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info("MCP 服务器进程已启动")
            # 给服务器一点启动时间
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"启动 MCP 服务器失败: {e}")
            raise
    
    async def stop(self):
        """停止 MCP 服务器进程"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            logger.info("MCP 服务器进程已停止")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用 MCP 工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具返回结果
        """
        if not self.process:
            raise RuntimeError("MCP 服务器未启动")
        
        # 构造 JSON-RPC 请求
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 1
        }
        
        try:
            # 发送请求
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()
            
            # 读取响应
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=self.timeout
            )
            response = json.loads(response_line.decode())
            
            if "error" in response:
                logger.error(f"MCP 工具调用错误: {response['error']}")
                return {"error": response["error"]}
            
            return response.get("result", {})
            
        except asyncio.TimeoutError:
            logger.error(f"MCP 工具调用超时: {tool_name}")
            return {"error": "请求超时"}
        except Exception as e:
            logger.error(f"MCP 工具调用异常: {e}")
            return {"error": str(e)}
    
    async def list_servers(self, **kwargs) -> Dict[str, Any]:
        """查询服务器列表"""
        return await self.call_tool("list_servers", kwargs)
    
    async def get_server_details(self, server_id: str) -> Dict[str, Any]:
        """获取服务器详情"""
        return await self.call_tool("get_server_details", {"server_id": server_id})
    
    async def get_server_topology(self, server_id: str) -> Dict[str, Any]:
        """获取服务器拓扑"""
        return await self.call_tool("get_server_topology", {"server_id": server_id})
    
    async def get_rack_topology(self, rack_id: str) -> Dict[str, Any]:
        """获取机柜拓扑"""
        return await self.call_tool("get_rack_topology", {"rack_id": rack_id})
    
    async def get_switch_info(self, switch_id: str) -> Dict[str, Any]:
        """获取交换机信息"""
        return await self.call_tool("get_switch_info", {"switch_id": switch_id})
    
    async def get_installation_logs(self, server_id: str, 
                                  start_time: Optional[str] = None,
                                  end_time: Optional[str] = None) -> Dict[str, Any]:
        """获取安装日志"""
        params = {"server_id": server_id}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        return await self.call_tool("get_installation_logs", params)
    
    async def analyze_installation_failure(self, server_id: str) -> Dict[str, Any]:
        """分析安装失败原因"""
        return await self.call_tool("analyze_installation_failure", {"server_id": server_id})


class MockMCPClient(MCPClient):
    """Mock MCP 客户端，直接调用本地函数而不启动进程"""
    
    def __init__(self):
        """初始化 Mock 客户端"""
        super().__init__([], timeout=30)
        # 导入 mock_mcp_server 模块
        from cz_agent_simple import mock_mcp_server
        self.mock_server = mock_mcp_server
    
    async def start(self):
        """Mock 启动"""
        logger.info("使用 Mock MCP 客户端")
    
    async def stop(self):
        """Mock 停止"""
        pass
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """直接调用 mock 服务器的函数"""
        try:
            # 获取对应的函数
            tool_func = getattr(self.mock_server, tool_name)
            # 调用函数
            result = await tool_func(**arguments)
            return result
        except AttributeError:
            logger.error(f"未找到工具: {tool_name}")
            return {"error": f"未找到工具: {tool_name}"}
        except Exception as e:
            logger.error(f"调用工具 {tool_name} 时出错: {e}")
            return {"error": str(e)}