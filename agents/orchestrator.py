from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..core.state import AgentState

# 初始化 LLM（生产环境应替换为私有模型）
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

INTENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个物流协同助手意图分类器。请将用户问题分类为以下之一：
    - order_status: 查询订单状态
    - policy_query: 询问规则政策
    - commission_rule: 佣金结算问题
    - damage_report: 货品破损上报
    - missing_task: 到仓无任务
    - compensation_claim: 赔偿诉求
    - user_complaint: 用户投诉
    - multi_issue: 多问题复合
    - other: 其他或无法识别
    
    只返回 JSON: {"intent": "...", "confidence": 0.x}"""),
    ("human", "{question}")
])

def run_orchestrator(state: AgentState) -> dict:
    question = state["messages"][-1].content
    
    # 敏感词立即拦截
    sensitive_words = ["赔偿", "起诉", "隐私", "个人信息", "罚款"]
    if any(w in question for w in sensitive_words):
        return {
            "intent": "sensitive_blocked",
            "confidence": 1.0,
            "requires_human": True,
            "response_text": "该问题涉及敏感内容，请【点击转人工】由专员为您处理。"
        }
    
    # 调用 LLM 分类
    chain = INTENT_PROMPT | llm
    try:
        result = chain.invoke({"question": question})
        parsed = eval(result.content)  # 实际应用中用 JSON parser
        intent = parsed["intent"]
        confidence = parsed["confidence"]
    except:
        intent, confidence = "other", 0.0
    
    # 低置信度转人工
    if confidence < 0.85 or intent == "other":
        return {
            "intent": "low_confidence",
            "confidence": confidence,
            "requires_human": True,
            "response_text": "请描述更清楚，或【联系人工客服】。"
        }
    
    return {
        "intent": intent,
        "confidence": confidence,
        "requires_human": False
    }