# models/sft/dataset.py
import json
from torch.utils.data import Dataset

class IntentDataset(Dataset):
    def __init__(self, file_path, tokenizer, max_length=128):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []
        label_map = {"order_status": 0, "policy_query": 1, "operation_guide": 2}
        
        with open(file_path, 'r') as f:
            for line in f:
                item = json.loads(line)
                self.data.append({
                    "text": item["text"],
                    "label": label_map[item["intent"]]
                })
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        encoding = self.tokenizer(
            item["text"],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt"
        )
        return {
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "labels": torch.tensor(item["label"], dtype=torch.long)
        }