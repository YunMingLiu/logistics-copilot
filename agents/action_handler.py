from ..tools.mock_tms import get_order_status
from ..tools.mock_policy import lookup_policy
from ..core.state import AgentState

ACTION_INTENTS = ["damage_report", "missing_task"]

def run_action_handler(state: AgentState) -> dict:
    intent = state["intent"]
    
    if intent == "damage_report":
        response = "检测到破损问题，请【上传照片申请补货】。"
        deep_link = "app://after-sales?category=perishable"
    elif intent == "missing_task":
        response = "检测到您可能漏派任务，是否【申请紧急补派】？"
        deep_link = "app://task/emergency-apply"
    else:
        response, deep_link = "操作暂不可用", None
    
    return {
        "response_text": response,
        "deep_link": deep_link
    }