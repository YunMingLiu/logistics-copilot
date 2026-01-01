# agents/policy_handler.py
from services.rag_retriever import RAGPolicyRetriever
from utils.safety_guard import contains_sensitive_content
from utils.metrics import RAG_POLICY_HIT, RAG_POLICY_MISS, FALLBACK_TO_HUMAN

retriever = RAGPolicyRetriever()

def handle_policy_query(question: str, context: dict) -> dict:
    metadata_filter = {
        "region": context.get("region", "default"),
        "min_app_version": context.get("app_version", "0.0.0")
    }
    
    result = retriever.retrieve(question, metadata_filter=metadata_filter)
    
    if not result:
        RAG_POLICY_MISS.inc()
        FALLBACK_TO_HUMAN.inc()
        return {
            "answer": "未找到相关政策说明，请联系人工客服。",
            "action": "fallback_to_human"
        }
    
    if contains_sensitive_content(result["text"]):
        FALLBACK_TO_HUMAN.inc()
        return {
            "answer": "该问题涉及敏感内容，请联系人工客服。",
            "action": "fallback_to_human"
        }
    
    RAG_POLICY_HIT.inc()
    answer = f"根据最新政策：{result['text']}"
    if result["deep_link"]:
        answer += f"\n\n查看全文：{result['deep_link']}"
    
    return {"answer": answer, "action": "show_answer"}