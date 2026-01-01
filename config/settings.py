# config/settings.py
import os

class Settings:
    # Model
    INTENT_MODEL_PATH = os.getenv("INTENT_MODEL_PATH", "models/sft/intent_model")
    EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
    
    # RAG
    POLICY_INDEX_PATH = "data/policy_faiss.index"
    POLICY_DOCS_PATH = "data/policy_docs.npy"
    POLICY_SIMILARITY_THRESHOLD = 0.75
    
    # Safety
    SENSITIVE_KEYWORDS = {"赔", "投诉升级", "诉讼", "法律"}
    
    # App
    APP_VERSION = "1.0.0"

settings = Settings()