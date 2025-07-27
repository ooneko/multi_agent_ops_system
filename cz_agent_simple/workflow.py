"""LangGraph 工作流定义"""
import re
from typing import Dict, Any, List
from datetime import datetime
from langgraph.graph import StateGraph, END
from cz_agent_simple.state import AgentState, QueryIntent, QueryAnalysis, DiagnosisResult
from cz_agent_simple.tools import (
    query_servers_tool,
    get_server_details_tool, 
    get_server_topology_tool,
    get_rack_topology_tool,
    get_switch_info_tool,
    get_installation_logs_tool,
    analyze_installation_failure_tool
)
import logging

logger = logging.getLogger(__name__)


async def analyze_query(state: AgentState) -> AgentState:
    """分析用户查询意图"""
    user_query = state["user_query"]
    user_query_lower = user_query.lower()
    
    # 初始化分析结果
    intent = QueryIntent.UNKNOWN
    entities = {}
    filters = {}
    confidence = 0.0
    
    # 提取服务器ID（使用原始查询保留大小写）
    server_id_match = re.search(r'(srv-\d+|server-\d+)', user_query, re.IGNORECASE)
    if server_id_match:
        entities["server_id"] = server_id_match.group(1)
    
    # 提取机柜ID（使用原始查询保留大小写）
    # 先尝试匹配完整的rack-xxx格式
    if 'rack-' in user_query_lower:
        rack_id_match = re.search(r'(rack-[a-zA-Z0-9]+)', user_query)
        if rack_id_match:
            entities["rack_id"] = rack_id_match.group(1)
    elif '机柜' in user_query:
        rack_id_match = re.search(r'机柜([a-zA-Z0-9]+)', user_query)
        if rack_id_match:
            entities["rack_id"] = f"rack-{rack_id_match.group(1)}"
    
    # 提取交换机ID
    switch_id_match = re.search(r'(sw-\w+-\d+|switch-\w+)', user_query, re.IGNORECASE)
    if switch_id_match:
        entities["switch_id"] = switch_id_match.group(1)
    
    # 判断查询意图
    if any(keyword in user_query_lower for keyword in ['安装失败', '装机失败', '失败原因', '故障诊断', '分析失败']):
        intent = QueryIntent.FAULT_DIAGNOSIS
        confidence = 0.95
    elif any(keyword in user_query_lower for keyword in ['装机日志', '安装日志', '日志']):
        intent = QueryIntent.INSTALLATION_LOG
        confidence = 0.9
    elif any(keyword in user_query_lower for keyword in ['拓扑', '网络连接', '连通性', '带内', '带外']):
        if '机柜' in user_query_lower or 'rack' in user_query_lower:
            intent = QueryIntent.RACK_ANALYSIS
        else:
            intent = QueryIntent.SERVER_TOPOLOGY
        confidence = 0.9
    elif any(keyword in user_query_lower for keyword in ['交换机', 'switch']):
        intent = QueryIntent.SWITCH_INFO
        confidence = 0.9
    elif any(keyword in user_query_lower for keyword in ['服务器列表', '所有服务器', '查询服务器', '查看服务器', '显示服务器', '查看']) and '服务器' in user_query_lower:
        intent = QueryIntent.SERVER_INFO
        confidence = 0.85
        # 提取筛选条件
        if '在线' in user_query_lower or 'online' in user_query_lower:
            filters["status"] = "online"
        elif '离线' in user_query_lower or 'offline' in user_query_lower:
            filters["status"] = "offline"
        elif '故障' in user_query_lower or 'failed' in user_query_lower:
            filters["status"] = "install_failed"
    elif entities.get("server_id"):
        intent = QueryIntent.SERVER_INFO
        confidence = 0.8
    
    # 更新状态
    state["query_analysis"] = QueryAnalysis(
        intent=intent,
        entities=entities,
        filters=filters,
        confidence=confidence
    )
    
    # 记录执行历史
    state["execution_history"].append({
        "step": "analyze_query",
        "timestamp": datetime.now().isoformat(),
        "result": f"Intent: {intent.value}, Confidence: {confidence}"
    })
    
    logger.info(f"查询分析完成 - 意图: {intent.value}, 置信度: {confidence}")
    return state


