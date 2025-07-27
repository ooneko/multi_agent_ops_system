#!/usr/bin/env python
"""简单测试脚本"""
import asyncio
import os
import sys

# 设置 Python 路径 - 需要到达包含 cz_agent_simple 的父目录
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from cz_agent_simple.agent import CZAgent

async def main():
    print("🐠 测试 CZ-Agent")
    print("=" * 50)
    
    # 创建 Agent
    agent = CZAgent(model="deepseek/deepseek-chat")
    
    # 测试查询
    queries = [
        "查看所有在线的服务器",
        "获取srv-001的详细信息",
        "查看rack-A02的网络拓扑"
    ]
    
    for query in queries:
        print(f"\n📝 查询: {query}")
        print("-" * 30)
        response = await agent.process_query(query)
        print(f"响应:\n{response}")
        print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())