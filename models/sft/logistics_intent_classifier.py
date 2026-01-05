# models/sft/logistics_intent_classifier.py
"""
物流意图分类器：支持置信度输出，用于路由决策。
"""

import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from peft import PeftModel


class LogisticsIntentClassifier:
    def __init__(self, model_path: str, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        # 加载标签
        with open(f"{model_path}/intent_labels.json", "r", encoding="utf-8") as f:
            self.labels = json.load(f)
        self.num_labels = len(self.labels)

        # 加载分词器和模型
        base_model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = '[PAD]'

        model = AutoModelForSequenceClassification.from_pretrained(
            base_model_name,
            num_labels=self.num_labels,
            ignore_mismatched_sizes=True,
        )
        model = PeftModel.from_pretrained(model, model_path)
        model.eval()
        model.to(self.device)

        self.tokenizer = tokenizer
        self.model = model

    def predict(self, text: str, threshold: float = 0.0):
        """
        预测意图及置信度。
        Args:
            text: 用户输入文本
            threshold: 置信度过滤阈值（可选）
        Returns:
            dict: {
                "intent_id": int,
                "intent_name": str,
                "confidence": float (0.0~1.0)
            }
        """
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128,
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1).cpu().squeeze()
            confidence, pred_id = torch.max(probs, dim=-1)
            pred_id = pred_id.item()
            confidence = confidence.item()

        result = {
            "intent_id": pred_id,
            "intent_name": self.labels[pred_id],
            "confidence": round(confidence, 4)
        }

        if confidence < threshold:
            result["warning"] = f"置信度低于阈值 {threshold}，建议人工审核"

        return result


# 示例使用
if __name__ == "__main__":
    classifier = LogisticsIntentClassifier("./models/sft/logistics_intent_lora")
    
    test_texts = [
        "我的货物在运输中破损了，请申请赔付",
        "需要将配送路线从A仓改为B仓",
        "库存不足，申请紧急补货",
        "今天天气真好！"  # 非物流意图（应低置信度）
    ]

    for text in test_texts:
        res = classifier.predict(text, threshold=0.7)
        print(f"输入: {text}")
        print(f"输出: {res}\n")