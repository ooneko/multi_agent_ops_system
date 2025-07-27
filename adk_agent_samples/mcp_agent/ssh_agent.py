"""
SSH Agent - 基于 Google ADK 的远程服务器管理智能体

本示例展示了如何创建一个功能完整的 SSH Agent，包括：
1. SSH 连接管理（密码和密钥认证）
2. 远程命令执行
3. 文件传输（上传/下载）
4. 批量操作支持
5. 完整的安全回调机制

作者：SSH Agent 示例
版本：1.0
"""

import os
import paramiko
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
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
from copy import deepcopy

# 加载环境变量
load_dotenv()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 工作目录
WORKSPACE_PATH = os.path.abspath(os.getcwd())


# ========== SSH 连接管理器 ==========
class SSHConnectionManager:
    """
    SSH 连接池管理器
    - 支持密码和密钥认证
    - 连接复用和自动重连
    - 并发连接管理
    """
    
    def __init__(self, max_connections: int = 10):
        self.connections: Dict[str, paramiko.SSHClient] = {}
        self.max_connections = max_connections
        self.executor = ThreadPoolExecutor(max_workers=max_connections)
        self._lock = asyncio.Lock()
        
    def _create_ssh_client(self, host: str, port: int = 22, username: str = None,
                          password: str = None, key_file: str = None,
                          timeout: int = 30) -> paramiko.SSHClient:
        """创建 SSH 客户端"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # 认证方式优先级：密钥 > 密码
            if key_file and os.path.exists(key_file):
                # 使用密钥认证
                key = paramiko.RSAKey.from_private_key_file(key_file)
                client.connect(host, port=port, username=username, 
                             pkey=key, timeout=timeout)
                logger.info(f"✅ 使用密钥成功连接到 {host}:{port}")
            elif password:
                # 使用密码认证
                client.connect(host, port=port, username=username,
                             password=password, timeout=timeout)
                logger.info(f"✅ 使用密码成功连接到 {host}:{port}")
            else:
                raise ValueError("必须提供密码或密钥文件")
                
            return client
            
        except Exception as e:
            client.close()
            raise Exception(f"SSH 连接失败: {str(e)}")
    
    async def get_connection(self, host: str, port: int = 22, username: str = None,
                           password: str = None, key_file: str = None) -> paramiko.SSHClient:
        """获取或创建 SSH 连接"""
        async with self._lock:
            conn_key = f"{username}@{host}:{port}"
            
            # 检查现有连接
            if conn_key in self.connections:
                client = self.connections[conn_key]
                # 测试连接是否仍然有效
                try:
                    client.exec_command("echo test", timeout=5)
                    return client
                except:
                    logger.warning(f"连接 {conn_key} 已断开，重新连接...")
                    client.close()
                    del self.connections[conn_key]
            
            # 创建新连接
            if len(self.connections) >= self.max_connections:
                # 关闭最旧的连接
                oldest_key = next(iter(self.connections))
                self.connections[oldest_key].close()
                del self.connections[oldest_key]
                logger.info(f"连接池已满，关闭最旧连接: {oldest_key}")
            
            # 在线程池中创建连接（避免阻塞异步循环）
            loop = asyncio.get_event_loop()
            client = await loop.run_in_executor(
                self.executor,
                self._create_ssh_client,
                host, port, username, password, key_file
            )
            
            self.connections[conn_key] = client
            return client
    
    async def close_all(self):
        """关闭所有连接"""
        async with self._lock:
            for conn_key, client in self.connections.items():
                try:
                    client.close()
                    logger.info(f"关闭连接: {conn_key}")
                except:
                    pass
            self.connections.clear()
    
    def __del__(self):
        """析构函数，确保关闭所有连接"""
        for client in self.connections.values():
            try:
                client.close()
            except:
                pass


# ========== SSH 工具集合 ==========
# 创建全局连接管理器
ssh_manager = SSHConnectionManager()


# SSH 执行命令工具
class SSHExecuteTool(BaseTool):
    """SSH 远程命令执行工具"""
    
    name = "ssh_execute"
    description = "在远程服务器上执行命令"
    
    def run(self, host: str, command: str, username: str = None, 
            password: str = None, key_file: str = None, port: int = 22,
            timeout: int = 30) -> Dict[str, Any]:
        """
        执行远程命令
        
        Args:
            host: 目标主机地址
            command: 要执行的命令
            username: SSH 用户名
            password: SSH 密码（可选）
            key_file: 私钥文件路径（可选）
            port: SSH 端口（默认 22）
            timeout: 命令执行超时时间（秒）
        
        Returns:
            包含 stdout、stderr 和退出码的字典
        """
        try:
            # 异步转同步（因为 BaseTool 是同步的）
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def _execute():
                client = await ssh_manager.get_connection(
                    host, port, username, password, key_file
                )
                
                # 执行命令
                stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
                
                # 读取输出
                stdout_text = stdout.read().decode('utf-8', errors='ignore')
                stderr_text = stderr.read().decode('utf-8', errors='ignore')
                exit_code = stdout.channel.recv_exit_status()
                
                return {
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "exit_code": exit_code,
                    "host": host,
                    "command": command,
                    "success": exit_code == 0
                }
            
            result = loop.run_until_complete(_execute())
            loop.close()
            
            logger.info(f"✅ SSH 命令执行完成: {command[:50]}... on {host}")
            return result
            
        except Exception as e:
            logger.error(f"❌ SSH 执行失败: {str(e)}")
            return {
                "error": str(e),
                "success": False,
                "host": host,
                "command": command
            }


# SSH 文件上传工具
class SSHUploadTool(BaseTool):
    """SSH 文件上传工具"""
    
    name = "ssh_upload"
    description = "上传文件到远程服务器"
    
    def run(self, host: str, local_path: str, remote_path: str,
            username: str = None, password: str = None, key_file: str = None,
            port: int = 22) -> Dict[str, Any]:
        """
        上传文件到远程服务器
        
        Args:
            host: 目标主机地址
            local_path: 本地文件路径
            remote_path: 远程文件路径
            username: SSH 用户名
            password: SSH 密码（可选）
            key_file: 私钥文件路径（可选）
            port: SSH 端口
        """
        try:
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"本地文件不存在: {local_path}")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def _upload():
                client = await ssh_manager.get_connection(
                    host, port, username, password, key_file
                )
                
                # 创建 SFTP 客户端
                sftp = client.open_sftp()
                
                try:
                    # 确保远程目录存在
                    remote_dir = os.path.dirname(remote_path)
                    if remote_dir:
                        try:
                            sftp.stat(remote_dir)
                        except FileNotFoundError:
                            # 递归创建目录
                            dirs = []
                            while remote_dir and remote_dir != '/':
                                dirs.append(remote_dir)
                                remote_dir = os.path.dirname(remote_dir)
                            
                            for d in reversed(dirs):
                                try:
                                    sftp.mkdir(d)
                                except:
                                    pass
                    
                    # 上传文件
                    sftp.put(local_path, remote_path)
                    
                    # 获取文件信息
                    file_stat = sftp.stat(remote_path)
                    
                    return {
                        "success": True,
                        "local_path": local_path,
                        "remote_path": remote_path,
                        "size": file_stat.st_size,
                        "host": host
                    }
                    
                finally:
                    sftp.close()
            
            result = loop.run_until_complete(_upload())
            loop.close()
            
            logger.info(f"✅ 文件上传成功: {local_path} -> {host}:{remote_path}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 文件上传失败: {str(e)}")
            return {
                "error": str(e),
                "success": False,
                "host": host,
                "local_path": local_path,
                "remote_path": remote_path
            }


# SSH 文件下载工具
class SSHDownloadTool(BaseTool):
    """SSH 文件下载工具"""
    
    name = "ssh_download"
    description = "从远程服务器下载文件"
    
    def run(self, host: str, remote_path: str, local_path: str,
            username: str = None, password: str = None, key_file: str = None,
            port: int = 22) -> Dict[str, Any]:
        """
        从远程服务器下载文件
        
        Args:
            host: 目标主机地址
            remote_path: 远程文件路径
            local_path: 本地文件路径
            username: SSH 用户名
            password: SSH 密码（可选）
            key_file: 私钥文件路径（可选）
            port: SSH 端口
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def _download():
                client = await ssh_manager.get_connection(
                    host, port, username, password, key_file
                )
                
                # 创建 SFTP 客户端
                sftp = client.open_sftp()
                
                try:
                    # 确保本地目录存在
                    local_dir = os.path.dirname(local_path)
                    if local_dir:
                        os.makedirs(local_dir, exist_ok=True)
                    
                    # 下载文件
                    sftp.get(remote_path, local_path)
                    
                    # 获取文件信息
                    file_size = os.path.getsize(local_path)
                    
                    return {
                        "success": True,
                        "remote_path": remote_path,
                        "local_path": local_path,
                        "size": file_size,
                        "host": host
                    }
                    
                finally:
                    sftp.close()
            
            result = loop.run_until_complete(_download())
            loop.close()
            
            logger.info(f"✅ 文件下载成功: {host}:{remote_path} -> {local_path}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 文件下载失败: {str(e)}")
            return {
                "error": str(e),
                "success": False,
                "host": host,
                "remote_path": remote_path,
                "local_path": local_path
            }


