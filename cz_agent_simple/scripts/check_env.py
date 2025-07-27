"""测试环境变量配置"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

print("=== 环境变量配置检查 ===\n")

# 检查各种 API 密钥
api_keys = {
    "DEEPSEEK_API_KEY": "DeepSeek",
    "OPENAI_API_KEY": "OpenAI",
    "GOOGLE_API_KEY": "Google AI",
    "ANTHROPIC_API_KEY": "Anthropic"
}

found_keys = []
for env_var, provider in api_keys.items():
    value = os.getenv(env_var)
    if value:
        # 隐藏密钥的大部分内容
        masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
        print(f"✅ {provider}: {env_var} = {masked_value}")
        found_keys.append(provider)
    else:
        print(f"❌ {provider}: {env_var} 未设置")

print("\n=== 模型选择逻辑 ===\n")

# 模拟 CZAgent 的模型选择逻辑
if os.getenv("DEEPSEEK_API_KEY"):
    selected_model = "deepseek/deepseek-chat"
    print(f"将使用模型: {selected_model} (基于 DEEPSEEK_API_KEY)")
elif os.getenv("OPENAI_API_KEY"):
    selected_model = "gpt-3.5-turbo"
    print(f"将使用模型: {selected_model} (基于 OPENAI_API_KEY)")
else:
    print("⚠️  未找到任何 API 密钥，将使用默认模型: deepseek/deepseek-chat")

print("\n=== 其他配置 ===\n")

# 检查其他可能的配置
other_configs = {
    "LOG_LEVEL": "日志级别",
    "MCP_SERVER_HOST": "MCP 服务器主机",
    "MCP_SERVER_PORT": "MCP 服务器端口"
}

for env_var, description in other_configs.items():
    value = os.getenv(env_var)
    if value:
        print(f"• {description}: {value}")

if not any(os.getenv(var) for var in other_configs):
    print("• 没有设置其他配置项")

print("\n=== 测试完成 ===")
print(f"\n发现 {len(found_keys)} 个可用的 LLM 提供商: {', '.join(found_keys) if found_keys else '无'}")

# 测试 LiteLLM 是否可以正常工作
if found_keys:
    print("\n正在测试 LiteLLM 连接...")
    try:
        import litellm
        # 仅导入，不实际调用 API
        print("✅ LiteLLM 模块加载成功")
    except Exception as e:
        print(f"❌ LiteLLM 加载失败: {e}")
else:
    print("\n⚠️  请在 .env 文件中配置至少一个 API 密钥")