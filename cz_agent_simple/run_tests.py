"""运行所有测试的脚本"""
import sys
import os
import unittest

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 需要先设置mock，因为某些模块会在导入时使用这些包
from unittest.mock import MagicMock

# Mock 外部依赖
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
sys.modules['mcp'] = MagicMock()
sys.modules['mcp.server'] = MagicMock()
sys.modules['mcp.server.fastmcp'] = MagicMock()

# 创建 mock 的 tool 装饰器
def mock_tool(name, args_schema=None):
    def decorator(func):
        func.name = name
        func.args_schema = args_schema
        func.description = func.__doc__
        func.afunc = func
        return func
    return decorator

langchain_mock.tools.tool = mock_tool

# 创建 StateGraph 和 END
class MockStateGraph:
    def __init__(self, state_type):
        self.state_type = state_type
        self.nodes = {}
        self.edges = []
        self.conditional_edges = []
        self.entry_point = None
    
    def add_node(self, name, func):
        self.nodes[name] = func
    
    def add_edge(self, from_node, to_node):
        self.edges.append((from_node, to_node))
    
    def add_conditional_edges(self, from_node, condition, branches):
        self.conditional_edges.append((from_node, condition, branches))
    
    def set_entry_point(self, node):
        self.entry_point = node
    
    def compile(self):
        return self
    
    async def ainvoke(self, state):
        return state

sys.modules['langgraph.graph'].StateGraph = MockStateGraph
sys.modules['langgraph.graph'].END = "END"

# Mock FastMCP
class MockFastMCP:
    def __init__(self, name):
        self.name = name
    
    def tool(self):
        def decorator(func):
            return func
        return decorator
    
    def run(self):
        pass

sys.modules['mcp.server.fastmcp'].FastMCP = MockFastMCP

# 现在导入测试模块
from cz_agent_simple import test_models
from cz_agent_simple import test_state
from cz_agent_simple import test_mcp_client
from cz_agent_simple import test_tools
from cz_agent_simple import test_workflow
from cz_agent_simple import test_mock_mcp_server
from cz_agent_simple import test_agent
from cz_agent_simple import test_demo

if __name__ == '__main__':
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试模块
    test_modules = [
        test_models,
        test_state,
        test_mcp_client,
        test_tools,
        test_workflow,
        test_mock_mcp_server,
        test_agent,
        test_demo
    ]
    
    for module in test_modules:
        suite.addTests(loader.loadTestsFromModule(module))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回状态码
    sys.exit(0 if result.wasSuccessful() else 1)