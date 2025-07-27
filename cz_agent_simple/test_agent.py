"""Agent 测试"""
import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import sys
from datetime import datetime

# Mock 必要的模块
langchain_mock = MagicMock()
langchain_mock.tools = MagicMock()
langchain_mock.agents = MagicMock()
langchain_mock.memory = MagicMock()
langchain_mock.schema = MagicMock()
langchain_mock.pydantic_v1 = MagicMock()

sys.modules['langchain'] = langchain_mock
sys.modules['langchain.tools'] = langchain_mock.tools
sys.modules['langchain.agents'] = langchain_mock.agents
sys.modules['langchain.memory'] = langchain_mock.memory
sys.modules['langchain.schema'] = langchain_mock.schema
sys.modules['langchain.pydantic_v1'] = langchain_mock.pydantic_v1
sys.modules['litellm'] = MagicMock()
sys.modules['langgraph'] = MagicMock()
sys.modules['langgraph.graph'] = MagicMock()

# Mock 类
class MockMemory:
    def __init__(self, **kwargs):
        self.chat_memory = MagicMock()
        self.chat_memory.add_user_message = MagicMock()
        self.chat_memory.add_ai_message = MagicMock()
        self.clear = MagicMock()  # 让 clear 成为一个 MagicMock，便于测试验证

sys.modules['langchain.memory'].ConversationBufferMemory = MockMemory

# 现在可以导入
from cz_agent_simple.agent import CZAgent


class TestCZAgent(unittest.TestCase):
    """测试 CZ Agent"""
    
    def setUp(self):
        """设置测试环境"""
        # Mock workflow
        self.mock_workflow = AsyncMock()
        self.mock_workflow.ainvoke = AsyncMock()
        
    @patch('cz_agent_simple.agent.create_workflow')
    def test_agent_initialization(self, mock_create_workflow):
        """测试 Agent 初始化"""
        mock_create_workflow.return_value = self.mock_workflow
        
        agent = CZAgent()
        
        # 验证初始化
        self.assertEqual(agent.model, "deepseek/deepseek-chat")
        self.assertIsNotNone(agent.workflow)
        self.assertIsNotNone(agent.memory)
        self.assertIsNotNone(agent.system_prompt)
        
        # 测试自定义模型
        agent2 = CZAgent(model="gpt-4")
        self.assertEqual(agent2.model, "gpt-4")
    
    @patch('cz_agent_simple.agent.create_workflow')
    def test_process_query_success(self, mock_create_workflow):
        """测试成功处理查询"""
        mock_create_workflow.return_value = self.mock_workflow
        
        async def run_test():
            # 准备 mock 响应
            self.mock_workflow.ainvoke.return_value = {
                "response": "找到 5 台在线服务器",
                "execution_time": 0.5
            }
            
            agent = CZAgent()
            result = await agent.process_query("查看所有在线服务器")
            
            # 验证调用
            self.mock_workflow.ainvoke.assert_called_once()
            call_args = self.mock_workflow.ainvoke.call_args[0][0]
            self.assertEqual(call_args["user_query"], "查看所有在线服务器")
            
            # 验证结果
            self.assertEqual(result, "找到 5 台在线服务器")
        
        asyncio.run(run_test())
    
    @patch('cz_agent_simple.agent.create_workflow')
    def test_process_query_error(self, mock_create_workflow):
        """测试处理查询时的错误处理"""
        mock_create_workflow.return_value = self.mock_workflow
        
        async def run_test():
            # 模拟错误
            self.mock_workflow.ainvoke.side_effect = Exception("连接超时")
            
            agent = CZAgent()
            result = await agent.process_query("查看服务器")
            
            # 验证错误处理
            self.assertIn("错误", result)
            self.assertIn("连接超时", result)
        
        asyncio.run(run_test())
    
    @patch('cz_agent_simple.agent.SimpleMemory')
    @patch('cz_agent_simple.agent.create_workflow')
    def test_chat_with_memory(self, mock_create_workflow, mock_simple_memory):
        """测试带记忆的对话"""
        mock_create_workflow.return_value = self.mock_workflow
        
        # 创建 mock memory 实例
        mock_memory_instance = MagicMock()
        mock_memory_instance.add_user_message = MagicMock()
        mock_memory_instance.add_ai_message = MagicMock()
        mock_memory_instance.chat_memory = mock_memory_instance
        mock_simple_memory.return_value = mock_memory_instance
        
        async def run_test():
            # 准备 mock 响应
            self.mock_workflow.ainvoke.return_value = {
                "response": "服务器 srv-001 状态正常"
            }
            
            agent = CZAgent()
            
            # 第一次对话
            response1 = await agent.chat("查看srv-001状态")
            self.assertEqual(response1, "服务器 srv-001 状态正常")
            
            # 验证记忆被更新
            mock_memory_instance.add_user_message.assert_called_with("查看srv-001状态")
            mock_memory_instance.add_ai_message.assert_called_with("服务器 srv-001 状态正常")
        
        asyncio.run(run_test())
    
    @patch('cz_agent_simple.agent.create_workflow')
    def test_clear_memory(self, mock_create_workflow):
        """测试清空记忆"""
        mock_create_workflow.return_value = self.mock_workflow
        
        agent = CZAgent()
        agent.memory.clear = MagicMock()
        
        agent.clear_memory()
        
        # 验证清空方法被调用
        agent.memory.clear.assert_called_once()
    
    @patch('cz_agent_simple.agent.create_workflow')
    def test_initial_state_structure(self, mock_create_workflow):
        """测试初始状态结构"""
        mock_create_workflow.return_value = self.mock_workflow
        
        async def run_test():
            self.mock_workflow.ainvoke.return_value = {"response": "OK"}
            
            agent = CZAgent()
            await agent.process_query("test query")
            
            # 获取传递给 workflow 的初始状态
            call_args = self.mock_workflow.ainvoke.call_args[0][0]
            
            # 验证所有必需的字段都存在
            required_fields = [
                "user_query", "query_analysis", "server_info",
                "topology_info", "switch_info", "installation_logs",
                "rack_servers", "affected_servers", "diagnosis",
                "response", "execution_history", "error",
                "timestamp", "execution_time"
            ]
            
            for field in required_fields:
                self.assertIn(field, call_args)
            
            # 验证初始值
            self.assertEqual(call_args["user_query"], "test query")
            self.assertIsNone(call_args["query_analysis"])
            self.assertEqual(call_args["execution_history"], [])
            self.assertIsInstance(call_args["timestamp"], datetime)
        
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()