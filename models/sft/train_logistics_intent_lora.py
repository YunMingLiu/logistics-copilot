"""
LoRA 微调脚本：支持 15+ 物流意图分类，输出可用于置信度过滤的模型。
"""

import os
import json
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, TaskType
from dataset import LogisticsIntentDataset  # 假设已适配多标签
import torch

# ================== 配置 ==================
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OUTPUT_DIR = "./models/sft/logistics_intent_lora"
LABELS_FILE = "./config/intent_labels.txt"  # 存储所有意图名称（每行一个）

EPOCHS = 5
BATCH_SIZE = 32
LEARNING_RATE = 3e-4  # LoRA 可用稍大学习率

LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.1
TARGET_MODULES = ["query", "key", "value"]


def load_labels(label_file):
    if not os.path.exists(label_file):
        raise FileNotFoundError(f"标签文件未找到: {label_file}")
    with open(label_file, "r", encoding="utf-8") as f:
        labels = [line.strip() for line in f if line.strip()]
    print(f"加载 {len(labels)} 个物流意图标签: {labels[:3]}...")
    return labels


def main():
    labels = load_labels(LABELS_FILE)
    num_labels = len(labels)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    if tokenizer.pad_token is None:
        tokenizer.add_special_tokens({'pad_token': '[PAD]'})

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=num_labels,
        ignore_mismatched_sizes=True,
    )
    if model.config.pad_token_id is None:
        model.config.pad_token_id = tokenizer.pad_token_id
    if len(tokenizer) != model.get_input_embeddings().weight.size(0):
        model.resize_token_embeddings(len(tokenizer))

    # 应用 LoRA
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type=TaskType.SEQ_CLS,
        target_modules=TARGET_MODULES,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # 保存标签映射（用于推理）
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "intent_labels.json"), "w", encoding="utf-8") as f:
        json.dump(labels, f, ensure_ascii=False, indent=2)

    train_dataset = LogisticsIntentDataset("data/logistics_train.jsonl", tokenizer, labels)

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        logging_steps=20,
        save_strategy="epoch",
        save_total_limit=2,
        fp16=torch.cuda.is_available(),
        optim="adamw_torch",
        report_to="none",
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        tokenizer=tokenizer,
    )

    print("开始 LoRA 微调（物流意图识别）...")
    trainer.train()
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"模型与标签已保存至: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()