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
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.lite_llm import LiteLlm
from google.adk.models import LlmRequest, LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from google.genai import types
import logging
from typing import Any, Dict, List, Optional
from copy import deepcopy

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


def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    在 Agent 开始执行任何逻辑之前调用。

    用途：
    - 验证配置参数
    - 注入额外的上下文信息
    - 记录 Agent 启动事件
    - 根据状态条件跳过 Agent 执行

    Args:
        callback_context: 包含 agent_name、invocation_id、state 等信息

    Returns:
        - None: 继续正常执行
        - types.Content: 跳过 Agent 执行并返回此内容
    """
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    current_state = callback_context.state.to_dict() if callback_context.state else {}

    logger.info(f"🚀 [BEFORE_AGENT] '{agent_name}' 准备开始执行 (Inv: {invocation_id})")
    logger.info(f"📋 当前状态: {current_state}")

    # 示例：根据状态决定是否跳过执行
    if current_state.get("skip_agent", False):
        logger.warning(f"⏭️ 根据状态条件跳过 Agent '{agent_name}' 的执行")
        return types.Content(
            parts=[types.Part(text=f"Agent {agent_name} 被 before_agent_callback 跳过")],
            role="model"
        )

    # 返回 None 以继续正常执行
    return None


def after_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    在 Agent 完成所有逻辑执行后调用。

    用途：
    - 记录执行结果
    - 清理资源
    - 发送通知或指标
    - 根据状态修改或替换输出

    Args:
        callback_context: 包含 agent_name、invocation_id、state 等信息

    Returns:
        - None: 使用 Agent 的原始输出
        - types.Content: 替换 Agent 的输出
    """
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    current_state = callback_context.state.to_dict() if callback_context.state else {}

    logger.info(f"✅ [AFTER_AGENT] '{agent_name}' 执行完成 (Inv: {invocation_id})")
    logger.info(f"📋 最终状态: {current_state}")

    # 示例：根据状态决定是否添加额外信息
    if current_state.get("add_safety_note", False):
        logger.info(f"📝 为 Agent '{agent_name}' 的输出添加安全提示")
        return types.Content(
            parts=[types.Part(text="✅ 操作已完成。\n\n⚠️ 安全提示：以上操作已经过安全审核。")],
            role="model"
        )

    # 返回 None 以使用原始输出
    return None


