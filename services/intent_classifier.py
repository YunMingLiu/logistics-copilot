# services/intent_classifier.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from config.settings import settings
from utils.metrics import INTENT_REQUESTS, INTENT_CONFIDENCE

class IntentClassifier:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.tokenizer = AutoTokenizer.from_pretrained(settings.INTENT_MODEL_PATH)
            self.model = AutoModelForSequenceClassification.from_pretrained(settings.INTENT_MODEL_PATH)
            self.model.eval()
            self._initialized = True

    def predict(self, text: str):
        INTENT_REQUESTS.inc()
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)
            confidence, pred = torch.max(probs, dim=-1)
            
            intent_id = pred.item()
            confidence_score = confidence.item()
            
            INTENT_CONFIDENCE.set(confidence_score)
            
            # 假设标签映射已保存在 config
            intent_map = {0: "order_status", 1: "policy_query", 2: "operation_guide"}
            intent = intent_map.get(intent_id, "unknown")
            
            return {"intent": intent, "confidence": confidence_score}