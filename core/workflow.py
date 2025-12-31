from langgraph.graph import StateGraph, END
from ..agents.orchestrator import run_orchestrator
from ..agents.query_handler import run_query_handler
from ..agents.action_handler import run_action_handler
from ..agents.incident_handler import run_incident_handler
from ..core.state import AgentState

# 意图路由映射
INTENT_ROUTES = {
    "order_status": "query",
    "policy_query": "query",
    "commission_rule": "query",
    "damage_report": "action",
    "missing_task": "action",
    "compensation_claim": "incident",
    "user_complaint": "incident",
    "multi_issue": "incident"
}

def route_intent(state: AgentState):
    if state["requires_human"]:
        return "return_response"
    intent = state["intent"]
    if intent in INTENT_ROUTES:
        return INTENT_ROUTES[intent]
    return "return_response"

# 构建图
workflow = StateGraph(AgentState)
workflow.add_node("orchestrator", run_orchestrator)
workflow.add_node("query", run_query_handler)
workflow.add_node("action", run_action_handler)
workflow.add_node("incident", run_incident_handler)

workflow.set_entry_point("orchestrator")
workflow.add_conditional_edges("orchestrator", route_intent)
workflow.add_edge("query", END)
workflow.add_edge("action", END)
workflow.add_edge("incident", END)

app = workflow.compile()