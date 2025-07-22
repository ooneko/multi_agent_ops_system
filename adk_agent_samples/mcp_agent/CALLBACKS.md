# MCP Agent 回调功能说明

本项目在 MCP Agent 中实现了 Google ADK 风格的回调机制，用于在不同阶段拦截和修改 Agent 的行为。

## 实现方式

由于当前 ADK 版本可能尚未暴露完整的回调 API，我们使用了包装器模式（Wrapper Pattern）来实现回调功能。这种方式通过 `MCPCallbackRunner` 类包装原始的 `Runner`，在消息处理流程中插入回调点。

## 回调点位说明

### 1. before_agent_callback ✅ 已实现
- **触发时机**: 在 Agent 执行核心逻辑之前
- **函数签名**: `before_agent_callback(agent_name: str, config: Dict[str, Any]) -> Dict[str, Any]`
- **用途**: 修改 Agent 配置，添加额外的上下文
- **返回值**: 修改后的配置字典
- **实现位置**: `MCPCallbackRunner.run_async()` 方法开始处

### 2. after_agent_callback ✅ 已实现
- **触发时机**: 在 Agent 执行核心逻辑之后
- **函数签名**: `after_agent_callback(agent_name: str, result: Any) -> Any`
- **用途**: 记录执行结果，进行后处理
- **返回值**: 处理后的结果
- **实现位置**: `MCPCallbackRunner.run_async()` 方法结束处

### 3. before_model_callback ✅ 已实现
- **触发时机**: 在调用语言模型之前
- **函数签名**: `before_model_callback(messages: List[Dict[str, str]], model_name: str) -> List[Dict[str, str]]`
- **用途**: 
  - 输入验证和过滤
  - 安全检查（如危险命令拦截）
  - 消息预处理
- **返回值**: 过滤后的消息列表
- **实现位置**: `MCPCallbackRunner.run_async()` 方法中

### 4. after_model_callback ✅ 已实现
- **触发时机**: 在模型返回响应之后
- **函数签名**: `after_model_callback(event: Any, model_name: str) -> Any`
- **用途**: 
  - 响应过滤
  - 添加免责声明
  - 日志记录
- **返回值**: 处理后的事件对象
- **实现位置**: `MCPCallbackRunner.run_async()` 方法中

### 5. before_tool_callback ✅ 已实现
- **触发时机**: 在调用工具之前
- **函数签名**: `before_tool_callback(tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]`
- **用途**: 
  - 工具参数验证
  - 权限检查
  - 危险操作拦截
- **返回值**: 验证后的工具参数
- **实现位置**: `CallbackMCPToolset.__call__()` 方法中

### 6. after_tool_callback ✅ 已实现
- **触发时机**: 在工具执行完成后
- **函数签名**: `after_tool_callback(tool_name: str, tool_result: Any) -> Any`
- **用途**: 
  - 结果处理
  - 日志记录
  - 错误处理
- **返回值**: 处理后的工具结果
- **实现位置**: `CallbackMCPToolset.__call__()` 方法中

## 实现示例

### Agent 生命周期回调示例

```python
# before_agent_callback - 在 Agent 开始执行前
def before_agent_callback(agent_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"🚀 [BEFORE_AGENT] '{agent_name}' 准备开始执行")
    logger.info(f"📋 配置信息: {config}")
    
    # 示例：根据用户或会话添加特殊配置
    if config.get("user_id") == "admin":
        config["skip_safety_check"] = True  # 管理员可跳过某些安全检查
        config["max_retries"] = 5  # 管理员有更多重试次数
    
    return config

# after_agent_callback - 在 Agent 完成执行后
def after_agent_callback(agent_name: str, result: Any) -> Any:
    logger.info(f"✅ [AFTER_AGENT] '{agent_name}' 执行完成")
    
    # 示例：记录执行统计
    if isinstance(result, dict):
        execution_time = result.get("execution_time", "N/A")
        success = result.get("success", False)
        
        # 可以在这里发送监控指标或通知
        if not success:
            logger.error(f"Agent 执行失败: {result.get('error', 'Unknown error')}")
    
    return result
```

### 模型交互回调示例

```python
# before_model_callback - 危险命令拦截
def before_model_callback(messages, model_name):
    filtered_messages = []
    for msg in messages:
        msg_copy = msg.copy()
        content = msg_copy.get("content", "")
        
        # 检测危险命令
        dangerous_commands = ["rm -rf", "format", "delete", "drop database"]
        if any(danger in content.lower() for danger in dangerous_commands):
            logger.warning(f"⚠️ 检测到危险命令: {content}")
            msg_copy["content"] = "🛑 您的请求包含潜在危险操作，已被安全策略拦截。"
        
        filtered_messages.append(msg_copy)
    return filtered_messages

# after_model_callback - 响应增强
def after_model_callback(event, model_name):
    if hasattr(event, 'is_final_response') and event.is_final_response():
        if hasattr(event, 'content') and event.content and event.content.parts:
            original_text = event.content.parts[0].text
            
            # 为特定类型的响应添加安全提示
            if "执行完成" in original_text:
                event.content.parts[0].text = (
                    original_text + 
                    "\n\n⚠️ 安全提示：以上操作已经过安全审核。"
                )
    return event
```

## 使用方式

1. **回调函数定义**: 在 `agent.py` 中定义了 6 个回调函数
2. **Runner 包装**: 通过 `MCPCallbackRunner` 类包装原始 Runner 处理 Agent 和模型回调
3. **工具包装**: 通过 `CallbackMCPToolset` 类包装原始工具集处理工具回调
4. **自动调用**: 在消息处理流程中自动调用相应的回调函数

## 测试示例

运行 agent.py 时，可以测试以下场景：

```bash
# 启动 Agent
python agent.py

# 测试普通命令（正常执行）
"帮我看看当前目录"

# 测试危险命令拦截（会被 before_model_callback 拦截）
"执行 rm -rf /tmp/test"

# 查看回调日志输出
# 日志会显示每个回调的触发时机和处理结果
```

## 注意事项

- 所有回调都会记录详细日志，便于调试和审计
- 安全策略可根据需要自定义，在 `before_model_callback` 和 `before_tool_callback` 中添加更多检查
- 当前实现使用包装器模式（`MCPCallbackRunner` 和 `CallbackMCPToolset`）
- 未来 ADK 可能会提供更原生的回调支持，届时可以迁移到官方 API

## 扩展建议

1. **增加更多安全检查**: 在 `before_model_callback` 中添加更多危险模式检测
2. **实现缓存机制**: 在回调中实现对常见查询的缓存
3. **添加审计日志**: 将所有回调触发记录到专门的审计日志文件
4. **性能监控**: 在回调中添加性能指标收集

