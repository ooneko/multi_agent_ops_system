"""
MCP Agent Demo - Agent 调用 MCP 协议的示例
"""
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.genai import types

# 加载环境变量
load_dotenv()

# 定义工作目录为代码运行目录
WORKSPACE_PATH = os.path.abspath(os.getcwd())

# 创建 MCP Agent
root_agent = Agent(
    model=LiteLlm(model='deepseek/deepseek-chat'),  # 使用 DeepSeek 模型
    name='mcp_agent_demo',
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
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",  # 自动确认安装
                    "@wonderwhy-er/desktop-commander",
                ],
                env={
                    "DESKTOP_COMMANDER_WORKSPACE": WORKSPACE_PATH,
                }
            ),
            # 可选：根据需要过滤工具
            # tool_filter=['start_process', 'read_file', 'write_file', 'search_files']
        )
    ],
)

async def call_agent(query: str, runner, user_id: str, session_id: str):
    """向 MCP Agent 发送查询并获取响应"""
    print(f"\n🐠 >>> 用户查询: {query}")

    # 准备用户消息
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response = "Agent 没有产生响应。"

    # 执行 agent 并处理事件流
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
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
    """主函数 - 运行 MCP Agent 示例"""
    print("\n🐠 ===== MCP Agent Demo 启动 =====")
    print(f"🐠 工作目录: {WORKSPACE_PATH}")

    # 创建会话服务
    session_service = InMemorySessionService()

    # 定义应用和用户标识
    app_name = "mcp_agent_demo"
    user_id = "user_1"
    session_id = "session_001"

    # 创建会话
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )

    # 创建 Runner
    runner = Runner(
        agent=root_agent,
        app_name=app_name,
        session_service=session_service
    )

    print(f"🐠 会话已创建: App='{app_name}', User='{user_id}', Session='{session_id}'")

    # 示例交互 - 展示命令执行功能
    example_queries = [
        "我想知道现在在哪个目录下工作",
        "帮我看看当前目录有哪些文件，要详细信息",
        "检查一下系统安装的 Python 是什么版本",
        "现在几点了？",
    ]
    
    print("\n🐠 开始示例交互...")
    for query in example_queries:
        await call_agent(query, runner, user_id, session_id)
        print("\n" + "-" * 60 + "\n")
    
    print("🐠 示例交互完成！")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())