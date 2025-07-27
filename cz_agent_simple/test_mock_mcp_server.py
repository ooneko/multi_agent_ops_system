"""Mock MCP Server 测试"""
import unittest
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock
from cz_agent_simple.models import ServerStatus
from cz_agent_simple import mock_mcp_server


class TestMockMCPServer(unittest.TestCase):
    
    def setUp(self):
        """测试前重新初始化数据"""
        mock_mcp_server.MOCK_SERVERS.clear()
        mock_mcp_server.MOCK_TOPOLOGIES.clear()
        mock_mcp_server.MOCK_SWITCHES.clear()
        mock_mcp_server.MOCK_INSTALLATION_LOGS.clear()
        mock_mcp_server.init_mock_data()
    
    def test_init_mock_data(self):
        """测试数据初始化"""
        # 验证数据已创建
        self.assertGreater(len(mock_mcp_server.MOCK_SERVERS), 0)
        self.assertGreater(len(mock_mcp_server.MOCK_TOPOLOGIES), 0)
        self.assertGreater(len(mock_mcp_server.MOCK_SWITCHES), 0)
        
        # 验证有故障服务器
        failed_servers = [s for s in mock_mcp_server.MOCK_SERVERS.values() 
                         if s.status == ServerStatus.INSTALL_FAILED]
        self.assertGreater(len(failed_servers), 0)
        
        # 验证故障服务器有日志
        for server in failed_servers:
            self.assertIn(server.server_id, mock_mcp_server.MOCK_INSTALLATION_LOGS)
    
    def test_list_servers(self):
        """测试服务器列表查询"""
        async def run_test():
            # 查询所有服务器
            result = await mock_mcp_server.list_servers()
            self.assertIn("total", result)
            self.assertIn("servers", result)
            self.assertGreater(result["total"], 0)
            
            # 按状态筛选
            result = await mock_mcp_server.list_servers(status="online")
            for server in result["servers"]:
                self.assertEqual(server["status"], "online")
            
            # 按机房筛选
            result = await mock_mcp_server.list_servers(room="room-01")
            for server in result["servers"]:
                self.assertEqual(server["location"]["room"], "room-01")
        
        asyncio.run(run_test())
    
    def test_get_server_details(self):
        """测试获取服务器详情"""
        async def run_test():
            # 获取第一个服务器的ID
            servers = list(mock_mcp_server.MOCK_SERVERS.keys())
            if servers:
                server_id = servers[0]
                result = await mock_mcp_server.get_server_details(server_id)
                
                self.assertEqual(result["server_id"], server_id)
                self.assertIn("hardware", result)
                self.assertIn("location", result)
                self.assertIn("status", result)
            
            # 测试不存在的服务器
            result = await mock_mcp_server.get_server_details("non-existent")
            self.assertIn("error", result)
        
        asyncio.run(run_test())
    
    def test_get_server_topology(self):
        """测试获取服务器拓扑"""
        async def run_test():
            # 获取第一个服务器的拓扑
            servers = list(mock_mcp_server.MOCK_TOPOLOGIES.keys())
            if servers:
                server_id = servers[0]
                result = await mock_mcp_server.get_server_topology(server_id)
                
                self.assertEqual(result["server_id"], server_id)
                self.assertIn("in_band_network", result)
                self.assertIn("out_of_band_network", result)
                self.assertIn("uplink_switches", result)
        
        asyncio.run(run_test())
    
    def test_get_rack_topology(self):
        """测试获取机柜拓扑"""
        async def run_test():
            # 测试特定的故障机柜
            result = await mock_mcp_server.get_rack_topology("rack-A02")
            self.assertIn("total_servers", result)
            self.assertIn("servers", result)
            
            # 如果是预设的故障机柜，应该有告警
            if result.get("out_of_band_connected", 0) < result.get("total_servers", 1) * 0.2:
                self.assertIn("alert", result)
                self.assertIn("recommended_action", result)
        
        asyncio.run(run_test())
    
    def test_get_switch_info(self):
        """测试获取交换机信息"""
        async def run_test():
            switches = list(mock_mcp_server.MOCK_SWITCHES.keys())
            if switches:
                switch_id = switches[0]
                result = await mock_mcp_server.get_switch_info(switch_id)
                
                self.assertEqual(result["switch_id"], switch_id)
                self.assertIn("port_summary", result)
                self.assertIn("connected_servers", result)
        
        asyncio.run(run_test())
    
    def test_get_installation_logs(self):
        """测试获取安装日志"""
        async def run_test():
            # 找一个安装失败的服务器
            failed_servers = [s for s in mock_mcp_server.MOCK_SERVERS.values() 
                            if s.status == ServerStatus.INSTALL_FAILED]
            if failed_servers:
                server_id = failed_servers[0].server_id
                result = await mock_mcp_server.get_installation_logs(server_id)
                
                self.assertEqual(result["server_id"], server_id)
                self.assertIn("installation", result)
                self.assertEqual(result["installation"]["status"], "failed")
                self.assertIn("logs", result["installation"])
        
        asyncio.run(run_test())
    
    def test_analyze_installation_failure(self):
        """测试安装失败分析"""
        async def run_test():
            # 找一个安装失败的服务器
            failed_servers = [s for s in mock_mcp_server.MOCK_SERVERS.values() 
                            if s.status == ServerStatus.INSTALL_FAILED]
            if failed_servers:
                server_id = failed_servers[0].server_id
                result = await mock_mcp_server.analyze_installation_failure(server_id)
                
                self.assertEqual(result["server_id"], server_id)
                self.assertIn("diagnosis", result)
                self.assertIn("root_cause", result["diagnosis"])
                self.assertIn("recommendations", result["diagnosis"])
                self.assertIsInstance(result["diagnosis"]["recommendations"], list)
        
        asyncio.run(run_test())
    
    def test_network_failure_scenario(self):
        """测试网络故障场景"""
        async def run_test():
            # 测试预设的机柜带外网络故障场景
            # rack-A02 in room-01 应该有带外网络故障
            servers_in_rack = []
            for srv_id, topology in mock_mcp_server.MOCK_TOPOLOGIES.items():
                if topology.rack_id == "rack-A02" and topology.room == "room-01":
                    servers_in_rack.append(srv_id)
                    # 验证带外网络应该是断开的
                    self.assertFalse(topology.out_of_band_connectivity.is_connected)
                    self.assertIsNotNone(topology.out_of_band_connectivity.failure_reason)
            
            # 确保有服务器在这个机柜
            self.assertGreater(len(servers_in_rack), 0)
        
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()