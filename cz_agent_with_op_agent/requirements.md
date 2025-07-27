# 交付平台与运维Agent协作系统需求文档

## 1. 系统概述

本系统模拟一个真实的运维场景：交付平台Agent从交付平台获取服务器列表，然后委派Linux运维Agent通过SSH在这些服务器上执行命令。这是一个典型的多Agent协作场景。

## 2. 系统架构

```
┌─────────────────────────────────────┐
│         用户请求                     │
└────────────┬────────────────────────┘
             │
             v
┌─────────────────────────────────────┐
│    交付平台Agent (CZ Agent)          │
│  - 获取服务器列表（Mock MCP）        │
│  - 任务分解和调度                    │
│  - 结果汇总                         │
└────────────┬────────────────────────┘
             │
             v
┌─────────────────────────────────────┐
│    Linux运维Agent (Op Agent)         │
│  - SSH连接管理                       │
│  - 命令执行                         │
│  - 结果收集                         │
└─────────────────────────────────────┘
```

## 3. Agent详细设计

### 3.1 交付平台Agent (DeliveryPlatformAgent)

**职责：**
- 从交付平台MCP获取服务器列表（初期使用Mock数据）
- 解析运维任务需求
- 将任务委派给Linux运维Agent
- 汇总并格式化执行结果

**核心功能：**
1. **服务器发现**
   - Mock一个交付平台MCP工具，返回服务器列表
   - 服务器信息包括：hostname, ip, port, username, auth_type

2. **任务管理**
   - 接收用户的运维任务请求
   - 制定执行计划
   - 监控任务执行状态

3. **结果处理**
   - 收集各服务器的执行结果
   - 生成执行报告

### 3.2 Linux运维Agent (LinuxOpAgent)

**职责：**
- 执行系统健康检查和监控
- 管理系统服务和进程
- 进行故障诊断和排查
- 执行系统维护任务
- 收集和分析系统日志

**核心功能：**
1. **系统监控与健康检查**
   - CPU、内存、磁盘使用率监控
   - 系统负载和性能指标采集
   - 网络连接状态检查
   - 进程和端口监控
   - 系统资源异常告警

2. **服务管理**
   - 服务状态检查（systemctl status）
   - 服务启停和重启操作
   - 服务日志查看和分析
   - 服务配置验证
   - 自启动服务管理

3. **故障诊断**
   - 系统日志分析（/var/log/）
   - 性能瓶颈定位
   - 错误日志提取
   - 网络连通性测试
   - 磁盘IO问题排查

4. **系统维护**
   - 清理临时文件和过期日志
   - 系统包更新检查
   - 配置文件备份和管理
   - 定时任务（cron）管理
   - 用户权限审计

5. **安全巡检**
   - 登录日志检查（异常登录检测）
   - 防火墙规则审计
   - 开放端口扫描
   - 文件权限检查
   - 安全补丁状态

## 4. 数据模型

### 4.1 服务器信息
```python
{
    "id": "server-001",
    "hostname": "web-server-01",
    "ip": "192.168.1.10",
    "port": 22,
    "username": "ubuntu",
    "auth_type": "password",  # password/key
    "auth_credential": "mock_password",
    "tags": ["web", "production"],
    "status": "active"
}
```

### 4.2 任务定义
```python
{
    "task_id": "task-001",
    "name": "系统健康巡检",
    "type": "health_check",  # health_check/service_manage/troubleshoot/maintenance/security_audit
    "operations": [
        {
            "type": "system_monitor",
            "checks": ["cpu", "memory", "disk", "load"]
        },
        {
            "type": "service_check",
            "services": ["nginx", "mysql", "redis"]
        },
        {
            "type": "log_analysis",
            "logs": ["/var/log/syslog", "/var/log/nginx/error.log"],
            "pattern": "error|warning|critical"
        }
    ],
    "target_servers": ["server-001", "server-002"],
    "timeout": 300,  # 秒
    "parallel": True
}
```

### 4.3 执行结果
```python
{
    "task_id": "task-001",
    "status": "completed",  # pending/running/completed/failed
    "start_time": "2025-01-22T10:00:00Z",
    "end_time": "2025-01-22T10:05:00Z",
    "summary": {
        "total_servers": 2,
        "success": 2,
        "failed": 0,
        "alerts": 1
    },
    "results": {
        "server-001": {
            "status": "success",
            "health_score": 95,
            "system_monitor": {
                "cpu_usage": "15%",
                "memory_usage": "65%",
                "disk_usage": {"/": "45%", "/data": "78%"},
                "load_average": "0.5, 0.8, 0.6"
            },
            "service_status": {
                "nginx": "active (running)",
                "mysql": "active (running)",
                "redis": "active (running)"
            },
            "alerts": []
        },
        "server-002": {
            "status": "success",
            "health_score": 80,
            "system_monitor": {
                "cpu_usage": "75%",
                "memory_usage": "85%",
                "disk_usage": {"/": "55%", "/data": "92%"},
                "load_average": "2.5, 2.8, 2.6"
            },
            "service_status": {
                "nginx": "active (running)",
                "mysql": "active (running)",
                "redis": "inactive (dead)"
            },
            "alerts": [
                {
                    "level": "warning",
                    "type": "high_disk_usage",
                    "message": "/data partition is 92% full"
                },
                {
                    "level": "error",
                    "type": "service_down",
                    "message": "redis service is not running"
                }
            ]
        }
    }
}
```