async def fetch_data(state: AgentState) -> AgentState:
    """根据意图获取数据"""
    analysis = state["query_analysis"]
    if not analysis:
        state["error"] = "查询分析失败"
        return state
    
    try:
        intent = analysis.intent
        entities = analysis.entities
        filters = analysis.filters
        
        if intent == QueryIntent.SERVER_INFO:
            if entities.get("server_id"):
                # 获取特定服务器信息
                result = await get_server_details_tool.ainvoke({"server_id": entities["server_id"]})
                state["server_info"] = result
            else:
                # 获取服务器列表
                result = await query_servers_tool.ainvoke(filters)
                state["server_info"] = result
        
        elif intent == QueryIntent.SERVER_TOPOLOGY:
            if entities.get("server_id"):
                result = await get_server_topology_tool.ainvoke({"server_id": entities["server_id"]})
                state["topology_info"] = result
        
        elif intent == QueryIntent.RACK_ANALYSIS:
            if entities.get("rack_id"):
                result = await get_rack_topology_tool.ainvoke({"rack_id": entities["rack_id"]})
                state["topology_info"] = result
        
        elif intent == QueryIntent.SWITCH_INFO:
            if entities.get("switch_id"):
                result = await get_switch_info_tool.ainvoke({"switch_id": entities["switch_id"]})
                state["switch_info"] = result
        
        elif intent == QueryIntent.INSTALLATION_LOG:
            if entities.get("server_id"):
                result = await get_installation_logs_tool.ainvoke({"server_id": entities["server_id"]})
                state["installation_logs"] = result
        
        elif intent == QueryIntent.FAULT_DIAGNOSIS:
            if entities.get("server_id"):
                # 获取综合诊断结果
                result = await analyze_installation_failure_tool.ainvoke({"server_id": entities["server_id"]})
                if "diagnosis" in result:
                    state["diagnosis"] = DiagnosisResult(
                        root_cause=result["diagnosis"]["root_cause"],
                        confidence=result["diagnosis"]["confidence"],
                        recommendations=result["diagnosis"]["recommendations"],
                        next_steps=result["diagnosis"]["next_steps"]
                    )
                # 同时获取相关数据
                state["server_info"] = await get_server_details_tool.ainvoke({"server_id": entities["server_id"]})
                state["topology_info"] = await get_server_topology_tool.ainvoke({"server_id": entities["server_id"]})
                state["installation_logs"] = await get_installation_logs_tool.ainvoke({"server_id": entities["server_id"]})
        
        # 记录执行历史
        state["execution_history"].append({
            "step": "fetch_data",
            "timestamp": datetime.now().isoformat(),
            "intent": intent.value
        })
        
    except Exception as e:
        logger.error(f"获取数据失败: {e}")
        state["error"] = f"获取数据失败: {str(e)}"
    
    return state


async def analyze_fault(state: AgentState) -> AgentState:
    """分析故障（如果需要）"""
    analysis = state["query_analysis"]
    
    # 只有在没有诊断结果且有故障相关数据时才进行分析
    if analysis and analysis.intent == QueryIntent.FAULT_DIAGNOSIS and not state.get("diagnosis"):
        # 基于已有数据进行简单分析
        recommendations = []
        root_cause = "需要进一步分析"
        
        # 检查拓扑信息
        if state.get("topology_info"):
            topo = state["topology_info"]
            if "out_of_band_network" in topo:
                oob = topo["out_of_band_network"]
                if not oob.get("connectivity", {}).get("is_connected", True):
                    recommendations.append("检查带外网络连接")
                    if oob.get("connectivity", {}).get("failure_reason"):
                        root_cause = oob["connectivity"]["failure_reason"]
        
        # 检查安装日志
        if state.get("installation_logs"):
            logs = state["installation_logs"]
            if "error_summary" in logs.get("installation", {}):
                root_cause = logs["installation"]["error_summary"]
        
        state["diagnosis"] = DiagnosisResult(
            root_cause=root_cause,
            confidence="medium",
            recommendations=recommendations if recommendations else ["请联系技术支持"],
            next_steps=["收集更多日志", "检查硬件状态"]
        )
    
    return state


