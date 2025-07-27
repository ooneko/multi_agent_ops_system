"""CZ-Agent 使用示例"""
import asyncio
import sys
import os

# 添加项目路径到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cz_agent_simple.agent import CZAgent


async def demo_basic_queries():
    """演示基本查询功能"""
    print("=== CZ-Agent 基本查询演示 ===\n")
    
    # 创建Agent
    agent = CZAgent()
    
    # 1. 查询服务器列表
    print("1. 查询在线服务器")
    response = await agent.process_query("查看所有在线的服务器")
    print(f"响应: {response}\n")
    print("-" * 50)
    
    # 2. 查询特定服务器
    print("\n2. 查询服务器详情")
    response = await agent.process_query("srv-0001的状态是什么")
    print(f"响应: {response}\n")
    print("-" * 50)
    
    # 3. 查询网络拓扑
    print("\n3. 查询网络拓扑")
    response = await agent.process_query("显示srv-0001的网络拓扑")
    print(f"响应: {response}\n")
    print("-" * 50)


async def demo_fault_diagnosis():
    """演示故障诊断功能"""
    print("\n\n=== CZ-Agent 故障诊断演示 ===\n")
    
    agent = CZAgent()
    
    # 1. 查找故障服务器
    print("1. 查找安装失败的服务器")
    response = await agent.process_query("显示所有安装失败的服务器")
    print(f"响应: {response}\n")
    print("-" * 50)
    
    # 2. 分析故障原因
    print("\n2. 分析故障原因")
    response = await agent.process_query("分析srv-0020安装失败的原因")
    print(f"响应: {response}\n")
    print("-" * 50)
    
    # 3. 查看安装日志
    print("\n3. 查看安装日志")
    response = await agent.process_query("查看srv-0020的安装日志")
    print(f"响应: {response}\n")
    print("-" * 50)


async def demo_rack_analysis():
    """演示机柜级别分析"""
    print("\n\n=== CZ-Agent 机柜分析演示 ===\n")
    
    agent = CZAgent()
    
    # 分析有问题的机柜
    print("分析机柜网络状态")
    response = await agent.process_query("查看机柜rack-A02的网络拓扑")
    print(f"响应: {response}\n")
    print("-" * 50)


async def demo_conversation():
    """演示对话功能（带记忆）"""
    print("\n\n=== CZ-Agent 对话演示 ===\n")
    
    agent = CZAgent()
    
    # 对话1
    print("用户: 有哪些服务器出现故障？")
    response = await agent.chat("有哪些服务器出现故障？")
    print(f"Agent: {response}\n")
    
    # 对话2（基于上下文）
    print("用户: 第一个服务器的详细信息是什么？")
    response = await agent.chat("第一个服务器的详细信息是什么？")
    print(f"Agent: {response}\n")
    
    # 清空记忆
    agent.clear_memory()
    print("(记忆已清空)")


async def main():
    """主函数"""
    print("欢迎使用 CZ-Agent 演示程序！")
    print("本演示将展示 CZ-Agent 的主要功能。\n")
    
    while True:
        print("\n请选择演示内容：")
        print("1. 基本查询功能")
        print("2. 故障诊断功能")
        print("3. 机柜级别分析")
        print("4. 对话功能演示")
        print("5. 运行所有演示")
        print("0. 退出")
        
        choice = input("\n请输入选项 (0-5): ")
        
        if choice == "0":
            print("感谢使用，再见！")
            break
        elif choice == "1":
            await demo_basic_queries()
        elif choice == "2":
            await demo_fault_diagnosis()
        elif choice == "3":
            await demo_rack_analysis()
        elif choice == "4":
            await demo_conversation()
        elif choice == "5":
            await demo_basic_queries()
            await demo_fault_diagnosis()
            await demo_rack_analysis()
            await demo_conversation()
        else:
            print("无效选项，请重新选择。")
        
        input("\n按回车继续...")


if __name__ == "__main__":
    # 设置事件循环策略（解决某些平台的兼容性问题）
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())