# SSH 批量执行工具
class SSHBatchExecuteTool(BaseTool):
    """SSH 批量命令执行工具"""
    
    name = "ssh_batch_execute"
    description = "在多台服务器上批量执行命令"
    
    def run(self, hosts: List[Dict[str, Any]], command: str,
            parallel: bool = True, max_workers: int = 5) -> List[Dict[str, Any]]:
        """
        批量执行命令
        
        Args:
            hosts: 主机列表，每个元素包含 host、username、password/key_file 等
            command: 要执行的命令
            parallel: 是否并行执行
            max_workers: 最大并行数
        
        Returns:
            执行结果列表
        """
        results = []
        
        if parallel:
            # 并行执行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def _batch_execute():
                tasks = []
                for host_info in hosts:
                    task = self._execute_single(host_info, command)
                    tasks.append(task)
                
                # 限制并发数
                semaphore = asyncio.Semaphore(max_workers)
                
                async def _limited_execute(host_info):
                    async with semaphore:
                        return await self._execute_single(host_info, command)
                
                tasks = [_limited_execute(host_info) for host_info in hosts]
                return await asyncio.gather(*tasks)
            
            results = loop.run_until_complete(_batch_execute())
            loop.close()
        else:
            # 串行执行
            for host_info in hosts:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self._execute_single(host_info, command)
                )
                loop.close()
                results.append(result)
        
        # 统计结果
        success_count = sum(1 for r in results if r.get("success", False))
        logger.info(f"✅ 批量执行完成: {success_count}/{len(hosts)} 成功")
        
        return {
            "results": results,
            "summary": {
                "total": len(hosts),
                "success": success_count,
                "failed": len(hosts) - success_count
            }
        }
    
    async def _execute_single(self, host_info: Dict[str, Any], command: str) -> Dict[str, Any]:
        """执行单个主机命令"""
        ssh_tool = SSHExecuteTool()
        result = ssh_tool.run(
            host=host_info["host"],
            command=command,
            username=host_info.get("username"),
            password=host_info.get("password"),
            key_file=host_info.get("key_file"),
            port=host_info.get("port", 22)
        )
        return result


