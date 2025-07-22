"""
Shell MCP Agent 测试文件
"""

import unittest
import asyncio
from unittest.mock import Mock


class TestShellAgent(unittest.TestCase):
    """Shell Agent 单元测试"""

    def test_agent_initialization(self):
        """测试 agent 初始化"""
        # 由于可能缺少依赖，使用 try-except
        try:
            from agent import shell_agent

            self.assertIsNotNone(shell_agent)
            self.assertEqual(shell_agent.name, "shell_assistant_agent")
            self.assertGreater(len(shell_agent.tools), 0)
        except ImportError:
            self.skipTest("缺少必要的依赖")

    def test_agent_instruction(self):
        """测试 agent 指令设置"""
        try:
            from agent import shell_agent

            self.assertIn("系统管理助手", shell_agent.instruction)
            self.assertIn("shell 命令", shell_agent.instruction)
        except ImportError:
            self.skipTest("缺少必要的依赖")

    def test_call_shell_agent_basic(self):
        """测试基本的 shell agent 调用"""
        try:
            from agent import call_shell_agent

            # 创建模拟的 runner
            mock_runner = Mock()

            # 创建模拟的事件
            mock_event = Mock()
            mock_event.is_final_response.return_value = True
            mock_event.content = Mock()
            mock_event.content.parts = [Mock(text="命令执行成功")]
            mock_event.actions = None

            # 设置异步生成器
            async def mock_run_async(*args, **kwargs):
                yield mock_event

            mock_runner.run_async = mock_run_async

            # 调用函数
            async def run_test():
                result = await call_shell_agent(
                    "测试命令", mock_runner, "test_user", "test_session"
                )
                self.assertEqual(result, "命令执行成功")

            asyncio.run(run_test())
        except ImportError:
            self.skipTest("缺少必要的依赖")

    def test_call_shell_agent_error(self):
        """测试 shell agent 错误处理"""
        try:
            from agent import call_shell_agent

            # 创建模拟的 runner
            mock_runner = Mock()

            # 创建模拟的错误事件
            mock_event = Mock()
            mock_event.is_final_response.return_value = True
            mock_event.content = None
            mock_event.actions = Mock()
            mock_event.actions.escalate = True
            mock_event.error_message = "测试错误"

            # 设置异步生成器
            async def mock_run_async(*args, **kwargs):
                yield mock_event

            mock_runner.run_async = mock_run_async

            # 调用函数
            async def run_test():
                result = await call_shell_agent(
                    "错误命令", mock_runner, "test_user", "test_session"
                )
                self.assertIn("Agent 报错", result)
                self.assertIn("测试错误", result)

            asyncio.run(run_test())
        except ImportError:
            self.skipTest("缺少必要的依赖")

    def test_workspace_path(self):
        """测试工作空间路径设置"""
        try:
            from agent import WORKSPACE_PATH
            import os

            # 确保路径是绝对路径
            self.assertTrue(os.path.isabs(WORKSPACE_PATH))
            # 确保路径存在或可以创建
            self.assertTrue(WORKSPACE_PATH.endswith("Code"))
        except ImportError:
            self.skipTest("缺少必要的依赖")


if __name__ == "__main__":
    unittest.main()
