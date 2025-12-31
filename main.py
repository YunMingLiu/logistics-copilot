from core.workflow import app
from langchain_core.messages import HumanMessage

if __name__ == "__main__":
    # 模拟司机提问
    question = "ORD123 生鲜烂了怎么处理？"
    
    result = app.invoke({
        "messages": [HumanMessage(content=question)],
        "user_id": "DRV_8866",
        "user_role": "driver",
        "intent": None,
        "confidence": 0.0,
        "context": {},
        "response_text": "",
        "requires_human": False,
        "ticket_created": False,
        "deep_link": None
    })
    
    print("🤖 助手回复:", result["response_text"])
    if result.get("deep_link"):
        print("🔗 操作链接:", result["deep_link"])