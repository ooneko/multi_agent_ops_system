"""MCP 客户端测试"""
import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from cz_agent_simple.mcp_client import MCPClient, MockMCPClient


class TestMockMCPClient(unittest.TestCase):
    """测试 Mock MCP 客户端"""
    
    def setUp(self):
        """设置测试环境"""
        self.client = MockMCPClient()
    
    def test_initialization(self):
        """测试客户端初始化"""
        self.assertIsNotNone(self.client)
        self.assertIsNotNone(self.client.mock_server)
    
    def test_list_servers(self):
        """测试查询服务器列表"""
        async def run_test():
            async with self.client:
                result = await self.client.list_servers()
                self.assertIn("total", result)
                self.assertIn("servers", result)
                self.assertIsInstance(result["servers"], list)
        
        asyncio.run(run_test())
    
    def test_get_server_details(self):
        """测试获取服务器详情"""
        async def run_test():
            async with self.client:
                # 先获取服务器列表
                servers = await self.client.list_servers()
                if servers["servers"]:
                    server_id = servers["servers"][0]["server_id"]
                    result = await self.client.get_server_details(server_id)
                    self.assertEqual(result["server_id"], server_id)
                    self.assertIn("hardware", result)
                    self.assertIn("location", result)
        
        asyncio.run(run_test())
    
    def test_get_server_topology(self):
        """测试获取服务器拓扑"""
        async def run_test():
            async with self.client:
                # 先获取服务器列表
                servers = await self.client.list_servers()
                if servers["servers"]:
                    server_id = servers["servers"][0]["server_id"]
                    result = await self.client.get_server_topology(server_id)
                    self.assertEqual(result["server_id"], server_id)
                    self.assertIn("in_band_network", result)
                    self.assertIn("out_of_band_network", result)
        
        asyncio.run(run_test())
    
    def test_analyze_installation_failure(self):
        """测试分析安装失败"""
        async def run_test():
            async with self.client:
                # 查找安装失败的服务器
                servers = await self.client.list_servers(status="install_failed")
                if servers["servers"]:
                    server_id = servers["servers"][0]["server_id"]
                    result = await self.client.analyze_installation_failure(server_id)
                    self.assertEqual(result["server_id"], server_id)
                    self.assertIn("diagnosis", result)
                    self.assertIn("recommendations", result["diagnosis"])
        
        asyncio.run(run_test())
    
    def test_error_handling(self):
        """测试错误处理"""
        async def run_test():
            async with self.client:
                # 测试不存在的服务器
                result = await self.client.get_server_details("non-existent")
                self.assertIn("error", result)
                
                # 测试不存在的工具
                result = await self.client.call_tool("non_existent_tool", {})
                self.assertIn("error", result)
        
        asyncio.run(run_test())


class TestMCPClient(unittest.TestCase):
    """测试 MCP 客户端基类"""
    
    def test_initialization(self):
        """测试客户端初始化"""
        client = MCPClient(["python", "-m", "test"], timeout=10)
        self.assertEqual(client.server_command, ["python", "-m", "test"])
        self.assertEqual(client.timeout, 10)
        self.assertIsNone(client.process)
    
    @patch('asyncio.create_subprocess_exec')
    def test_start_stop(self, mock_subprocess):
        """测试启动和停止"""
        async def run_test():
            # 模拟进程
            mock_process = AsyncMock()
            mock_subprocess.return_value = mock_process
            
            client = MCPClient(["test"])
            await client.start()
            
            # 验证进程已创建
            mock_subprocess.assert_called_once()
            self.assertEqual(client.process, mock_process)
            
            # 测试停止
            await client.stop()
            mock_process.terminate.assert_called_once()
            mock_process.wait.assert_called_once()
        
        asyncio.run(run_test())
    
    @patch('asyncio.create_subprocess_exec')
    def test_call_tool(self, mock_subprocess):
        """测试工具调用"""
        async def run_test():
            # 模拟进程
            mock_process = AsyncMock()
            mock_process.stdin = AsyncMock()
            mock_process.stdout = AsyncMock()
            
            # 模拟响应
            response = {"jsonrpc": "2.0", "result": {"data": "test"}, "id": 1}
            mock_process.stdout.readline.return_value = json.dumps(response).encode() + b'\n'
            
            mock_subprocess.return_value = mock_process
            
            client = MCPClient(["test"])
            await client.start()
            
            # 调用工具
            result = await client.call_tool("test_tool", {"param": "value"})
            
            # 验证请求已发送
            mock_process.stdin.write.assert_called_once()
            mock_process.stdin.drain.assert_called_once()
            
            # 验证结果
            self.assertEqual(result, {"data": "test"})
        
        import json
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()