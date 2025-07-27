#!/usr/bin/env python
"""
Tests for Cluster Management MCP Server
"""

import unittest
import asyncio
from cluster_server import list_servers, get_server_details, get_cluster_summary, check_server_health


class TestClusterServer(unittest.TestCase):
    """测试集群管理 MCP Server 的功能"""
    
    def _run_async(self, coro):
        """辅助方法运行异步函数"""
        return asyncio.get_event_loop().run_until_complete(coro)
    
    def test_list_servers_all(self):
        """测试获取所有服务器列表"""
        servers = self._run_async(list_servers())
        self.assertEqual(len(servers), 5)
        self.assertTrue(all("id" in server for server in servers))
        self.assertTrue(all("hostname" in server for server in servers))
        self.assertTrue(all("status" in server for server in servers))
    
    def test_list_servers_by_status(self):
        """测试按状态筛选服务器"""
        online_servers = self._run_async(list_servers(status="online"))
        self.assertEqual(len(online_servers), 3)
        self.assertTrue(all(server["status"] == "online" for server in online_servers))
        
        offline_servers = self._run_async(list_servers(status="offline"))
        self.assertEqual(len(offline_servers), 1)
        self.assertEqual(offline_servers[0]["status"], "offline")
        
        maintenance_servers = self._run_async(list_servers(status="maintenance"))
        self.assertEqual(len(maintenance_servers), 1)
        self.assertEqual(maintenance_servers[0]["status"], "maintenance")
    
    def test_list_servers_by_datacenter(self):
        """测试按数据中心筛选服务器"""
        beijing_servers = self._run_async(list_servers(datacenter="DC-Beijing"))
        self.assertEqual(len(beijing_servers), 3)
        self.assertTrue(all(server["datacenter"] == "DC-Beijing" for server in beijing_servers))
    
    def test_list_servers_by_resources(self):
        """测试按资源筛选服务器"""
        high_memory_servers = self._run_async(list_servers(min_memory_gb=128))
        self.assertEqual(len(high_memory_servers), 2)
        self.assertTrue(all(server["memory_gb"] >= 128 for server in high_memory_servers))
        
        high_cpu_servers = self._run_async(list_servers(min_cpu_cores=28))
        self.assertEqual(len(high_cpu_servers), 3)
        self.assertTrue(all(server["cpu_cores"] >= 28 for server in high_cpu_servers))
    
    def test_list_servers_combined_filters(self):
        """测试组合筛选条件"""
        servers = self._run_async(list_servers(
            status="online",
            datacenter="DC-Beijing",
            min_memory_gb=128
        ))
        self.assertEqual(len(servers), 2)
        self.assertTrue(all(
            server["status"] == "online" and 
            server["datacenter"] == "DC-Beijing" and 
            server["memory_gb"] >= 128 
            for server in servers
        ))
    
    def test_get_server_details_valid(self):
        """测试获取有效服务器详情"""
        details = self._run_async(get_server_details("server-001"))
        self.assertEqual(details["id"], "server-001")
        self.assertEqual(details["hostname"], "prod-server-001")
        self.assertIn("cpu", details)
        self.assertIn("memory_gb", details)
    
    def test_get_server_details_invalid(self):
        """测试获取无效服务器详情"""
        details = self._run_async(get_server_details("invalid-id"))
        self.assertIn("error", details)
        self.assertIn("available_ids", details)
        self.assertEqual(len(details["available_ids"]), 5)
    
    def test_get_cluster_summary(self):
        """测试获取集群概况"""
        summary = self._run_async(get_cluster_summary())
        
        self.assertEqual(summary["total_servers"], 5)
        self.assertEqual(summary["status_distribution"]["online"], 3)
        self.assertEqual(summary["status_distribution"]["offline"], 1)
        self.assertEqual(summary["status_distribution"]["maintenance"], 1)
        
        self.assertEqual(summary["datacenter_distribution"]["DC-Beijing"], 3)
        self.assertEqual(summary["datacenter_distribution"]["DC-Shanghai"], 1)
        self.assertEqual(summary["datacenter_distribution"]["DC-Shenzhen"], 1)
        
        self.assertEqual(summary["total_resources"]["cpu_cores"], 148)
        self.assertEqual(summary["total_resources"]["memory_gb"], 800)
        self.assertEqual(summary["total_resources"]["disk_tb"], 31)
        
        self.assertEqual(summary["online_servers"], 3)
        self.assertIsInstance(summary["average_load"], float)
        self.assertIn("last_update", summary)
    
    def test_check_server_health_online(self):
        """测试检查在线服务器健康状态"""
        health = self._run_async(check_server_health("server-001"))
        
        self.assertEqual(health["server_id"], "server-001")
        self.assertEqual(health["hostname"], "prod-server-001")
        self.assertEqual(health["overall_health"], "healthy")
        self.assertTrue(health["checks"]["connectivity"])
        self.assertEqual(health["checks"]["cpu_usage"], "normal")
        self.assertIn("timestamp", health)
    
    def test_check_server_health_maintenance(self):
        """测试检查维护中服务器健康状态"""
        health = self._run_async(check_server_health("server-004"))
        
        self.assertEqual(health["overall_health"], "unhealthy")
        self.assertFalse(health["checks"]["connectivity"])
        self.assertIn("maintenance_note", health)
    
    def test_check_server_health_offline(self):
        """测试检查离线服务器健康状态"""
        health = self._run_async(check_server_health("server-005"))
        
        self.assertEqual(health["overall_health"], "unhealthy")
        self.assertFalse(health["checks"]["connectivity"])
        self.assertIn("offline_reason", health)
    
    def test_check_server_health_invalid(self):
        """测试检查无效服务器健康状态"""
        health = self._run_async(check_server_health("invalid-id"))
        self.assertIn("error", health)


if __name__ == "__main__":
    unittest.main()