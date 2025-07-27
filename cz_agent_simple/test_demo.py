"""Demo 脚本测试"""
import unittest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import sys
import io

# Mock 必要的模块
sys.modules['langchain'] = MagicMock()
sys.modules['langchain.tools'] = MagicMock()
sys.modules['langchain.agents'] = MagicMock()
sys.modules['langchain.memory'] = MagicMock()
sys.modules['langchain.schema'] = MagicMock()
sys.modules['langchain.pydantic_v1'] = MagicMock()
sys.modules['litellm'] = MagicMock()
sys.modules['langgraph'] = MagicMock()
sys.modules['langgraph.graph'] = MagicMock()

from cz_agent_simple.demo import (
    demo_basic_queries,
    demo_fault_diagnosis,
    demo_rack_analysis,
    demo_conversation
)


class TestDemo(unittest.TestCase):
    """测试演示脚本"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_agent = MagicMock()
        self.mock_agent.process_query = AsyncMock()
        self.mock_agent.chat = AsyncMock()
        self.mock_agent.clear_memory = MagicMock()
    
    @patch('cz_agent_simple.demo.CZAgent')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_demo_basic_queries(self, mock_stdout, mock_cz_agent):
        """测试基本查询演示"""
        mock_cz_agent.return_value = self.mock_agent
        self.mock_agent.process_query.side_effect = [
            "找到 10 台在线服务器",
            "服务器 srv-0001 状态正常",
            "网络拓扑信息"
        ]
        
        async def run_test():
            await demo_basic_queries()
            
            # 验证调用次数
            self.assertEqual(self.mock_agent.process_query.call_count, 3)
            
            # 验证输出包含预期内容
            output = mock_stdout.getvalue()
            self.assertIn("基本查询演示", output)
            self.assertIn("找到 10 台在线服务器", output)
        
        asyncio.run(run_test())
    
    @patch('cz_agent_simple.demo.CZAgent')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_demo_fault_diagnosis(self, mock_stdout, mock_cz_agent):
        """测试故障诊断演示"""
        mock_cz_agent.return_value = self.mock_agent
        self.mock_agent.process_query.side_effect = [
            "找到 2 台安装失败的服务器",
            "故障原因：网络配置错误",
            "安装日志详情"
        ]
        
        async def run_test():
            await demo_fault_diagnosis()
            
            # 验证调用
            self.assertEqual(self.mock_agent.process_query.call_count, 3)
            
            # 验证查询内容
            calls = self.mock_agent.process_query.call_args_list
            self.assertIn("安装失败", calls[0][0][0])
            self.assertIn("srv-0020", calls[1][0][0])
        
        asyncio.run(run_test())
    
    @patch('cz_agent_simple.demo.CZAgent')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_demo_rack_analysis(self, mock_stdout, mock_cz_agent):
        """测试机柜分析演示"""
        mock_cz_agent.return_value = self.mock_agent
        self.mock_agent.process_query.return_value = "机柜网络状态分析结果"
        
        async def run_test():
            await demo_rack_analysis()
            
            # 验证调用
            self.mock_agent.process_query.assert_called_once()
            call_args = self.mock_agent.process_query.call_args[0][0]
            self.assertIn("rack-A02", call_args)
        
        asyncio.run(run_test())
    
    @patch('cz_agent_simple.demo.CZAgent')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_demo_conversation(self, mock_stdout, mock_cz_agent):
        """测试对话演示"""
        mock_cz_agent.return_value = self.mock_agent
        self.mock_agent.chat.side_effect = [
            "发现 3 台故障服务器",
            "srv-001 的详细信息"
        ]
        
        async def run_test():
            await demo_conversation()
            
            # 验证chat被调用两次
            self.assertEqual(self.mock_agent.chat.call_count, 2)
            
            # 验证记忆被清空
            self.mock_agent.clear_memory.assert_called_once()
            
            # 验证输出
            output = mock_stdout.getvalue()
            self.assertIn("对话演示", output)
            self.assertIn("记忆已清空", output)
        
        asyncio.run(run_test())
    
    def test_imports(self):
        """测试导入是否正确"""
        # 这个测试主要是确保demo.py可以被导入
        import cz_agent_simple.demo as demo_module
        self.assertTrue(hasattr(demo_module, 'main'))
        self.assertTrue(hasattr(demo_module, 'demo_basic_queries'))
        self.assertTrue(hasattr(demo_module, 'demo_fault_diagnosis'))
        self.assertTrue(hasattr(demo_module, 'demo_rack_analysis'))
        self.assertTrue(hasattr(demo_module, 'demo_conversation'))


if __name__ == "__main__":
    unittest.main()