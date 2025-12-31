from typing import TypedDict, List, Optional, Dict, Any
from langchain_core.messages import HumanMessage

class AgentState(TypedDict):
    # 短期记忆：单次会话上下文
    messages: List[HumanMessage]
    user_id: str                # 司机/团长 ID（已认证）
    user_role: str              # "driver" or "group_leader"
    
    # 意图识别结果
    intent: Optional[str]
    confidence: float
    
    # 工具调用上下文
    context: Dict[str, Any]
    
    # 各处理器输出
    response_text: str
    requires_human: bool
    ticket_created: bool
    deep_link: Optional[str]