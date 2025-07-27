"""状态定义测试"""
import unittest
from datetime import datetime
from cz_agent_simple.state import QueryIntent, QueryAnalysis, DiagnosisResult, AgentState


class TestQueryIntent(unittest.TestCase):
    """测试查询意图枚举"""
    
    def test_query_intent_values(self):
        """测试意图枚举值"""
        self.assertEqual(QueryIntent.SERVER_INFO.value, "server_info")
        self.assertEqual(QueryIntent.FAULT_DIAGNOSIS.value, "fault_diagnosis")
        self.assertEqual(QueryIntent.UNKNOWN.value, "unknown")
    
    def test_all_intents_defined(self):
        """测试所有意图都已定义"""
        intents = [intent.value for intent in QueryIntent]
        expected = [
            "server_info", "server_topology", "switch_info",
            "installation_log", "fault_diagnosis", "rack_analysis", "unknown"
        ]
        self.assertEqual(sorted(intents), sorted(expected))


class TestQueryAnalysis(unittest.TestCase):
    """测试查询分析结果"""
    
    def test_default_initialization(self):
        """测试默认初始化"""
        analysis = QueryAnalysis(intent=QueryIntent.SERVER_INFO)
        self.assertEqual(analysis.intent, QueryIntent.SERVER_INFO)
        self.assertEqual(analysis.entities, {})
        self.assertEqual(analysis.filters, {})
        self.assertEqual(analysis.confidence, 0.0)
    
    def test_with_entities_and_filters(self):
        """测试带实体和过滤器的初始化"""
        analysis = QueryAnalysis(
            intent=QueryIntent.FAULT_DIAGNOSIS,
            entities={"server_id": "srv-001"},
            filters={"status": "install_failed"},
            confidence=0.95
        )
        self.assertEqual(analysis.entities["server_id"], "srv-001")
        self.assertEqual(analysis.filters["status"], "install_failed")
        self.assertEqual(analysis.confidence, 0.95)


class TestDiagnosisResult(unittest.TestCase):
    """测试诊断结果"""
    
    def test_diagnosis_result_initialization(self):
        """测试诊断结果初始化"""
        diagnosis = DiagnosisResult(
            root_cause="网络配置错误",
            confidence="high",
            recommendations=["检查DHCP服务器"],
            next_steps=["重新尝试安装"]
        )
        self.assertEqual(diagnosis.root_cause, "网络配置错误")
        self.assertEqual(diagnosis.confidence, "high")
        self.assertEqual(len(diagnosis.recommendations), 1)
        self.assertEqual(len(diagnosis.next_steps), 1)
        self.assertEqual(diagnosis.related_issues, [])
    
    def test_with_related_issues(self):
        """测试包含相关问题的诊断结果"""
        diagnosis = DiagnosisResult(
            root_cause="交换机故障",
            confidence="high",
            recommendations=["更换交换机"],
            next_steps=["联系网络团队"],
            related_issues=[
                {"server_id": "srv-002", "issue": "同机柜服务器也无法连接"}
            ]
        )
        self.assertEqual(len(diagnosis.related_issues), 1)
        self.assertEqual(diagnosis.related_issues[0]["server_id"], "srv-002")


class TestAgentState(unittest.TestCase):
    """测试 Agent 状态"""
    
    def test_agent_state_creation(self):
        """测试创建 Agent 状态"""
        now = datetime.now()
        state: AgentState = {
            "user_query": "查看服务器srv-001的状态",
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
            "timestamp": now,
            "execution_time": None
        }
        
        self.assertEqual(state["user_query"], "查看服务器srv-001的状态")
        self.assertIsNone(state["query_analysis"])
        self.assertEqual(state["execution_history"], [])
        self.assertEqual(state["timestamp"], now)
    
    def test_agent_state_with_data(self):
        """测试包含数据的 Agent 状态"""
        analysis = QueryAnalysis(
            intent=QueryIntent.SERVER_INFO,
            entities={"server_id": "srv-001"}
        )
        
        state: AgentState = {
            "user_query": "查看服务器srv-001的状态",
            "query_analysis": analysis,
            "server_info": {"server_id": "srv-001", "status": "online"},
            "topology_info": None,
            "switch_info": None,
            "installation_logs": None,
            "rack_servers": None,
            "affected_servers": None,
            "diagnosis": None,
            "response": "服务器srv-001当前状态为在线",
            "execution_history": [
                {"step": "query_analysis", "duration": 0.1},
                {"step": "fetch_server_info", "duration": 0.5}
            ],
            "error": None,
            "timestamp": datetime.now(),
            "execution_time": 0.6
        }
        
        self.assertEqual(state["query_analysis"].intent, QueryIntent.SERVER_INFO)
        self.assertEqual(state["server_info"]["status"], "online")
        self.assertEqual(len(state["execution_history"]), 2)
        self.assertEqual(state["execution_time"], 0.6)
    
    def test_type_annotations(self):
        """测试类型注解的正确性"""
        # 这个测试主要是确保 TypedDict 定义正确
        # 在运行时不会强制类型，但有助于IDE和类型检查器
        annotations = AgentState.__annotations__
        
        # 检查关键字段的类型注解
        self.assertEqual(annotations["user_query"], str)
        self.assertEqual(annotations["timestamp"], datetime)
        # 检查可选字段和列表字段存在
        self.assertIn("query_analysis", annotations)
        self.assertIn("execution_history", annotations)


if __name__ == "__main__":
    unittest.main()