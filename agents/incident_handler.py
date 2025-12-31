import json
from ..utils.logger import log_incident
from ..core.state import AgentState

def run_incident_handler(state: AgentState) -> dict:
    # 模拟拉取多源数据（实际应并行调用）
    context = {
        "order": {"id": "ORD123", "status": "DELIVERED"},
        "gps": [{"time": "06:30", "location": "朝阳仓"}],
        "chat_log": ["用户：没收到货！"]
    }
    
    # 生成异常快照
    snapshot = {
        "user_id": state["user_id"],
        "intent": state["intent"],
        "context": context,
        "original_question": state["messages"][-1].content
    }
    
    # 记录工单（实际调用工单系统）
    log_incident(snapshot)
    
    return {
        "response_text": "已为您提交异常处理申请，专员将在10分钟内联系您。",
        "ticket_created": True,
        "requires_human": True
    }