# ========== Agent 回调函数 ==========
# 复用原有的回调函数，添加 SSH 特定的安全检查

def before_model_callback_ssh(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """SSH Agent 特定的模型前回调"""
    agent_name = callback_context.agent_name
    logger.info(f"🔍 [SSH BEFORE_MODEL] 准备调用模型，Agent: '{agent_name}'")
    
    # 检查最后一条用户消息
    last_user_message = ""
    if llm_request.contents and llm_request.contents[-1].role == 'user':
        if llm_request.contents[-1].parts:
            last_user_message = llm_request.contents[-1].parts[0].text
    
    if last_user_message:
        logger.info(f"📨 检查 SSH 相关请求: '{last_user_message[:100]}...'")
    
    # SSH 特定的危险模式
    ssh_dangerous_patterns = [
        "rm -rf /",  # 删除根目录
        "dd if=/dev/zero of=/dev",  # 磁盘擦除
        ":(){ :|:& };:",  # Fork 炸弹
        "> /etc/passwd",  # 破坏系统文件
        "chmod -R 777 /",  # 修改系统权限
    ]
    
    # 安全检查
    if last_user_message:
        for pattern in ssh_dangerous_patterns:
            if pattern in last_user_message.lower():
                logger.warning(f"⚠️ 检测到危险 SSH 命令，阻止执行")
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=(
                            "🛑 检测到潜在危险的 SSH 命令。\n"
                            "出于安全考虑，该操作已被阻止。\n"
                            "如需执行此类操作，请联系系统管理员。"
                        ))]
                    )
                )
    
    return None


