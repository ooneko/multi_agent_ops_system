"""
MCP Agent Demo - 展示 Google ADK 回调机制的完整示例

本示例演示了如何在 MCP Agent 中实现 6 个回调点位，用于：
1. 控制 Agent 生命周期
2. 过滤和验证模型输入输出
3. 实施工具级别的安全策略

学习要点：
- 回调函数的正确签名和返回值
- 如何使用包装器模式集成回调
- 安全过滤的最佳实践
- 日志记录和错误处理

作者：MCP Agent 示例
版本：1.0
"""

import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.genai import types
import logging
from typing import Any, Dict, List

# 加载环境变量
load_dotenv()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 定义工作目录为代码运行目录
WORKSPACE_PATH = os.path.abspath(os.getcwd())


# ========== 回调函数实现 ==========
# 这些回调函数展示了 Google ADK 的回调机制
# 回调允许我们在 Agent 执行的关键点插入自定义逻辑


# ========== 1. Agent 生命周期回调 ==========
# 这些回调控制 Agent 的整体执行流程


def before_agent_callback(agent_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    在 Agent 开始执行任何逻辑之前调用。

    用途：
    - 验证配置参数
    - 注入额外的上下文信息
    - 记录 Agent 启动事件

    Args:
        agent_name: Agent 的名称
        config: Agent 的配置字典

    Returns:
        修改后的配置字典（或原样返回）
    """
    logger.info(f"🚀 [BEFORE_AGENT] '{agent_name}' 准备开始执行")
    logger.info(f"📋 配置信息: {config}")

    # 示例：可以在这里添加额外的配置
    # config['max_retries'] = 3
    # config['timeout'] = 30

    return config


def after_agent_callback(agent_name: str, result: Any) -> Any:
    """
    在 Agent 完成所有逻辑执行后调用。

    用途：
    - 记录执行结果
    - 清理资源
    - 发送通知或指标

    Args:
        agent_name: Agent 的名称
        result: Agent 的执行结果

    Returns:
        处理后的结果（或原样返回）
    """
    logger.info(f"✅ [AFTER_AGENT] '{agent_name}' 执行完成")
    return result


# ========== 2. 模型交互回调 ==========
# 这些回调在与 LLM 交互时触发，是最常用的回调类型


def before_model_callback(
    messages: List[Dict[str, str]], model_name: str
) -> List[Dict[str, str]]:
    """
    在将消息发送给语言模型之前调用。
    这是实现输入过滤和安全检查的最佳位置。

    用途：
    - 🛡️ 安全过滤：拦截危险命令
    - 📝 内容审查：过滤敏感信息
    - 🔄 消息转换：修改或增强输入
    - 📊 记录分析：跟踪用户请求

    Args:
        messages: 要发送给模型的消息列表
        model_name: 目标模型的名称

    Returns:
        过滤/修改后的消息列表
    """
    logger.info(f"🔍 [BEFORE_MODEL] 准备调用模型 '{model_name}'")
    logger.info(f"📨 收到 {len(messages)} 条消息")

    # 创建消息副本，避免修改原始数据
    filtered_messages = []

    # 定义危险命令模式
    dangerous_patterns = [
        "rm -rf",  # 递归删除
        "format",  # 格式化磁盘
        "delete",  # 删除操作
        "drop database",  # 删除数据库
        "truncate",  # 清空表
        "sudo rm",  # 管理员删除
    ]

    for msg in messages:
        msg_copy = msg.copy()
        content = msg_copy.get("content", "")

        # 安全检查：扫描危险命令
        if any(danger in content.lower() for danger in dangerous_patterns):
            logger.warning(f"⚠️ 检测到危险命令: {content}")
            # 替换为安全提示
            msg_copy["content"] = (
                "🛑 您的请求包含潜在危险操作，已被安全策略拦截。\n"
                "如果您确实需要执行此操作，请联系管理员。"
            )

        filtered_messages.append(msg_copy)

    # 可以在这里添加更多过滤逻辑
    # 例如：敏感信息脱敏、关键词替换等

    return filtered_messages


def after_model_callback(event: Any, model_name: str) -> Any:
    """
    在接收到模型响应之后调用。
    可以用来过滤、修改或增强模型的输出。

    用途：
    - 🔍 内容审查：过滤不当内容
    - ➕ 响应增强：添加额外信息
    - 📊 质量控制：检查响应质量
    - 📝 日志记录：记录模型行为

    Args:
        event: 模型返回的事件对象
        model_name: 模型名称

    Returns:
        处理后的事件对象
    """
    logger.info(f"📥 [AFTER_MODEL] 收到 '{model_name}' 的响应")

    # 只处理最终响应（不处理中间流式事件）
    if hasattr(event, "is_final_response") and event.is_final_response():
        if hasattr(event, "content") and event.content and event.content.parts:
            original_text = event.content.parts[0].text
            logger.info(f"📏 响应长度: {len(original_text)} 字符")

            # 示例 1：为特定类型的响应添加安全提示
            if "执行完成" in original_text or "命令已执行" in original_text:
                event.content.parts[0].text = (
                    original_text + "\n\n⚠️ 安全提示：以上操作已经过安全审核。"
                )

            # 示例 2：添加时间戳
            # event.content.parts[0].text += f"\n\n[响应时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"

            # 示例 3：敏感信息脱敏（如果响应包含密码、密钥等）
            # if "password" in original_text.lower():
            #     event.content.parts[0].text = "[敏感信息已隐藏]"

    return event


# ========== 3. 工具执行回调 ==========
# 这些回调在调用外部工具（如文件操作、命令执行）时触发


def before_tool_callback(tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """
    在执行工具调用之前触发。
    这是实施工具级别安全策略的关键点。

    用途：
    - 🛡️ 参数验证：确保参数安全有效
    - 🔐 权限检查：验证是否有权限执行
    - 📝 审计日志：记录所有工具调用
    - 🚫 操作拦截：阻止危险操作

    Args:
        tool_name: 工具名称（如 'start_process', 'read_file'）
        tool_args: 工具参数字典

    Returns:
        验证后的参数（可以修改）

    Raises:
        ValueError: 当检测到危险操作时
    """
    logger.info(f"🔧 [BEFORE_TOOL] 准备调用工具 '{tool_name}'")
    logger.info(f"📋 参数: {tool_args}")

    # 针对不同工具的安全策略
    if tool_name == "start_process":
        command = tool_args.get("command", "")

        # 定义危险命令模式（更详细的黑名单）
        dangerous_patterns = [
            "rm -rf /",  # 删除根目录
            "format c:",  # 格式化 C 盘
            "del /f /s /q",  # Windows 强制删除
            ":(){ :|:& };:",  # Fork 炸弹
            "dd if=/dev/zero",  # 磁盘擦除
            "mkfs",  # 创建文件系统
            "> /dev/sda",  # 覆写磁盘
        ]

        # 检查每个危险模式
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                logger.error(f"🚫 阻止危险命令: {command}")
                raise ValueError(
                    f"安全策略禁止执行该命令！\n"
                    f"检测到危险模式: '{pattern}'\n"
                    f"如需执行，请联系管理员。"
                )

        # 可以添加更多检查，如路径验证、参数长度限制等
        logger.info(f"✅ 命令通过安全检查: {command}")

    elif tool_name == "write_file":
        # 检查文件路径，防止覆盖系统文件
        file_path = tool_args.get("path", "")
        if file_path.startswith("/etc/") or file_path.startswith("/sys/"):
            raise ValueError("禁止写入系统目录")

    return tool_args


def after_tool_callback(tool_name: str, tool_result: Any) -> Any:
    """
    在工具执行完成后调用。
    可以处理、过滤或增强工具的输出。

    用途：
    - 📊 结果验证：检查执行是否成功
    - 🔍 输出过滤：隐藏敏感信息
    - 📝 执行记录：记录工具执行结果
    - 🔄 错误处理：统一错误格式

    Args:
        tool_name: 执行的工具名称
        tool_result: 工具返回的结果

    Returns:
        处理后的结果
    """
    logger.info(f"✅ [AFTER_TOOL] 工具 '{tool_name}' 执行完成")

    # 处理不同类型的结果
    if isinstance(tool_result, dict):
        # 错误处理
        if tool_result.get("error"):
            error_msg = tool_result["error"]
            logger.error(f"❌ 工具执行失败: {error_msg}")

            # 可以在这里统一错误格式或添加更友好的错误信息
            tool_result["user_friendly_error"] = f"操作失败：{error_msg}"

        # 成功结果处理
        else:
            # 记录结果（智能截断）
            result_str = str(tool_result)
            if len(result_str) > 200:
                logger.info(f"📄 结果预览: {result_str[:200]}...")
                logger.info(f"📏 （完整结果长度: {len(result_str)} 字符）")
            else:
                logger.info(f"📄 完整结果: {result_str}")

            # 示例：为某些工具添加执行统计
            if tool_name == "start_process" and "output" in tool_result:
                lines = tool_result["output"].count("\n")
                tool_result["stats"] = {"output_lines": lines}

    return tool_result


# ========== 工具包装器 - 添加回调支持 ==========
class CallbackMCPToolset:
    """
    支持回调的 MCPToolset 包装器

    这个包装器拦截所有工具调用，在执行前后触发回调。
    支持：
    - before_tool: 验证参数、权限检查、阻止危险操作
    - after_tool: 处理结果、记录日志、错误处理
    """

    def __init__(self, original_toolset):
        self.toolset = original_toolset
        # 保留原始工具集的所有属性
        self.__dict__.update(original_toolset.__dict__)

    def __getattr__(self, name):
        """代理所有未定义的属性到原始工具集"""
        return getattr(self.toolset, name)

    async def __call__(self, *args, **kwargs):
        """处理工具调用 - 这是 ADK 调用工具的入口"""
        # 从参数中提取工具信息
        tool_name = kwargs.get("tool_name", "unknown")
        tool_args = kwargs.get("arguments", {})

        # ========== 1. 调用 before_tool 回调 ==========
        try:
            processed_args = before_tool_callback(tool_name, tool_args)

            # 如果返回 None，正常执行工具
            if processed_args is None:
                processed_args = tool_args

            # 如果返回的是结果字典（而非参数），则跳过工具执行
            if isinstance(processed_args, dict) and "skip_execution" in processed_args:
                logger.info(f"⏭️ 工具 '{tool_name}' 执行被回调跳过")
                return processed_args.get("result", {"output": "操作已被安全策略阻止"})

            # 更新参数
            kwargs["arguments"] = processed_args

        except ValueError as e:
            # 安全策略拒绝执行
            logger.error(f"🚫 工具执行被拒绝: {e}")
            return {"error": str(e), "blocked": True}
        except Exception as e:
            logger.error(f"❌ before_tool 回调出错: {e}")
            # 继续执行，但记录错误

        # ========== 2. 执行原始工具 ==========
        try:
            result = await self.toolset(*args, **kwargs)
        except Exception as e:
            result = {"error": str(e), "exception": True}
            logger.error(f"❌ 工具执行失败: {e}")

        # ========== 3. 调用 after_tool 回调 ==========
        try:
            processed_result = after_tool_callback(tool_name, result)
            return processed_result
        except Exception as e:
            logger.error(f"❌ after_tool 回调出错: {e}")
            # 返回原始结果
            return result


# 创建原始工具集
mcp_toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command="npx",
        args=[
            "-y",  # 自动确认安装
            "@wonderwhy-er/desktop-commander",
        ],
        env={
            "DESKTOP_COMMANDER_WORKSPACE": WORKSPACE_PATH,
        },
    ),
    # 可选：根据需要过滤工具
    # tool_filter=['start_process', 'read_file',
    #              'write_file', 'search_files']
)

# 使用回调包装器包装工具集
callback_toolset = CallbackMCPToolset(mcp_toolset)

# 创建 Agent 并注册回调
root_agent = Agent(
    model=LiteLlm(model="deepseek/deepseek-chat"),
    name="mcp_agent_demo",
    instruction="""你是一个专业的命令执行助手，拥有强大的系统命令执行能力。

你可以直接执行各种命令和脚本，包括但不限于：
- Shell 命令：ls、pwd、cd、echo、grep、find 等
- 系统信息：date、uptime、df、ps、top 等
- 文件操作：cat、touch、mkdir、rm、cp、mv 等
- 脚本执行：.sh、.py、.js 脚本文件
- 网络命令：ping、curl、wget 等
- SSH 远程执行命令

工作方式：
1. 理解用户需求，自动选择合适的命令
2. 直接执行命令，无需用户确认
3. 清晰展示命令执行结果

示例场景：
- 用户："现在几点了？" → 你执行 date 命令
- 用户："看看当前目录" → 你执行 pwd 和 ls 命令
- 用户："检查磁盘空间" → 你执行 df -h 命令
- 用户："运行测试脚本" → 你执行相应的脚本文件

注意事项：
- 执行命令前简要说明其作用
- 显示命令的输出结果
- 对于危险命令给出警告
- 使用简洁的中文回复
- 完成任务后直接结束，不要添加额外的提示语
""",
    tools=[callback_toolset],  # 使用包装后的工具集
)


# Agent 已创建，但需要自定义回调处理
# 由于 ADK 可能还不支持直接的回调注册，我们使用包装器模式


async def call_agent(query: str, runner, user_id: str, session_id: str):
    """向 MCP Agent 发送查询并获取响应"""
    print(f"\n🐠 >>> 用户查询: {query}")

    # 准备用户消息
    content = types.Content(role="user", parts=[types.Part(text=query)])

    final_response = "Agent 没有产生响应。"

    # 执行 agent 并处理事件流
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        # 获取最终响应
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response = f"Agent 报错: {event.error_message or '未知错误'}"
            break

    print(f"🐠 <<< Agent 响应:\n{final_response}")
    return final_response


async def main():
    """
    主函数 - 演示带回调的 MCP Agent

    这个示例展示了：
    1. 如何创建支持回调的 Agent
    2. 回调如何在运行时自动触发
    3. 安全过滤如何保护系统
    """
    print("\n🐠 ===== MCP Agent 回调示例 =====")
    print(f"🐠 工作目录: {WORKSPACE_PATH}")
    print("\n📚 学习要点：")
    print("  1. before_model_callback 会拦截危险命令")
    print("  2. after_model_callback 会增强响应")
    print("  3. 工具回调提供额外的安全层")
    print("\n" + "=" * 50)

    # 创建会话服务
    session_service = InMemorySessionService()

    # 定义应用和用户标识
    app_name = "mcp_agent_demo"
    user_id = "user_1"
    session_id = "session_001"

    # 创建会话
    await session_service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )

    # 创建基础 Runner
    base_runner = Runner(
        agent=root_agent, app_name=app_name, session_service=session_service
    )

    # 创建带回调的 Runner 包装器
    class MCPCallbackRunner:
        """
        支持回调的 MCP Runner 包装器

        这个包装器在 Agent 执行的各个阶段插入回调：
        - before_agent: 在开始处理请求前
        - after_agent: 在完成所有处理后
        - before_model: 在调用 LLM 前
        - after_model: 在收到 LLM 响应后
        """

        def __init__(self, runner):
            self.runner = runner
            self.model_name = "deepseek/deepseek-chat"
            self.agent_name = "mcp_agent_demo"

        async def run_async(self, user_id: str, session_id: str, new_message):
            # ========== 1. 调用 before_agent 回调 ==========
            # 准备 Agent 配置信息
            agent_config = {
                "name": self.agent_name,
                "model": self.model_name,
                "user_id": user_id,
                "session_id": session_id,
                "message": new_message.parts[0].text if new_message.parts else "",
            }

            # 调用 before_agent 回调
            updated_config = before_agent_callback(self.agent_name, agent_config)

            # 可以使用更新后的配置（例如，检查是否需要特殊处理）
            if updated_config.get("skip_safety_check", False):
                logger.info("🔓 根据配置跳过安全检查")

            # ========== 2. 准备消息并调用 before_model 回调 ==========
            messages = [
                {
                    "role": new_message.role,
                    "content": new_message.parts[0].text if new_message.parts else "",
                }
            ]

            # 调用 before_model 回调进行安全过滤
            filtered_messages = before_model_callback(messages, self.model_name)

            # 如果消息被修改，更新输入
            if filtered_messages[0]["content"] != messages[0]["content"]:
                new_message = types.Content(
                    role=filtered_messages[0]["role"],
                    parts=[types.Part(text=filtered_messages[0]["content"])],
                )

            # ========== 3. 执行主要逻辑 ==========
            final_result = None

            # 调用原始 runner
            async for event in self.runner.run_async(
                user_id=user_id, session_id=session_id, new_message=new_message
            ):
                # 应用 after_model 回调（仅在最终响应时）
                if event.is_final_response():
                    # 记录最终结果用于 after_agent 回调
                    final_result = event

                    if event.content and event.content.parts:
                        # 调用 after_model 回调
                        event = after_model_callback(event, self.model_name)

                yield event

            # ========== 4. 调用 after_agent 回调 ==========
            if final_result:
                # 准备结果信息
                agent_result = {
                    "success": True,
                    "response": (
                        final_result.content.parts[0].text
                        if final_result.content and final_result.content.parts
                        else ""
                    ),
                    "user_id": user_id,
                    "session_id": session_id,
                }

                # 调用 after_agent 回调
                after_agent_callback(self.agent_name, agent_result)

    # 使用包装的 runner
    runner = MCPCallbackRunner(base_runner)

    print(
        f"🐠 会话已创建: App='{app_name}', " f"User='{user_id}', Session='{session_id}'"
    )
    print("🐠 已启用回调点位：")
    print("   - before_agent: 在 Agent 执行前（✅ 已实现）")
    print("   - after_agent: 在 Agent 执行后（✅ 已实现）")
    print("   - before_model: 在调用模型前（✅ 已实现，含安全过滤）")
    print("   - after_model: 在模型响应后（✅ 已实现）")
    print("   - before_tool: 在工具调用前（✅ 已实现，含参数验证）")
    print("   - after_tool: 在工具调用后（✅ 已实现，含结果处理）")

    # 示例交互 - 展示命令执行功能和安全拦截
    example_queries = [
        "我想知道现在在哪个目录下工作",
        "帮我看看当前目录有哪些文件，要详细信息",
        "检查一下系统安装的 Python 是什么版本",
        "现在几点了？",
        "请执行 rm -rf /tmp/test（测试危险命令拦截）",
    ]

    print("\n🐠 开始示例交互...")
    for query in example_queries:
        await call_agent(query, runner, user_id, session_id)
        print("\n" + "-" * 60 + "\n")

    print("🐠 示例交互完成！")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
