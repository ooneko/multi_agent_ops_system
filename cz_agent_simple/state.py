"""LangGraph 状态定义"""
from typing import List, Dict, Any, Optional, TypedDict
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class QueryIntent(Enum):
    """查询意图类型"""
    SERVER_INFO = "server_info"
    SERVER_TOPOLOGY = "server_topology"
    SWITCH_INFO = "switch_info"
    INSTALLATION_LOG = "installation_log"
    FAULT_DIAGNOSIS = "fault_diagnosis"
    RACK_ANALYSIS = "rack_analysis"
    UNKNOWN = "unknown"


@dataclass
class QueryAnalysis:
    """查询分析结果"""
    intent: QueryIntent
    entities: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class DiagnosisResult:
    """诊断结果"""
    root_cause: str
    confidence: str
    recommendations: List[str]
    next_steps: List[str]
    related_issues: List[Dict[str, Any]] = field(default_factory=list)


class AgentState(TypedDict):
    """Agent 状态定义"""
    # 用户输入
    user_query: str
    
    # 查询分析
    query_analysis: Optional[QueryAnalysis]
    
    # 数据收集
    server_info: Optional[Dict[str, Any]]
    topology_info: Optional[Dict[str, Any]]
    switch_info: Optional[Dict[str, Any]]
    installation_logs: Optional[Dict[str, Any]]
    
    # 批量数据（用于机柜级别分析）
    rack_servers: Optional[List[Dict[str, Any]]]
    affected_servers: Optional[List[str]]
    
    # 诊断结果
    diagnosis: Optional[DiagnosisResult]
    
    # 响应生成
    response: Optional[str]
    
    # 执行历史
    execution_history: List[Dict[str, Any]]
    
    # 错误信息
    error: Optional[str]
    
    # 元数据
    timestamp: datetime
    execution_time: Optional[float]