def before_tool_callback_ssh(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """SSH 工具执行前的安全检查"""
    tool_name = tool.name
    logger.info(f"🔧 [SSH BEFORE_TOOL] 准备调用工具 '{tool_name}'")
    
    # SSH 执行命令的安全检查
    if tool_name == "ssh_execute" or tool_name == "ssh_batch_execute":
        command = args.get("command", "")
        
        # 危险命令黑名单
        blacklist_commands = [
            "rm -rf /",
            "dd if=/dev/zero",
            "mkfs",
            "> /dev/",
            "format",
            ":(){",  # Fork bomb
        ]
        
        for dangerous in blacklist_commands:
            if dangerous in command:
                logger.error(f"🚫 阻止危险 SSH 命令: {command}")
                return {
                    "error": f"安全策略禁止执行该命令！检测到危险模式: '{dangerous}'",
                    "blocked": True,
                    "success": False
                }
        
        # 记录审计日志
        host = args.get("host", "unknown")
        username = args.get("username", "unknown")
        logger.info(f"📝 SSH 审计: {username}@{host} 执行命令: {command}")
    
    # 文件操作的路径检查
    elif tool_name in ["ssh_upload", "ssh_download"]:
        if tool_name == "ssh_upload":
            remote_path = args.get("remote_path", "")
            # 防止覆盖系统文件
            if remote_path.startswith("/etc/") or remote_path.startswith("/boot/"):
                return {
                    "error": "禁止上传到系统关键目录",
                    "blocked": True,
                    "success": False
                }
        
    return None


def after_tool_callback_ssh(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:
    """SSH 工具执行后的处理"""
    tool_name = tool.name
    
    # 处理 SSH 执行结果
    if tool_name == "ssh_execute" and isinstance(tool_response, dict):
        if tool_response.get("success"):
            # 添加执行时间戳
            modified_response = deepcopy(tool_response)
            modified_response["timestamp"] = datetime.now().isoformat()
            
            # 对于长输出进行截断提示
            stdout = tool_response.get("stdout", "")
            if len(stdout) > 1000:
                modified_response["output_truncated"] = True
                modified_response["full_length"] = len(stdout)
            
            return modified_response
    
    return None


# ========== 创建 SSH Agent ==========

# 创建本地工具集（可选）
mcp_toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command="npx",
        args=["-y", "@wonderwhy-er/desktop-commander"],
        env={"DESKTOP_COMMANDER_WORKSPACE": WORKSPACE_PATH},
    ),
)

