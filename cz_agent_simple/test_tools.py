"""工具函数测试"""
import unittest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

# 直接导入工具，不需要 mock langchain
from cz_agent_simple.tools import (
    query_servers_tool,
    get_server_details_tool,
    get_server_topology_tool,
    get_rack_topology_tool,
    get_switch_info_tool,
    get_installation_logs_tool,
    analyze_installation_failure_tool,
    ALL_TOOLS
)


class TestTools(unittest.TestCase):
    """测试 LangChain 工具函数"""
    
    def test_all_tools_exported(self):
        """测试所有工具都已导出"""
        self.assertEqual(len(ALL_TOOLS), 7)
        tool_names = [tool.name for tool in ALL_TOOLS]
        expected_names = [
            "query_servers",
            "get_server_details",
            "get_server_topology",
            "get_rack_topology",
            "get_switch_info",
            "get_installation_logs",
            "analyze_installation_failure"
        ]
        # 确保所有期望的工具名都在工具列表中
        self.assertEqual(set(tool_names), set(expected_names))
    
    @patch('cz_agent_simple.tools.mcp_client')
    def test_query_servers_tool(self, mock_client):
        """测试查询服务器工具"""
        async def run_test():
            # 模拟返回数据
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.list_servers = AsyncMock(return_value={
                "total": 2,
                "servers": [
                    {"server_id": "srv-001", "status": "online"},
                    {"server_id": "srv-002", "status": "offline"}
                ]
            })
            
            # 调用工具
            result = await query_servers_tool(status="online")
            
            # 验证调用
            mock_client.start.assert_called_once()
            mock_client.list_servers.assert_called_once_with(
                status="online",
                region=None,
                room=None,
                rack=None
            )
            mock_client.stop.assert_called_once()
            
            # 验证结果
            self.assertEqual(result["total"], 2)
            self.assertEqual(len(result["servers"]), 2)
        
        asyncio.run(run_test())
    
    @patch('cz_agent_simple.tools.mcp_client')
    def test_get_server_details_tool(self, mock_client):
        """测试获取服务器详情工具"""
        async def run_test():
            # 模拟返回数据
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.get_server_details = AsyncMock(return_value={
                "server_id": "srv-001",
                "status": "online",
                "hardware": {
                    "cpu_cores": 32,
                    "memory_gb": 128
                }
            })
            
            # 调用工具
            result = await get_server_details_tool(server_id="srv-001")
            
            # 验证调用
            mock_client.get_server_details.assert_called_once_with("srv-001")
            
            # 验证结果
            self.assertEqual(result["server_id"], "srv-001")
            self.assertEqual(result["status"], "online")
        
        asyncio.run(run_test())
    
    @patch('cz_agent_simple.tools.mcp_client')
    def test_analyze_installation_failure_tool(self, mock_client):
        """测试分析安装失败工具"""
        async def run_test():
            # 模拟返回数据
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.analyze_installation_failure = AsyncMock(return_value={
                "server_id": "srv-001",
                "diagnosis": {
                    "root_cause": "网络配置错误",
                    "confidence": "high",
                    "recommendations": ["检查DHCP服务器"]
                }
            })
            
            # 调用工具
            result = await analyze_installation_failure_tool(server_id="srv-001")
            
            # 验证结果
            self.assertEqual(result["server_id"], "srv-001")
            self.assertIn("diagnosis", result)
            self.assertEqual(result["diagnosis"]["root_cause"], "网络配置错误")
        
        asyncio.run(run_test())
    
    @patch('cz_agent_simple.tools.mcp_client')
    def test_error_handling(self, mock_client):
        """测试错误处理"""
        async def run_test():
            # 模拟错误
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.list_servers = AsyncMock(side_effect=Exception("连接失败"))
            
            # 调用工具
            result = await query_servers_tool()
            
            # 验证错误处理
            self.assertIn("error", result)
            self.assertIn("连接失败", result["error"])
            
            # 确保 stop 仍然被调用
            mock_client.stop.assert_called_once()
        
        asyncio.run(run_test())
    
    def test_tool_descriptions(self):
        """测试工具描述信息"""
        # 验证每个工具都有描述
        for tool in ALL_TOOLS:
            # 工具对象有多种类型，需要检查不同的属性
            if hasattr(tool, 'description'):
                self.assertIsNotNone(tool.description)
                if isinstance(tool.description, str):
                    self.assertGreater(len(tool.description), 10)
            elif hasattr(tool, '__doc__'):
                self.assertIsNotNone(tool.__doc__)
                self.assertGreater(len(tool.__doc__), 10)
    
    def test_tool_schemas(self):
        """测试工具参数模式"""
        # 验证关键工具都有 args_schema 属性
        for tool in [query_servers_tool, get_server_details_tool, analyze_installation_failure_tool]:
            self.assertTrue(hasattr(tool, 'args_schema'))
            # 如果 args_schema 存在且不为 None，验证它
            if getattr(tool, 'args_schema', None) is not None:
                self.assertIsNotNone(tool.args_schema)


if __name__ == "__main__":
    unittest.main()