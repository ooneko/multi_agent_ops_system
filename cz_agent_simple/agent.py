"""沧竹 Agent - 智能运维助手主程序"""
import asyncio
import logging
from datetime import datetime

import litellm
from dotenv import load_dotenv
# Memory imports - using a simple list to store messages instead of deprecated ConversationBufferMemory

from cz_agent_simple.state import AgentState
from cz_agent_simple.workflow import create_workflow

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置 LiteLLM
litellm.drop_params = True  # 自动丢弃不支持的参数


class SimpleMemory:
    """简单的内存管理类，替代弃用的 ConversationBufferMemory"""
    
    def __init__(self):
        self.messages = []
        self.chat_memory = self  # 兼容旧代码
    
    def add_user_message(self, message: str):
        """添加用户消息"""
        self.messages.append({"role": "user", "content": message})
    
    def add_ai_message(self, message: str):
        """添加 AI 消息"""
        self.messages.append({"role": "assistant", "content": message})
    
    def clear(self):
        """清空消息历史"""
        self.messages = []
    
    @property
    def chat_history(self):
        """获取聊天历史"""
        return self.messages


class CZAgent:
    """沧竹智能运维助手"""
    
    def __init__(self, model: str = None):
        """
        初始化 Agent
        
        Args:
            model: LLM 模型名称，如果未指定则从环境变量读取
        """
        # 如果没有指定模型，从环境变量读取
        if model is None:
            import os
            # 检查是否有 DeepSeek API key
            if os.getenv("DEEPSEEK_API_KEY"):
                model = "deepseek/deepseek-chat"
            elif os.getenv("OPENAI_API_KEY"):
                model = "gpt-3.5-turbo"
            else:
                # 默认使用 DeepSeek
                model = "deepseek/deepseek-chat"
                logger.warning("未找到 API 密钥环境变量，使用默认模型: deepseek/deepseek-chat")
        
        self.model = model
        logger.info(f"使用模型: {self.model}")
        self.workflow = create_workflow()
        
        # 使用简单的消息列表替代弃用的 ConversationBufferMemory
        self.memory = SimpleMemory()
        
        # 系统提示词
        self.system_prompt = """你是沧竹(CZ-Agent)，一个专业的数据中心智能运维助手。

你的主要职责是：
1. 查询和分析服务器状态信息
2. 诊断服务器安装失败的原因
3. 分析网络拓扑和连通性问题
4. 提供专业的故障修复建议

你拥有以下能力：
- 查询服务器列表和详细信息
- 获取服务器的网络拓扑（带内/带外网络）
- 查看交换机信息和端口状态
- 分析服务器安装日志
- 诊断故障原因并提供解决方案

请以专业、准确、易懂的方式回答用户的问题。在分析故障时，要综合考虑多个维度的信息，给出具体可行的建议。"""
    
    async def process_query(self, query: str) -> str:
        """
        处理用户查询
        
        Args:
            query: 用户查询内容
            
        Returns:
            处理结果
        """
        try:
            # 创建初始状态
            initial_state: AgentState = {
                "user_query": query,
                "query_analysis": None,
                "server_info": None,
                "topology_info": None,
                "switch_info": None,
                "installation_logs": None,
                "rack_servers": None,
                "affected_servers": None,
                "diagnosis": None,
                "response": None,
                "execution_history": [],
                "error": None,
                "timestamp": datetime.now(),
                "execution_time": None
            }
            
            # 记录开始时间
            start_time = datetime.now()
            
            # 运行工作流
            logger.info(f"开始处理查询: {query}")
            final_state = await self.workflow.ainvoke(initial_state)
            
            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"查询处理完成，耗时: {execution_time:.2f}秒")
            
            # 返回响应
            return final_state.get("response", "抱歉，处理您的请求时出现了问题。")
            
        except Exception as e:
            logger.error(f"处理查询时出错: {e}")
            return f"处理您的请求时出现错误：{str(e)}"
    
    async def chat(self, message: str) -> str:
        """
        对话接口（带记忆功能）
        
        Args:
            message: 用户消息
            
        Returns:
            Agent 响应
        """
        # 添加到记忆
        self.memory.chat_memory.add_user_message(message)
        
        # 处理查询
        response = await self.process_query(message)
        
        # 添加响应到记忆
        self.memory.chat_memory.add_ai_message(response)
        
        return response
    
    def clear_memory(self):
        """清空对话记忆"""
        self.memory.clear()
        logger.info("对话记忆已清空")


async def main():
    """主函数 - 演示用法"""
    print("欢迎使用沧竹智能运维助手 (CZ-Agent)")
    print("=" * 50)
    
    # 创建 Agent
    agent = CZAgent()
    
    # 演示查询
    demo_queries = [
        "查看所有在线的服务器",
        "srv-0020的状态是什么",
        "分析srv-0020安装失败的原因",
        "查看rack-A02的网络拓扑",
        "获取sw-tor-001的信息"
    ]
    
    print("\n演示查询：")
    for query in demo_queries[:3]:  # 只演示前3个查询
        print(f"\n用户: {query}")
        response = await agent.process_query(query)
        print(f"Agent: {response}")
        print("-" * 50)
    
    # 交互式对话
    print("\n\n进入交互模式（输入 'exit' 退出，'clear' 清空记忆）")
    while True:
        try:
            user_input = input("\n用户: ")
            if user_input.lower() == 'exit':
                print("再见！")
                break
            elif user_input.lower() == 'clear':
                agent.clear_memory()
                print("记忆已清空")
                continue
            
            response = await agent.chat(user_input)
            print(f"\nAgent: {response}")
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())