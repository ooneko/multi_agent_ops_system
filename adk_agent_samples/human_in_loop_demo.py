"""
Human-in-the-Loop Demo - 展示如何使用 ADK Callback 实现人工审批
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
from threading import Event
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HumanApprovalSystem:
    """人工审批系统"""

    def __init__(self):
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self.approval_results: Dict[str, Dict[str, Any]] = {}
        self.approval_events: Dict[str, Event] = {}

    def request_approval(self, approval_id: str, request_data: Dict[str, Any]) -> str:
        """请求人工审批"""
        self.pending_approvals[approval_id] = {
            "id": approval_id,
            "timestamp": datetime.now().isoformat(),
            "data": request_data,
            "status": "pending",
        }

        # 创建等待事件
        self.approval_events[approval_id] = Event()

        # 记录审批请求
        logger.info(f"[APPROVAL REQUEST] ID: {approval_id}")
        logger.info(
            f"Request Data: {json.dumps(request_data, indent=2, ensure_ascii=False)}"
        )

        # 等待审批结果
        self.approval_events[approval_id].wait()

        # 获取审批结果
        result = self.approval_results.get(approval_id, {})
        return result

    def approve(self, approval_id: str, message: Optional[str] = None):
        """批准请求"""
        if approval_id in self.pending_approvals:
            self.approval_results[approval_id] = {
                "approved": True,
                "message": message or "已批准",
                "timestamp": datetime.now().isoformat(),
            }
            self.pending_approvals[approval_id]["status"] = "approved"

            # 触发等待事件
            if approval_id in self.approval_events:
                self.approval_events[approval_id].set()

            logger.info(f"[APPROVED] ID: {approval_id}")

    def reject(self, approval_id: str, reason: str):
        """拒绝请求"""
        if approval_id in self.pending_approvals:
            self.approval_results[approval_id] = {
                "approved": False,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            }
            self.pending_approvals[approval_id]["status"] = "rejected"

            # 触发等待事件
            if approval_id in self.approval_events:
                self.approval_events[approval_id].set()

            logger.info(f"[REJECTED] ID: {approval_id}, Reason: {reason}")


# 全局审批系统实例
approval_system = HumanApprovalSystem()


def before_model_callback_with_approval(
    messages: List[Dict[str, str]], model_name: str
) -> List[Dict[str, str]]:
    """带人工审批的 before_model 回调"""

    # 获取最新的用户消息
    user_message = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_message = msg.get("content", "")
            break

    if not user_message:
        return messages

    # 检查是否需要人工审批的场景
    need_approval = False
    approval_type = ""

    # 场景1：执行系统命令
    if any(
        cmd in user_message.lower() for cmd in ["执行", "运行", "启动", "删除", "修改"]
    ):
        need_approval = True
        approval_type = "command_execution"

    # 场景2：访问敏感信息
    elif any(
        sensitive in user_message.lower()
        for sensitive in ["密码", "密钥", "token", "secret"]
    ):
        need_approval = True
        approval_type = "sensitive_access"

    # 场景3：外部API调用
    elif any(api in user_message.lower() for api in ["api", "接口", "调用", "请求"]):
        need_approval = True
        approval_type = "api_call"

    if need_approval:
        # 生成审批ID
        approval_id = f"approval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 准备审批请求数据
        approval_request = {
            "type": approval_type,
            "user_message": user_message,
            "model": model_name,
            "context": {
                "message_count": len(messages),
                "timestamp": datetime.now().isoformat(),
            },
        }

        print("\n⚠️  需要人工审批 ⚠️")
        print(f"审批ID: {approval_id}")
        print(f"类型: {approval_type}")
        print(f"用户请求: {user_message}")
        print("\n请在另一个终端运行以下命令来批准或拒绝：")
        cmd_approve = (
            f'python -c "from human_in_loop_demo import approval_system; '
            f"approval_system.approve('{approval_id}')\""
        )
        print(f"批准: {cmd_approve}")
        cmd_reject = (
            f'python -c "from human_in_loop_demo import approval_system; '
            f"approval_system.reject('{approval_id}', '原因')\""
        )
        print(f"拒绝: {cmd_reject}")
        print("\n等待审批中...")

        # 请求审批（阻塞等待）
        result = approval_system.request_approval(approval_id, approval_request)

        if result.get("approved"):
            print(f"✅ 审批通过: {result.get('message')}")
            return messages
        else:
            print(f"❌ 审批拒绝: {result.get('reason')}")
            # 返回拒绝消息
            filtered_messages = messages.copy()
            filtered_messages[-1] = {
                "role": "user",
                "content": f"您的请求已被拒绝。原因：{result.get('reason')}",
            }
            return filtered_messages

    return messages


def create_agent_with_approval():
    """创建带人工审批的 Agent"""
    return Agent(
        model=LiteLlm(model="deepseek/deepseek-chat"),
        name="human_in_loop_agent",
        instruction="""你是一个需要人工审批的智能助手。

