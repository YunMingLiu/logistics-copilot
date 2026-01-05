# config.py
import os

# 文档路径
POLICY_DOCS_PATH = os.getenv("POLICY_DOCS_PATH", "data/policy_docs.npy")

# Milvus 配置
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))
MILVUS_COLLECTION_NAME = os.getenv("MILVUS_COLLECTION_NAME", "policy_rag")