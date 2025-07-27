"""验证项目设置"""
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("🐠 CZ-Agent 设置验证\n")
print("=" * 50)

# 1. 检查 Python 版本
print(f"\n1. Python 版本: {sys.version.split()[0]}")
if sys.version_info >= (3, 8):
    print("   ✅ Python 版本符合要求 (>= 3.8)")
else:
    print("   ❌ 需要 Python 3.8 或更高版本")

# 2. 检查环境变量
print("\n2. 环境变量配置:")
api_key = os.getenv("DEEPSEEK_API_KEY")
if api_key:
    masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"   ✅ DEEPSEEK_API_KEY: {masked}")
else:
    print("   ❌ DEEPSEEK_API_KEY 未设置")
    print("   💡 请在 .env 文件中设置您的 API 密钥")

# 3. 检查项目文件
print("\n3. 项目文件检查:")
required_files = [
    "agent.py",
    "workflow.py", 
    "tools.py",
    "state.py",
    "models.py",
    "mcp_client.py",
    "mock_mcp_server.py",
    "requirements.txt",
    ".env"
]

missing_files = []
for file in required_files:
    # scripts 目录的父目录是项目根目录
    project_root = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(project_root, file)
    if os.path.exists(path):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} (缺失)")
        missing_files.append(file)

# 4. 模拟模型选择
print("\n4. 模型选择逻辑:")
if os.getenv("DEEPSEEK_API_KEY"):
    print("   🤖 将使用: deepseek/deepseek-chat")
elif os.getenv("OPENAI_API_KEY"):
    print("   🤖 将使用: gpt-3.5-turbo")
else:
    print("   ⚠️  未配置 API 密钥，将使用默认模型")

# 5. 总结
print("\n" + "=" * 50)
print("\n📊 验证结果总结:\n")

issues = []
if sys.version_info < (3, 8):
    issues.append("Python 版本过低")
if not api_key:
    issues.append("未配置 API 密钥")
if missing_files:
    issues.append(f"缺失 {len(missing_files)} 个文件")

if not issues:
    print("✅ 所有检查通过！项目已准备就绪。")
    print("\n下一步:")
    print("1. 安装依赖: pip install -r requirements.txt")
    print("2. 运行 Agent: python -m cz_agent_simple.agent")
else:
    print("❌ 发现以下问题:")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    print("\n请解决以上问题后再继续。")

print("\n🐠 验证完成！")