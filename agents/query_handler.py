from ..tools.mock_tms import get_order_status
from ..tools.mock_policy import lookup_policy
from ..core.state import AgentState

QUERY_INTENTS = ["order_status", "policy_query", "commission_rule"]

def run_query_handler(state: AgentState) -> dict:
    intent = state["intent"]
    question = state["messages"][-1].content
    
    # 提取关键词（简化）
    if "ORD" in question:
        order_id = next((w for w in question.split() if w.startswith("ORD")), None)
    else:
        order_id = None
    
    # 调用对应工具
    if intent == "order_status" and order_id:
        data = get_order_status(order_id)
        response = f"订单 {order_id} 状态：{data['status']}"
    elif intent == "policy_query":
        keyword = "生鲜破损" if "烂" in question or "破损" in question else "通用"
        response = lookup_policy(keyword)
    else:
        response = "暂无法回答此问题。"
    
    # 安全审查：禁止模糊词
    if any(w in response for w in ["可能", "大概", "建议"]):
        return {"requires_human": True, "response_text": "信息需人工确认，请联系客服。"}
    
    return {"response_text": response}