## 5. 实现细节

### 5.1 技术栈
- **框架**: Google ADK (遵循现有项目规范)
- **SSH连接**: 使用现有SSH MCP工具
- **异步处理**: asyncio
- **日志**: Python logging

### 5.2 交互流程

1. **用户发起请求**
   ```
   用户: "检查所有生产环境服务器的磁盘使用情况"
   ```

2. **交付平台Agent处理**
   - 调用Mock MCP获取服务器列表
   - 筛选出生产环境服务器
   - 创建执行任务

3. **委派给Linux运维Agent**
   - 传递服务器列表和命令
   - 监控执行进度

4. **Linux运维Agent执行**
   - 调用SSH MCP工具连接服务器
   - 执行运维命令（系统监控、服务检查等）
   - 收集和分析结果

5. **返回结果**
   - 汇总各服务器执行结果
   - 格式化输出给用户

### 5.3 Mock数据设计

初期将Mock以下数据：
1. **服务器列表**: 5台不同角色的服务器（web、db、cache等）
2. **SSH连接**: 模拟成功/失败场景
3. **命令执行**: 返回预定义的命令输出

## 6. 安全考虑

1. **凭据管理**
   - 密码/密钥不明文存储
   - 使用环境变量或密钥管理服务

2. **命令安全**
   - 禁止执行危险命令（rm -rf /、shutdown等）
   - 命令参数验证

3. **审计日志**
   - 记录所有操作
   - 包含操作者、时间、目标、命令、结果

## 7. 扩展性设计

1. **MCP集成**
   - Mock接口设计便于后续替换为真实MCP
   - 统一的接口定义

2. **Agent扩展**
   - 支持添加更多类型的运维Agent
   - 插件化的命令执行器

3. **监控集成**
   - 预留监控指标接口
   - 支持Prometheus等监控系统

## 8. 测试策略

1. **单元测试**
   - Mock SSH连接测试
   - 命令解析测试
   - 结果处理测试

2. **集成测试**
   - Agent间通信测试
   - 完整流程测试

## 9. 评估方案 (基于Google ADK Evaluate框架)

### 9.1 评估策略

采用Google ADK的评估框架，重点评估：
- **工具使用准确性**：Agent是否选择了正确的工具和参数
- **任务完成质量**：运维操作的结果是否符合预期
- **执行路径合理性**：Agent的决策过程是否高效合理
- **错误处理能力**：面对异常情况的处理是否恰当

### 9.2 评估数据集设计

#### 9.2.1 健康检查场景评估
```json
{
  "test_name": "health_check_evaluation",
  "cases": [
    {
      "name": "正常服务器健康检查",
      "input": "检查生产环境服务器健康状态",
      "expected_tool_trajectory": [
        {
          "tool_name": "get_server_list",
          "parameters": {"filter": {"tags": ["production"]}}
        },
        {
          "tool_name": "execute_health_check",
          "parameters": {"server_ids": ["server-001", "server-002"]}
        }
      ],
      "expected_response": {
        "contains": ["健康度", "CPU使用率", "内存使用率", "服务状态"]
      }
    },
    {
      "name": "异常服务器检测",
      "input": "检查服务器异常情况",
      "expected_alerts": ["high_cpu_usage", "service_down", "disk_full"]
    }
  ]
}
```

#### 9.2.2 故障诊断场景评估
```json
{
  "test_name": "troubleshooting_evaluation",
  "cases": [
    {
      "name": "服务响应慢诊断",
      "input": "web-server-01响应很慢，帮我排查",
      "expected_tool_trajectory": [
        {
          "tool_name": "check_system_load",
          "parameters": {"server_id": "web-server-01"}
        },
        {
          "tool_name": "analyze_processes",
          "parameters": {"sort_by": "cpu"}
        },
        {
          "tool_name": "check_service_logs",
          "parameters": {"service": "nginx", "pattern": "error"}
        }
      ],
      "expected_diagnosis": {
        "identifies_issue": true,
        "provides_solution": true
      }
    }
  ]
}
```