async def generate_response(state: AgentState) -> AgentState:
    """生成最终响应"""
    analysis = state["query_analysis"]
    
    if state.get("error"):
        state["response"] = f"抱歉，处理您的请求时出现错误：{state['error']}"
        return state
    
    if not analysis:
        state["response"] = "抱歉，我无法理解您的查询意图。"
        return state
    
    response_parts = []
    
    # 根据意图生成响应
    if analysis.intent == QueryIntent.SERVER_INFO:
        if state.get("server_info"):
            info = state["server_info"]
            if "servers" in info:
                # 服务器列表
                response_parts.append(f"找到 {info['total']} 台服务器：")
                for server in info["servers"][:10]:  # 最多显示10台
                    response_parts.append(
                        f"- {server['server_id']} ({server['hostname']}): "
                        f"状态={server['status']}, "
                        f"位置={server['location']['room']}/{server['location']['rack']}"
                    )
                if info['total'] > 10:
                    response_parts.append(f"... 还有 {info['total'] - 10} 台服务器")
            else:
                # 单个服务器详情
                response_parts.append(f"服务器 {info['server_id']} 详情：")
                response_parts.append(f"- 主机名: {info['hostname']}")
                response_parts.append(f"- 状态: {info['status']}")
                response_parts.append(f"- IP地址: {info['ip_address']}")
                response_parts.append(f"- 硬件: {info['hardware']['cpu_cores']}核CPU, {info['hardware']['memory_gb']}GB内存")
                response_parts.append(f"- 位置: {info['location']['room']}/{info['location']['rack']}/U{info['location']['rack_position']}")
    
    elif analysis.intent == QueryIntent.SERVER_TOPOLOGY:
        if state.get("topology_info"):
            topo = state["topology_info"]
            response_parts.append(f"服务器 {topo['server_id']} 网络拓扑：")
            response_parts.append(f"\n带内网络:")
            response_parts.append(f"- 路径: {' → '.join(topo['in_band_network']['path'])}")
            response_parts.append(f"- 状态: {topo['in_band_network']['status']}")
            response_parts.append(f"\n带外网络:")
            response_parts.append(f"- 路径: {' → '.join(topo['out_of_band_network']['path'])}")
            response_parts.append(f"- 状态: {topo['out_of_band_network']['status']}")
            if topo['out_of_band_network'].get('connectivity', {}).get('failure_reason'):
                response_parts.append(f"- 故障原因: {topo['out_of_band_network']['connectivity']['failure_reason']}")
    
    elif analysis.intent == QueryIntent.RACK_ANALYSIS:
        if state.get("topology_info"):
            rack = state["topology_info"]
            response_parts.append(f"机柜 {rack['rack_id']} 分析：")
            response_parts.append(f"- 服务器总数: {rack['total_servers']}")
            response_parts.append(f"- 带内网络正常: {rack['in_band_connected']}")
            response_parts.append(f"- 带外网络正常: {rack['out_of_band_connected']}")
            if "alert" in rack:
                response_parts.append(f"\n⚠️ 告警: {rack['alert']}")
                response_parts.append(f"建议操作: {rack['recommended_action']}")
    
    elif analysis.intent == QueryIntent.FAULT_DIAGNOSIS:
        if state.get("diagnosis"):
            diag = state["diagnosis"]
            response_parts.append("故障诊断结果：")
            response_parts.append(f"\n根本原因: {diag.root_cause}")
            response_parts.append(f"置信度: {diag.confidence}")
            response_parts.append("\n建议措施:")
            for i, rec in enumerate(diag.recommendations, 1):
                response_parts.append(f"{i}. {rec}")
            response_parts.append("\n后续步骤:")
            for i, step in enumerate(diag.next_steps, 1):
                response_parts.append(f"{i}. {step}")
    
    elif analysis.intent == QueryIntent.INSTALLATION_LOG:
        if state.get("installation_logs"):
            logs = state["installation_logs"]
            if "installation" in logs:
                inst = logs["installation"]
                response_parts.append(f"服务器 {logs['server_id']} 安装日志：")
                response_parts.append(f"- 状态: {inst['status']}")
                response_parts.append(f"- 开始时间: {inst['start_time']}")
                if inst.get('error_summary'):
                    response_parts.append(f"- 错误摘要: {inst['error_summary']}")
                response_parts.append("\n日志详情:")
                for log in inst['logs'][-5:]:  # 显示最后5条
                    response_parts.append(f"[{log['timestamp']}] {log['level']}: {log['message']}")
            else:
                response_parts.append(logs.get("message", "没有找到安装日志"))
    
    elif analysis.intent == QueryIntent.SWITCH_INFO:
        if state.get("switch_info"):
            switch = state["switch_info"]
            response_parts.append(f"交换机 {switch['switch_id']} 信息：")
            response_parts.append(f"- 名称: {switch['name']}")
            response_parts.append(f"- 型号: {switch['model']}")
            response_parts.append(f"- 状态: {switch['status']}")
            response_parts.append(f"- 端口状态: {switch['port_summary']['up']}/{switch['port_summary']['total']} UP")
            response_parts.append(f"- 连接服务器数: {len(switch['connected_servers'])}")
    
    else:
        response_parts.append("抱歉，我无法处理您的查询。")
    
    state["response"] = "\n".join(response_parts)
    
    # 记录执行历史
    state["execution_history"].append({
        "step": "generate_response",
        "timestamp": datetime.now().isoformat()
    })
    
    return state


def should_analyze_fault(state: AgentState) -> str:
    """判断是否需要进行故障分析"""
    analysis = state.get("query_analysis")
    if analysis and analysis.intent == QueryIntent.FAULT_DIAGNOSIS and not state.get("diagnosis"):
        return "analyze_fault"
    return "generate_response"


def create_workflow() -> StateGraph:
    """创建 LangGraph 工作流"""
    # 创建状态图
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("analyze_query", analyze_query)
    workflow.add_node("fetch_data", fetch_data)
    workflow.add_node("analyze_fault", analyze_fault)
    workflow.add_node("generate_response", generate_response)
    
    # 设置入口点
    workflow.set_entry_point("analyze_query")
    
    # 添加边
    workflow.add_edge("analyze_query", "fetch_data")
    
    # 条件边：根据是否需要故障分析决定下一步
    workflow.add_conditional_edges(
        "fetch_data",
        should_analyze_fault,
        {
            "analyze_fault": "analyze_fault",
            "generate_response": "generate_response"
        }
    )
    
    workflow.add_edge("analyze_fault", "generate_response")
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()