# 创建 SSH Agent
ssh_agent = Agent(
    model=LiteLlm(model="deepseek/deepseek-chat"),
    name="ssh_operations_agent",
    instruction="""你是一个专业的 SSH 远程服务器管理助手，具备强大的远程操作能力。

核心能力：
1. **远程命令执行**：在远程服务器上执行各种 Shell 命令
2. **文件传输**：上传和下载文件到/从远程服务器
3. **批量操作**：同时在多台服务器上执行相同操作
4. **服务器管理**：系统监控、服务管理、日志查看等

支持的认证方式：
- 密码认证
- SSH 密钥认证

工作流程：
1. 理解用户的远程操作需求
2. 选择合适的 SSH 工具执行任务
3. 清晰展示操作结果和状态
4. 在出现错误时提供解决建议

安全原则：
- 执行命令前说明其作用
- 对危险操作给出警告
- 保护敏感信息（如密码）
- 记录所有操作日志

示例场景：
- "在服务器 192.168.1.100 上查看系统负载"
- "上传配置文件到多台服务器"
- "批量重启所有 Web 服务器的 nginx"
- "下载服务器日志文件进行分析"

注意：
- 请确保提供正确的服务器连接信息
- 优先使用 SSH 密钥认证以提高安全性
- 对于生产环境操作请格外谨慎
""",
    tools=[
        SSHExecuteTool(),
        SSHUploadTool(),
        SSHDownloadTool(),
        SSHBatchExecuteTool(),
        mcp_toolset  # 包含本地工具
    ],
    # 注册回调函数
    before_model_callback=before_model_callback_ssh,
    before_tool_callback=before_tool_callback_ssh,
    after_tool_callback=after_tool_callback_ssh,
)


# ========== 辅助函数 ==========

async def call_ssh_agent(query: str, runner, user_id: str, session_id: str):
    """向 SSH Agent 发送查询并获取响应"""
    print(f"\n🔐 >>> SSH 操作请求: {query}")
    
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
    
    print(f"🔐 <<< SSH Agent 响应:\n{final_response}")
    return final_response


async def main():
    """主函数 - 演示 SSH Agent 功能"""
    print("\n🔐 ===== SSH Agent 演示 =====")
    print(f"🔐 工作目录: {WORKSPACE_PATH}")
    print("\n📚 功能特性：")
    print("  1. 远程命令执行（支持密码和密钥认证）")
    print("  2. 文件上传下载（SFTP）")
    print("  3. 批量服务器操作")
    print("  4. 完整的安全审计")
    print("\n" + "=" * 50)
    
    # 创建会话服务
    session_service = InMemorySessionService()
    
    # 定义应用和用户标识
    app_name = "ssh_agent_demo"
    user_id = "user_1"
    session_id = "session_001"
    
    # 创建会话
    await session_service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
    
    # 创建 Runner
    runner = Runner(
        agent=ssh_agent, app_name=app_name, session_service=session_service
    )
    
    print(f"🔐 会话已创建: App='{app_name}', User='{user_id}', Session='{session_id}'")
    
    # 示例交互
    example_queries = [
        "在本地执行 echo 'Hello from SSH Agent' 命令",
        # 注意：以下示例需要实际的服务器信息
        # "在服务器 192.168.1.100 上执行 uptime 命令，用户名是 admin，密码是 password123",
        # "上传本地的 config.json 到服务器 192.168.1.100 的 /tmp/config.json",
    ]
    
    print("\n🔐 开始示例交互...")
    print("🔐 注意：要测试远程功能，请提供实际的服务器连接信息")
    
    for query in example_queries:
        await call_ssh_agent(query, runner, user_id, session_id)
        print("\n" + "-" * 60 + "\n")
    
    # 清理资源
    await ssh_manager.close_all()
    print("🔐 已关闭所有 SSH 连接")
    print("🔐 示例演示完成！")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())