### 9.3 评估指标

1. **功能性指标**
   - 工具调用准确率 (tool_accuracy_score): ≥ 0.9
   - 任务完成率 (task_completion_rate): ≥ 0.95
   - 响应相关性 (response_relevance_score): ≥ 0.85

2. **性能指标**
   - 平均响应时间 (avg_response_time): < 30s
   - 并发处理能力 (concurrent_capacity): ≥ 10 servers

3. **可靠性指标**
   - 错误处理覆盖率 (error_handling_coverage): 100%
   - 故障恢复成功率 (failure_recovery_rate): ≥ 0.9

### 9.4 评估实现

```python
# tests/evaluation/test_agent_evaluation.py
import pytest
from google.adk.evaluation import AgentEvaluator

@pytest.mark.asyncio
async def test_health_check_scenarios():
    """评估健康检查场景"""
    await AgentEvaluator.evaluate(
        agent_module="cz_agent_with_op_agent",
        eval_dataset_file_path_or_dir="tests/evaluation/datasets/health_check.evalset.json",
        config={
            "tool_trajectory_match_threshold": 0.9,
            "response_match_threshold": 0.85
        }
    )

@pytest.mark.asyncio
async def test_troubleshooting_scenarios():
    """评估故障诊断场景"""
    await AgentEvaluator.evaluate(
        agent_module="cz_agent_with_op_agent",
        eval_dataset_file_path_or_dir="tests/evaluation/datasets/troubleshooting.evalset.json",
        config={
            "tool_trajectory_match_threshold": 0.85,
            "diagnosis_accuracy_threshold": 0.8
        }
    )

@pytest.mark.asyncio
async def test_maintenance_scenarios():
    """评估系统维护场景"""
    await AgentEvaluator.evaluate(
        agent_module="cz_agent_with_op_agent",
        eval_dataset_file_path_or_dir="tests/evaluation/datasets/maintenance.evalset.json"
    )
```

### 9.5 持续改进流程

1. **基准测试** - 建立初始性能基准
2. **定期评估** - 每周运行完整评估套件
3. **结果分析** - 识别低分区域和改进点
4. **迭代优化** - 基于评估结果优化Agent行为
5. **回归测试** - 确保新改动不影响现有功能

## 10. 实现步骤

1. **第一阶段：基础框架** (~1小时)
   - 创建项目结构
   - 实现基础Agent类
   - Mock MCP工具

2. **第二阶段：交付平台Agent** (~1.5小时)
   - 实现服务器发现功能
   - 实现任务管理
   - 实现与运维Agent的通信

3. **第三阶段：Linux运维Agent** (~1.5小时)
   - 实现运维操作功能
   - 实现结果分析
   - 实现安全控制

4. **第四阶段：评估框架集成** (~1.5小时)
   - 创建评估数据集
   - 实现评估测试
   - 性能基准测试

5. **第五阶段：集成测试** (~0.5小时)
   - 完整流程测试
   - 性能优化

**预计总时间：约6小时**

## 10. 示例使用场景

### 场景1：系统健康巡检
```
用户: "对所有生产服务器进行健康检查"

执行流程:
1. 交付平台Agent获取服务器列表，筛选tag包含"production"的服务器
2. 创建健康检查任务，包含系统资源、服务状态、日志分析
3. Linux运维Agent执行：
   - 系统资源监控（CPU、内存、磁盘）
   - 关键服务状态检查
   - 系统日志错误分析
4. 返回健康报告：
   - server-001: 健康度95%，所有服务正常
   - server-002: 健康度80%，发现警告：磁盘使用率92%，redis服务停止
```

### 场景2：故障诊断
```
用户: "web-server-03响应缓慢，请排查原因"

执行流程:
1. 交付平台Agent定位目标服务器
2. Linux运维Agent执行故障诊断：
   - 检查系统负载和进程状态
   - 分析网络连接情况
   - 查看应用日志错误
   - 检查磁盘IO性能
3. 返回诊断结果：
   - 发现问题：CPU使用率95%，mysql进程占用过高
   - 原因分析：存在慢查询，导致数据库负载过高
   - 建议措施：优化SQL查询，增加索引
```

### 场景3：批量维护操作
```
用户: "清理所有服务器上30天前的日志文件"

执行流程:
1. 交付平台Agent获取所有服务器列表
2. Linux运维Agent执行维护任务：
   - 查找30天前的日志文件
   - 计算将释放的空间
   - 执行清理操作
   - 验证清理结果
3. 返回执行报告：
   - 总计清理服务器：10台
   - 释放总空间：150GB
   - 各服务器清理详情
```

---

请确认以上需求文档是否符合您的期望？确认后我将开始实现。