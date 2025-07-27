"""测试运行器的测试"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# 添加当前目录到 Python 路径，以便可以导入 run_tests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入 run_tests 以确保所有 mock 设置都已完成
import run_tests


class TestRunTests(unittest.TestCase):
    """测试 run_tests.py 脚本"""
    
    def test_mock_modules_setup(self):
        """测试模块 mock 设置"""
        # 验证必要的模块已被 mock
        self.assertIn('langchain', sys.modules)
        self.assertIn('langchain.tools', sys.modules)
        self.assertIn('litellm', sys.modules)
        self.assertIn('langgraph', sys.modules)
        self.assertIn('mcp', sys.modules)
    
    def test_mock_tool_decorator(self):
        """测试 langchain.tools 模块已被正确 mock"""
        # 验证 langchain.tools 模块已被 mock
        self.assertIn('langchain.tools', sys.modules)
        
        # 验证可以导入 tool 装饰器
        from langchain.tools import tool
        
        # 验证 tool 是可调用的（即使是 MagicMock）
        self.assertTrue(callable(tool))
        
        # 测试使用 tool 装饰器不会抛出异常
        @tool("test_tool", args_schema=None)
        def test_func():
            """Test function"""
            return "test"
        
        # 验证函数仍然可以被调用（MagicMock 会返回另一个 MagicMock）
        result = test_func()
        # 测试没有抛出异常即表示 mock 设置成功
    
    def test_mock_state_graph(self):
        """测试 langgraph 模块已被正确 mock"""
        # 验证 langgraph.graph 模块已被 mock
        self.assertIn('langgraph.graph', sys.modules)
        
        # 验证可以导入并使用 StateGraph 和 END
        from langgraph.graph import StateGraph, END
        
        # 验证 StateGraph 可以被实例化（即使是 MagicMock）
        graph = StateGraph(dict)
        
        # 验证基本方法存在并可调用
        # MagicMock 会自动创建这些属性，所以它们总是存在的
        graph.add_node("test", lambda x: x)
        graph.add_edge("test", "end")
        graph.set_entry_point("test")
        graph.compile()
        
        # 测试没有抛出异常即表示 mock 设置成功
    
    def test_mock_fast_mcp(self):
        """测试 MockFastMCP"""
        # 验证 mcp.server.fastmcp.FastMCP 已被 mock
        from mcp.server.fastmcp import FastMCP
        
        mcp = FastMCP("test_server")
        self.assertEqual(mcp.name, "test_server")
        
        # 测试 tool 装饰器
        @mcp.tool()
        def test_tool():
            return "test"
        
        # 应该返回原函数
        self.assertEqual(test_tool(), "test")
        
        # 测试 run 方法
        mcp.run()  # 不应该抛出异常
    
    def test_imports(self):
        """测试是否可以导入所有测试模块"""
        try:
            from cz_agent_simple import test_models
            from cz_agent_simple import test_state
            from cz_agent_simple import test_mcp_client
            from cz_agent_simple import test_tools
            from cz_agent_simple import test_workflow
            from cz_agent_simple import test_mock_mcp_server
            from cz_agent_simple import test_agent
            from cz_agent_simple import test_demo
            
            # 如果所有导入都成功，测试通过
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import test module: {e}")


if __name__ == "__main__":
    unittest.main()