# agents/api_handler.py
import requests
from config.settings import settings
from utils.metrics import API_CALL_COUNTER

def handle(intent: str, context: dict) -> dict:
    user_id = context.get("user_id")
    if not user_id:
        return {"answer": "请先登录", "action": "require_login"}

    try:
        if intent == "order_status":
            # 调用 Java 订单服务（通过内网 HTTP 或 gRPC）
            resp = requests.post(
                "http://order-service.internal/v1/status",
                json={"user_id": user_id, "last_order_only": True},
                timeout=2
            )
            if resp.status_code == 200:
                data = resp.json()
                answer = f"您的最新订单 {data['order_id']} 当前状态：{data['status']}，预计 {data['eta']} 到达。"
                return {"answer": answer, "action": "show_answer", "source": "order_api"}
        
        elif intent == "delivery_estimate":
            resp = requests.post(
                "http://logistics-service.internal/v1/estimate",
                json={"user_lat": context["lat"], "user_lng": context["lng"]},
                timeout=2
            )
            if resp.status_code == 200:
                eta = resp.json()["minutes"]
                return {
                    "answer": f"当前平均配送时间约 {eta} 分钟。",
                    "action": "show_answer",
                    "source": "logistics_api"
                }

        elif intent == "account_balance":
            # 注意：敏感操作需二次验证（此处简化）
            resp = requests.get(
                f"http://account-service.internal/v1/balance?user_id={user_id}",
                headers={"Authorization": f"Bearer {context['token']}"},
                timeout=2
            )
            if resp.status_code == 200:
                balance = resp.json()["balance"]
                return {
                    "answer": f"您的账户余额为 ¥{balance:.2f}。",
                    "action": "show_answer",
                    "source": "account_api"
                }

        # API 调用失败
        return {"answer": "系统繁忙，请稍后再试。", "action": "retry_later"}

    except Exception as e:
        # 记录错误，但不暴露细节
        API_CALL_COUNTER.labels(intent=intent, status="error").inc()
        return {"answer": "查询失败，请联系客服。", "action": "fallback_to_human"}