对于以下类型的请求，需要等待人工审批：
1. 执行系统命令
2. 访问敏感信息
3. 调用外部API

请清晰地解释你要做什么，并等待审批。
""",
    )


class HumanInLoopRunner:
    """支持人工审批的 Runner 包装器"""

    def __init__(self, runner):
        self.runner = runner
        self.model_name = "deepseek/deepseek-chat"

    async def run_async(self, user_id: str, session_id: str, new_message):
        # 准备消息格式
        messages = [
            {
                "role": new_message.role,
                "content": new_message.parts[0].text if new_message.parts else "",
            }
        ]

        # 调用带审批的 before_model 回调
        filtered_messages = before_model_callback_with_approval(
            messages, self.model_name
        )

        # 如果消息被修改，更新 new_message
        if filtered_messages[0]["content"] != messages[0]["content"]:
            new_message = types.Content(
                role=filtered_messages[0]["role"],
                parts=[types.Part(text=filtered_messages[0]["content"])],
            )

        # 调用原始 runner
        async for event in self.runner.run_async(
            user_id=user_id, session_id=session_id, new_message=new_message
        ):
            yield event


async def simulate_approval(approval_id: str, approve: bool = True, delay: float = 5.0):
    """模拟人工审批（用于演示）"""
    await asyncio.sleep(delay)

    if approve:
        approval_system.approve(approval_id, "模拟批准")
    else:
        approval_system.reject(approval_id, "模拟拒绝：不符合安全策略")


async def main():
    """主函数 - 演示 Human-in-the-Loop"""
    print("\n🤖 ===== Human-in-the-Loop Demo =====")

    # 创建 Agent
    agent = create_agent_with_approval()

    # 创建会话
    session_service = InMemorySessionService()
    app_name = "human_in_loop_demo"
    user_id = "user_1"
    session_id = "session_001"

    await session_service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )

    # 创建 Runner 并包装
    base_runner = Runner(
        agent=agent, app_name=app_name, session_service=session_service
    )
    runner = HumanInLoopRunner(base_runner)

    print("✅ 系统已启动，支持人工审批功能")
    print("\n演示场景：")

    # 测试场景
    test_queries = [
        "你好，介绍一下你自己",  # 不需要审批
        "帮我执行 ls -la 命令",  # 需要审批
        "获取系统的密码文件",  # 需要审批（敏感）
        "调用天气API获取北京天气",  # 需要审批（API）
    ]

    for i, query in enumerate(test_queries):
        print(f"\n--- 测试 {i+1}: {query} ---")

        content = types.Content(role="user", parts=[types.Part(text=query)])

        # 如果需要审批，启动模拟审批任务
        if i > 0:  # 除了第一个查询，其他都需要审批
            approval_id = f"approval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            # 模拟审批（第3个查询会被拒绝）
            asyncio.create_task(
                simulate_approval(
                    approval_id, approve=(i != 2), delay=3.0  # 第3个查询被拒绝
                )
            )

        # 执行查询
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    print(f"Agent 响应: {event.content.parts[0].text}")
                break

    print("\n✅ 演示完成！")


if __name__ == "__main__":
    asyncio.run(main())
