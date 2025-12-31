# tests/test_intents.py
import pytest
from langchain_core.messages import HumanMessage
from core.workflow import app  


@pytest.fixture
def mock_user_state():
    """返回一个标准的初始状态，用于测试"""
    return {
        "messages": [],
        "user_id": "TEST_USER_001",
        "user_role": "driver",
        "intent": None,
        "confidence": 0.0,
        "context": {},
        "response_text": "",
        "requires_human": False,
        "ticket_created": False,
        "deep_link": None
    }


def run_agent_with_input(user_input: str, state=None):
    """封装调用 LangGraph 应用的逻辑"""
    if state is None:
        state = {
            "messages": [HumanMessage(content=user_input)],
            "user_id": "TEST_USER_001",
            "user_role": "driver",
            "intent": None,
            "confidence": 0.0,
            "context": {},
            "response_text": "",
            "requires_human": False,
            "ticket_created": False,
            "deep_link": None
        }
    else:
        state["messages"] = [HumanMessage(content=user_input)]
    result = app.invoke(state)
    return result


# ————————————————————————
# 敏感词拦截测试
# ————————————————————————
def test_sensitive_word_blocking():
    """测试敏感词命中立即转人工"""
    sensitive_inputs = [
        "你们要赔我200块！",
        "我要起诉你们泄露我的隐私",
        "再不处理我就去工商局投诉"
    ]
    for inp in sensitive_inputs:
        result = run_agent_with_input(inp)
        assert result["requires_human"] is True
        assert "敏感" in result["response_text"] or "人工" in result["response_text"]


# ————————————————————————
# 低置信度/未知意图兜底
# ————————————————————————
def test_low_confidence_fallback():
    """测试模糊或无法识别的问题转人工"""
    vague_inputs = [
        "今天天气怎么样？",  # 与物流无关
        "你好啊",           # 无明确意图
        "这个东西怎么弄？"   # 指代不明
    ]
    for inp in vague_inputs:
        result = run_agent_with_input(inp)
        # 注意：在 orchestrator 中，LLM 可能返回 intent="other" 或 confidence < 0.85
        # 所以 requires_human 应为 True
        assert result["requires_human"] is True
        assert "请描述更清楚" in result["response_text"] or "人工客服" in result["response_text"]


# ————————————————————————
# 查询类意图（order_status / policy_query）
# ————————————————————————
def test_order_status_query():
    """测试订单状态查询"""
    result = run_agent_with_input("ORD123 到哪了？")
    assert "DELIVERED" in result["response_text"]
    assert result["requires_human"] is False


def test_policy_query():
    """测试政策查询"""
    result = run_agent_with_input("生鲜烂了怎么办？")
    assert "上传照片" in result["response_text"] or "补货" in result["response_text"]
    assert result["requires_human"] is False


# ————————————————————————
# 操作建议类（damage_report / missing_task）
# ————————————————————————
def test_damage_report_action():
    """测试破损上报引导"""
    result = run_agent_with_input("刚送的牛奶箱破了，里面漏了")
    assert "上传照片" in result["response_text"]
    assert result["deep_link"] == "app://after-sales?category=perishable"


def test_missing_task_action():
    """测试漏派任务引导"""
    result = run_agent_with_input("到仓发现没给我派单")
    assert "紧急补派" in result["response_text"]
    assert result["deep_link"] == "app://task/emergency-apply"


# ————————————————————————
# 高风险/复合异常类（compensation_claim / user_complaint）
# ————————————————————————
def test_compensation_claim_incident():
    """测试赔偿诉求触发工单"""
    result = run_agent_with_input("用户说没收到货，要我赔500，怎么办？")
    assert "专员将在10分钟内联系您" in result["response_text"]
    assert result["requires_human"] is True
    assert result["ticket_created"] is True  # 如果你在 incident_handler 中设置了此字段


# ————————————————————————
# 安全审查：Query Handler 中的模糊词拦截
# ————————————————————————
def test_query_handler_hallucination_block():
    """模拟 Query Handler 返回含‘可能’的回答 → 被安全审查拦截"""
    pass  # 实际项目中可通过 monkeypatch 模拟工具返回含“可能”的文本


if __name__ == "__main__":
    pytest.main([__file__, "-v"])