# ========== 2. 模型交互回调 ==========
# 这些回调在与 LLM 交互时触发，是最常用的回调类型


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    在将消息发送给语言模型之前调用。
    这是实现输入过滤和安全检查的最佳位置。

    用途：
    - 🛡️ 安全过滤：拦截危险命令
    - 📝 内容审查：过滤敏感信息
    - 🔄 消息转换：修改或增强输入
    - 📊 记录分析：跟踪用户请求

    Args:
        callback_context: 包含 agent_name 等上下文信息
        llm_request: 包含要发送给模型的请求

    Returns:
        - None: 继续使用（可能已修改的）请求
        - LlmResponse: 跳过 LLM 调用并返回此响应
    """
    agent_name = callback_context.agent_name
    logger.info(f"🔍 [BEFORE_MODEL] 准备调用模型，Agent: '{agent_name}'")

    # 检查最后一条用户消息
    last_user_message = ""
    if llm_request.contents and llm_request.contents[-1].role == 'user':
        if llm_request.contents[-1].parts:
            last_user_message = llm_request.contents[-1].parts[0].text
    
    if last_user_message:
        logger.info(f"📨 检查用户消息: '{last_user_message[:100]}...'")

    # 定义危险命令模式
    dangerous_patterns = [
        "rm -rf",  # 递归删除
        "format",  # 格式化磁盘
        "delete",  # 删除操作
        "drop database",  # 删除数据库
        "truncate",  # 清空表
        "sudo rm",  # 管理员删除
    ]

    # 安全检查：扫描危险命令
    if last_user_message and any(danger in last_user_message.lower() for danger in dangerous_patterns):
        logger.warning(f"⚠️ 检测到危险命令，阻止 LLM 调用")
        # 返回安全响应，跳过 LLM 调用
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=(
                    "🛑 您的请求包含潜在危险操作，已被安全策略拦截。\n"
                    "如果您确实需要执行此操作，请联系管理员。"
                ))]
            )
        )

    # 修改系统指令（如需要）
    if llm_request.config.system_instruction:
        original_instruction = llm_request.config.system_instruction
        if isinstance(original_instruction, types.Content) and original_instruction.parts:
            # 添加安全提醒到系统指令
            original_text = original_instruction.parts[0].text or ""
            original_instruction.parts[0].text = original_text + "\n\n⚠️ 安全提醒：请遵守所有安全规定。"
            logger.info("📝 已在系统指令中添加安全提醒")

    # 返回 None 以继续处理（可能已修改的）请求
    return None


def after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    在接收到模型响应之后调用。
    可以用来过滤、修改或增强模型的输出。

    用途：
    - 🔍 内容审查：过滤不当内容
    - ➕ 响应增强：添加额外信息
    - 📊 质量控制：检查响应质量
    - 📝 日志记录：记录模型行为

    Args:
        callback_context: 包含 agent_name 等上下文信息
        llm_response: 模型返回的响应

    Returns:
        - None: 使用原始响应
        - LlmResponse: 使用修改后的响应
    """
    agent_name = callback_context.agent_name
    logger.info(f"📥 [AFTER_MODEL] 收到响应，Agent: '{agent_name}'")

    # 检查响应内容
    original_text = ""
    if llm_response.content and llm_response.content.parts:
        if llm_response.content.parts[0].text:
            original_text = llm_response.content.parts[0].text
            logger.info(f"📏 响应长度: {len(original_text)} 字符")
        elif llm_response.content.parts[0].function_call:
            logger.info(f"🔧 响应包含工具调用: '{llm_response.content.parts[0].function_call.name}'")
            return None  # 不修改工具调用
    elif llm_response.error_message:
        logger.error(f"❌ 响应包含错误: '{llm_response.error_message}'")
        return None

    # 检查是否需要修改响应
    if original_text and ("执行完成" in original_text or "命令已执行" in original_text):
        logger.info("📝 为响应添加安全提示")
        
        # 创建新的响应对象
        modified_parts = [deepcopy(part) for part in llm_response.content.parts]
        modified_parts[0].text = original_text + "\n\n⚠️ 安全提示：以上操作已经过安全审核。"
        
        new_response = LlmResponse(
            content=types.Content(role="model", parts=modified_parts),
            grounding_metadata=llm_response.grounding_metadata
        )
        return new_response

    # 返回 None 使用原始响应
    return None


# ========== 3. 工具执行回调 ==========
# 这些回调在调用外部工具（如文件操作、命令执行）时触发


