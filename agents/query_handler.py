from ..tools.mock_tms import get_order_status
from ..tools.mock_policy import lookup_policy
from ..core.state import AgentState
import logging
from services.rag_retriever import RAGRetriever  # 自定义 RAG 检索服务
from utils.safety_guard import contains_sensitive_content
from constants import POLICY_SIMILARITY_THRESHOLD
# agents/query_handler.py
from services.intent_classifier import IntentClassifier
from services.rag_retriever import RAGPolicyRetriever
from utils.safety_guard import contains_sensitive_content, mask_pii
from utils.metrics import FALLBACK_TO_HUMAN
from config.settings import settings

classifier = IntentClassifier()
retriever = RAGPolicyRetriever()

def handle_query(user_question: str, user_context: dict) -> dict:
    # Step 1: 脱敏
    clean_question = mask_pii(user_question)
    
    # Step 2: 意图识别
    intent_result = classifier.predict(clean_question)
    intent = intent_result["intent"]
    confidence = intent_result["confidence"]
    
    # Step 3: 低置信度兜底
    if confidence < 0.85:
        FALLBACK_TO_HUMAN.inc()
        return {"answer": "未理解您的问题，请联系人工客服。", "action": "fallback_to_human"}
    
    # Step 4: 分发
    if intent == "policy_query":
        from .policy_handler import handle_policy_query
        return handle_policy_query(clean_question, user_context)
    elif intent == "order_status":
        return {"answer": "正在查询订单状态...", "action": "call_order_api"}
    else:
        FALLBACK_TO_HUMAN.inc()
        return {"answer": "该问题暂不支持，请联系人工客服。", "action": "fallback_to_human"}
    
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

def handle_policy_query(user_question: str, user_context: dict) -> dict:
    """
    安全 RAG 政策问答：检索 + 模板回答，禁止 LLM 生成
    """
    metadata_filter = {
        "region": user_context.get("region", "default"),
        "min_app_version": user_context.get("app_version", "0.0.0")
    }

    # Step 1: RAG 检索
    results = retriever.retrieve(
        query=user_question,
        top_k=1,
        metadata_filter=metadata_filter,
        threshold=POLICY_SIMILARITY_THRESHOLD
    )

    # Step 2: 未命中 → 转人工
    if not results:
        return {
            "answer": "未找到相关政策说明，请联系人工客服。",
            "action": "fallback_to_human",
            "source": "rag_policy_miss"
        }

    snippet = results[0]["text"]

    # Step 3: 敏感内容拦截
    if contains_sensitive_content(snippet):
        return {
            "answer": "该问题涉及敏感内容，请联系人工客服。",
            "action": "fallback_to_human",
            "source": "rag_policy_sensitive"
        }

    # Step 4: 安全组装答案（固定模板）
    answer = f"根据最新政策：{snippet}"
    if results[0]["deep_link"]:
        answer += f"\n\n查看全文：{results[0]['deep_link']}"

    return {
        "answer": answer,
        "action": "show_answer",
        "source": "rag_policy_hit"
    }