def before_tool_callback(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """
    在执行工具调用之前触发。
    这是实施工具级别安全策略的关键点。

    用途：
    - 🛡️ 参数验证：确保参数安全有效
    - 🔐 权限检查：验证是否有权限执行
    - 📝 审计日志：记录所有工具调用
    - 🚫 操作拦截：阻止危险操作

    Args:
        tool: 工具对象
        args: 工具参数字典
        tool_context: 包含 agent_name 等上下文信息

    Returns:
        - None: 继续使用（可能已修改的）参数
        - Dict: 跳过工具执行并返回此结果
    """
    agent_name = tool_context.agent_name
    tool_name = tool.name
    logger.info(f"🔧 [BEFORE_TOOL] 准备调用工具 '{tool_name}'，Agent: '{agent_name}'")
    logger.info(f"📋 参数: {args}")

    # 针对不同工具的安全策略
    if tool_name == "start_process":
        command = args.get("command", "")

        # 定义危险命令模式（更详细的黑名单）
        dangerous_patterns = [
            "rm -rf /",  # 删除根目录
            ":(){ :|:& };:",  # Fork 炸弹
            "dd if=/dev/zero",  # 磁盘擦除
            "mkfs",  # 创建文件系统
            "> /dev/sda",  # 覆写磁盘
        ]

        # 检查每个危险模式
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                logger.error(f"🚫 阻止危险命令: {command}")
                # 返回错误结果，跳过工具执行
                return {
                    "error": f"安全策略禁止执行该命令！检测到危险模式: '{pattern}'",
                    "blocked": True
                }

        # 可以修改参数
        if command.upper() == "BLOCK":
            logger.warning(f"⚠️ 检测到 BLOCK 关键词，跳过工具执行")
            return {"result": "工具执行被 before_tool_callback 阻止"}

        logger.info(f"✅ 命令通过安全检查: {command}")

    elif tool_name == "write_file":
        # 检查文件路径，防止覆盖系统文件
        file_path = args.get("path", "")
        if file_path.startswith("/etc/") or file_path.startswith("/sys/"):
            return {"error": "禁止写入系统目录", "blocked": True}

    # 返回 None 以继续执行（可能已修改的参数）
    return None


def after_tool_callback(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:
    """
    在工具执行完成后调用。
    可以处理、过滤或增强工具的输出。

    用途：
    - 📊 结果验证：检查执行是否成功
    - 🔍 输出过滤：隐藏敏感信息
    - 📝 执行记录：记录工具执行结果
    - 🔄 错误处理：统一错误格式

    Args:
        tool: 工具对象
        args: 使用的参数
        tool_context: 包含 agent_name 等上下文信息
        tool_response: 工具返回的结果

    Returns:
        - None: 使用原始结果
        - Dict: 使用修改后的结果
    """
    agent_name = tool_context.agent_name
    tool_name = tool.name
    logger.info(f"✅ [AFTER_TOOL] 工具 '{tool_name}' 执行完成，Agent: '{agent_name}'")
    logger.info(f"📋 使用的参数: {args}")
    logger.info(f"📄 原始结果: {tool_response}")

    # 处理不同类型的结果
    if isinstance(tool_response, dict):
        # 错误处理
        if tool_response.get("error"):
            error_msg = tool_response["error"]
            logger.error(f"❌ 工具执行失败: {error_msg}")

            # 创建修改后的响应
            modified_response = deepcopy(tool_response)
            modified_response["user_friendly_error"] = f"操作失败：{error_msg}"
            return modified_response

        # 成功结果处理
        else:
            # 记录结果（智能截断）
            result_str = str(tool_response)
            if len(result_str) > 200:
                logger.info(f"📄 结果预览: {result_str[:200]}...")
                logger.info(f"📏 （完整结果长度: {len(result_str)} 字符）")
            else:
                logger.info(f"📄 完整结果: {result_str}")

            # 示例：为某些工具添加执行统计
            if tool_name == "start_process" and "output" in tool_response:
                modified_response = deepcopy(tool_response)
                lines = tool_response.get("output", "").count("\n")
                modified_response["stats"] = {"output_lines": lines}
                modified_response["note_from_callback"] = "已添加输出统计信息"
                logger.info(f"📊 已添加统计信息: {lines} 行输出")
                return modified_response

    # 返回 None 使用原始结果
    return None




# 创建工具集
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
    tools=[mcp_toolset],
    # 注册所有回调函数
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)


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

    # 创建 Runner
    runner = Runner(
        agent=root_agent, app_name=app_name, session_service=session_service
    )

    print(
        f"🐠 会话已创建: App='{app_name}', " f"User='{user_id}', Session='{session_id}'"
    )
    print("🐠 已启用回调点位：")
    print("   - before_agent: 在 Agent 执行前")
    print("   - after_agent: 在 Agent 执行后")
    print("   - before_model: 在调用模型前（含安全过滤）")
    print("   - after_model: 在模型响应后")
    print("   - before_tool: 在工具调用前（含参数验证）")
    print("   - after_tool: 在工具调用后（含结果处理）")

    # 示例交互 - 展示命令执行功能和安全拦截
    example_queries = [
        "现在几点了？",
        "请执行 rm -rf /tmp/test（测试危险命令拦截）",  # 测试危险命令拦截
    ]

    print("\n🐠 开始示例交互...")
    for query in example_queries:
        await call_agent(query, runner, user_id, session_id)
        print("\n" + "-" * 60 + "\n")

    print("🐠 示例交互完成！")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
